import asyncio
import configparser
import datetime
import hashlib
import logging
import re
import sqlite3
from dataclasses import dataclass
from enum import Enum
from xml.etree import ElementTree as Etree

import aiohttp
from discord.channel import TextChannel
from discord.client import Client
from discord.embeds import Embed
from discord.ext import commands, tasks
from discord.ext.commands import Bot, Context
from discord.message import Message

from settings_files._global import DEBUG_STATUS
from utils.utils import strtobool

logger = logging.getLogger("discord")


class Options(Enum):
    ENABLED = "enabled"
    RSS = "rss"
    CHANNEL = "channel"
    PATH = "config_path"


def options_converter(option: str) -> Options:
    option = option.lower()
    return Options(option)


def empty_embed(argument):
    """
    If argument is not empty return the argument
    else prevent error with an empty embed instance.
    :param argument:
    :return argument:
    :return Embed.Empty:
    """
    if argument:
        return argument
    else:
        return Embed.Empty


def check(author, sections):
    def inner_check(message: Message):
        if message.author.id == author.id \
                and message.clean_content in sections:
            return True
        return False

    return inner_check


class Rss(commands.Cog):
    """Add and manage RSS feeds"""

    def __init__(self, bot: Bot):
        self.bot = bot
        self.config = configparser.ConfigParser()
        self.config_path = "./data/rss.cfg"
        self.config.read(self.config_path)
        self.ini = re.compile("```ini.*```", re.DOTALL)
        self.set = re.compile("{.*}")
        self.void = set()
        self.read = set()
        self.db = RssDB().make()
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
            f"[{self.config[msg.content].name}]\n"
            f"enabled = {self.config[msg.content]['enabled']}\n"
            f"rss = {self.config[msg.content]['rss']}\n"
            f"channel = {self.config[msg.content]['channel']}\n"
            f"```"
        )

    @staticmethod
    async def wait_until() -> None:
        """
        Waits for the next full or half hour.
        """
        now = datetime.datetime.now()
        wait_clean = datetime.datetime.now().replace(minute=0, second=0, microsecond=0)
        wait = [
            (wait_clean + datetime.timedelta(minutes=30) - now).total_seconds(),
            (wait_clean + datetime.timedelta(hours=1) - now).total_seconds()
        ]
        wait_until = min([x for x in wait if x > 0])
        await asyncio.sleep(wait_until)

    @tasks.loop()
    async def get_rss_feeds(self):
        await self.wait_until()
        logger.info("Start fetching rss feed")
        self.config.read(self.config_path)
        self.void = self.db.get_feed
        task_list = [self.process_feed(section) for section in self.config.sections()]
        await asyncio.gather(*task_list)
        self.db.add_feed(self.read)
        self.read.clear()
        logger.info("Finished fetching rss feed")

    async def process_feed(self, section):
        if section == "DEFAULT":
            return
        logger.info(f"Start processing feed: {section}")
        link = self.config[section]["rss"]
        rss_feed = await Rss.get_page(link)
        if rss_feed:
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
            logger.exception("Could not decode website")
            return ""
        except Exception:
            logger.exception("Unexpected error")
            return ""

    async def create_embed(self, items: list, section: str):
        logger.debug(f"Create embed for {section}")
        link = self.config[section]["rss"]
        enabled = strtobool(self.config[section]["enabled"])
        color_config = empty_embed(self.config[section]["color"])
        author_icon = empty_embed(self.config[section]["author_icon"])
        author_url = empty_embed(self.config[section]["author_url"])
        channel_id = int(self.config[section]["channel"])
        repeat = False

        try:
            if color_config is not Embed.Empty:
                color = int(color_config, 16)
            else:
                color = color_config
        except ValueError:
            logger.warning("The color must be hexadecimal.")
            color = Embed.Empty

        embed = Embed(
            title=section,
            color=color,
            url=link
        )
        embed.set_author(
            name="RSS Reader",
            icon_url=author_icon,
            url=author_url
        )
        embed.set_footer(text=f"Source: {link}\n")

        character_limit = int(self.config["DEFAULT"]["character_limit"])
        field_limit = int(self.config["DEFAULT"]["field_limit"])
        field_name_limit = int(self.config["DEFAULT"]["field_name_limit"])
        field_value_limit = int(self.config["DEFAULT"]["field_value_limit"])

        items_left = items.copy()
        for item in items:
            try:
                name = item.find("title").text
                value = item.find("description").text
                item_link = item.find("link").text
                if not item_link:
                    item_link = ""

                to_be_continued = "`...`"
                if len(name) >= field_name_limit:
                    name = name[:field_name_limit - len(to_be_continued)] + to_be_continued
                if len(value) + len(item_link) >= field_value_limit:
                    value_limit = field_value_limit - len(item_link) - len(to_be_continued)
                    value = value[:value_limit] + to_be_continued
                value += f"\n{item_link}"
                to_hash = name + value

                if character_limit - len(to_hash) >= 0 and field_limit - 1 >= 0:
                    items_left.pop(0)
                    character_limit -= len(to_hash)
                    field_limit -= 1
                    fingerprint = hashlib.sha1(to_hash.encode("UTF-8")).hexdigest()
                    self.read.add(fingerprint)
                    if fingerprint not in self.void or fingerprint not in self.read:
                        logger.info(
                            f"New feed: Name:{name} - Value: {value} - Fingerprint: {fingerprint}".replace("\n", ""))
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
                        logger.warning(f"Could not publish message. Channel: {channel.name}({channel.id})")
            except Exception:
                logger.exception("Unhandled exception")

        if repeat:
            await self.create_embed(items_left, section)


def setup(bot: Bot):
    bot.add_cog(Rss(bot))


# noinspection SqlResolve
@dataclass(frozen=True)
class RssDB:
    conn = sqlite3.connect("./data/rss.db")

    def make(self):
        with self.conn as c:
            c.execute('''CREATE TABLE if NOT EXISTS TempChannels
                             (lastFetch DATE NOT NULL,
                             fingerprint TEXT NOT NULL,
                             PRIMARY KEY (fingerprint)
                             )''')
        return self

    @property
    def get_feed(self) -> set[str]:
        with self.conn as c:
            c.execute("DELETE FROM TempChannels WHERE lastFetch <= date('now','-365 day')")
        with self.conn as c:
            saved = c.execute(f"""SELECT fingerprint FROM TempChannels""").fetchall()
        return {entry[0] for entry in saved}

    def add_feed(self, fingerprints: set):
        saved = self.get_feed
        for fingerprint in fingerprints:
            with self.conn as c:
                if fingerprint in saved:
                    c.execute(f"""UPDATE TempChannels SET lastFetch=? where fingerprint=?""",
                              (datetime.datetime.now(), fingerprint))
                else:
                    c.execute(f"""INSERT into TempChannels(lastFetch,fingerprint)
                                VALUES(?,?)""", (datetime.datetime.now(), fingerprint))
