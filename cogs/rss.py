from discord.ext import commands, tasks
from discord.ext.commands import Bot, Context
from discord.client import Client
from discord.message import Message
from discord.channel import TextChannel
from discord.embeds import Embed
import asyncio
import aiohttp
from enum import Enum
import configparser
from utils.logbot import LogBot
from xml.etree import ElementTree as Etree
import aiofile
import hashlib
import re
from utils.utils import strtobool
from settings_files._global import DEBUG_STATUS


class Options(Enum):
    ENABLED = "enabled"
    RSS = "rss"
    CHANNEL = "channel"
    PATH = "config_path"


def options_converter(option: str) -> Options:
    option = option.lower()
    return Options(option)


def check(author, sections):
    def inner_check(message: Message):
        if message.author.id == author.id \
                and message.clean_content in sections:
            return True
        return False

    return inner_check


class Rss(commands.Cog):

    def __init__(self, bot: Bot):
        self.bot = bot
        self.config = configparser.ConfigParser()
        self.config_path = "./data/rss.cfg"
        self.config.read(self.config_path)
        self.feed_fingerprint = "./data/rss.txt"
        self.ini = re.compile("```ini.*```", re.DOTALL)
        self.set = re.compile("{.*}")
        self.void = set()
        self.read = set()
        if not DEBUG_STATUS():
            self.get_rss_feeds.start()

    def write_config(self):
        with open(self.config_path, "w") as f_out:
            self.config.write(f_out)

    @commands.command(name="rss-feed")
    @commands.is_owner()
    async def add_rss_feed(self, ctx: Context, *_):
        matches = re.finditer(self.ini, ctx.message.clean_content)
        for match in matches:
            start, end = match.span()
            raw_config: str = ctx.message.clean_content[start + 7:end - 4]
            config = configparser.ConfigParser()
            config.read_string(raw_config)
            for section in config.sections():
                self.config[section] = {
                    "enabled": config[section]["enabled"],
                    "rss": config[section]["rss"],
                    "channel": config[section]["channel"],
                }
        self.write_config()

    @commands.command(name="rss-config")
    @commands.is_owner()
    @commands.guild_only()
    async def rss_config(self, ctx: Context):
        await ctx.send(f"choose feed you want to edit:\n"
                       f"{sorted(self.config.sections())}")

        msg: Message = await Client.wait_for(
            self.bot,
            event="message",
            check=check(ctx.author, set(self.config.sections())),
            timeout=30
        )

        await ctx.send(
            f"```ini\n"
            f"[{self.config[msg.clean_content].name}]\n"
            f"enabled = {self.config[msg.clean_content]['enabled']}\n"
            f"rss = {self.config[msg.clean_content]['rss']}\n"
            f"channel = {self.config[msg.clean_content]['channel']}\n"
            f"```"
        )

    @tasks.loop(minutes=30)
    async def get_rss_feeds(self):
        LogBot.logger.info("Start fetching rss feed")
        self.config.read(self.config_path)
        await self.read_fingerprints()
        task_list = [self.process_feed(section) for section in self.config.sections()]
        await asyncio.gather(*task_list)
        await self.write_fingerprints()
        LogBot.logger.info("Finished fetching rss feed")

    async def process_feed(self, section):
        if section == "default":
            return
        LogBot.logger.info(f"Start processing feed: {section}")
        link = self.config[section]["rss"]
        rss_feed = await Rss.get_page(link)
        tree = Etree.fromstring(rss_feed)
        items = tree.findall("./channel/item")
        await self.create_embed(items, section)

    @staticmethod
    async def get_page(url: str) -> str:
        # noinspection PyBroadException
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    rss_feed = await response.text(encoding="ISO-8859-1")

                return rss_feed
        except aiohttp.ClientError:
            return ""
        except UnicodeDecodeError:
            LogBot.logger.exception("Could not decode website")
            return ""
        except Exception:
            LogBot.logger.exception("Unexpected error")
            return ""

    async def create_embed(self, items: list, section: str):
        LogBot.logger.debug(f"Create embed for {section}")
        link = self.config[section]["rss"]
        enabled = strtobool(self.config[section]["enabled"])
        channel_id = int(self.config[section]["channel"])
        repeat = False

        embed = Embed(
            title=section,
            url=link
        )
        embed.set_author(name="RSS Reader")
        embed.set_footer(text=f"Source: {link}\n")
        character_limit = int(self.config["default"]["character_limit"])
        field_limit = int(self.config["default"]["field_limit"])

        items_left = items.copy()
        for item in items:
            try:
                name = item.find("title").text
                value = item.find("description").text
                item_link = item.find("link").text
                if not item_link:
                    item_link = ""

                if len(name) >= 256:
                    name = name[:253] + "..."
                if len(value) + len(item_link) >= 1024:
                    value_limit = 1020 - len(item_link)
                    value = value[:value_limit] + "..."
                value = value + f"\n{item_link}"
                to_hash = name + value

                if character_limit - len(to_hash) >= 0 and field_limit - 1 >= 0:
                    items_left.pop(0)
                    character_limit -= len(to_hash)
                    field_limit -= 1
                    fingerprint = hashlib.sha1(to_hash.encode("UTF-8")).hexdigest()
                    self.read.add(fingerprint)
                    if fingerprint not in self.void or fingerprint not in self.read:
                        embed.add_field(
                            name=name,
                            value=value,
                            inline=False
                        )
                else:
                    repeat = True
                    break
            except TypeError:
                pass

        if enabled:
            # noinspection PyBroadException
            try:
                if len(embed.fields) > 0:
                    channel: TextChannel = await Client.fetch_channel(self.bot, channel_id)
                    message: Message = await channel.send(embed=embed)
                    # noinspection PyBroadException
                    try:
                        await message.publish()
                    except Exception:
                        LogBot.logger.warning(f"Could not publish message. Channel: {channel.name}({channel.id})")
            except Exception:
                LogBot.logger.exception("Unhandled exception")

        if repeat:
            await self.create_embed(items_left, section)

    async def write_fingerprints(self):
        # noinspection PyBroadException
        try:
            path = self.feed_fingerprint
            async with aiofile.async_open(path, "w") as f_out:
                for entry in self.read:
                    await f_out.write(entry + "\n")
        except Exception:
            LogBot.logger.exception("Could not write file:")
        finally:
            self.void = self.read.copy()
            self.read.clear()

    async def read_fingerprints(self):
        # noinspection PyBroadException
        try:
            path = self.feed_fingerprint
            async with aiofile.AIOFile(path, "r", encoding="UTF-8") as f_in:
                # noinspection PyUnresolvedReferences
                void = {entry.replace("\n", "") async for entry in aiofile.LineReader(f_in)}
            self.void = void.copy()
        except Exception:
            LogBot.logger.exception("Could not read file:")


def setup(bot: Bot):
    bot.add_cog(Rss(bot))
