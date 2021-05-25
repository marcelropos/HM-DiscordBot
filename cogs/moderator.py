import asyncio
import datetime
import re
import xml.etree.ElementTree as ElementTree

from discord import Guild, Role, Message
from discord.ext import commands, tasks
from discord.ext.commands import Context, Bot, Cog

from settings_files.all_errors import *
from utils.logbot import LogBot
from utils.utils import strtobool


class Events(Cog):

    def __init__(self, bot: Bot):
        self.bot = bot
        self.link = re.compile(r"https?://")
        self.config = ElementTree.parse("./data/config.xml").getroot()

    @Cog.listener(name="on_message")
    async def restricted_messages(self, message: Message):
        channels_conf = self.config \
            .find("Guilds") \
            .find(f"Guild-{message.guild.id}") \
            .find("Channels")
        try:
            restricted_channels = {channels_conf.find("BOT_COMMANDS_CHANNEL").text, channels_conf.find("HELP").text}
            if message.guild and len(message.author.roles) == 1 and message.channel.id in restricted_channels:
                match = re.match(self.link, message.content)
                if match:
                    await message.delete()
                    await message.channel.send(f"<@{message.author.id}>\n"
                                               f"Non-verified members are not allowed to post links to this channel.")
                    LogBot.logger.info(f"Message >>{message.clean_content}<< in channel {message.channel}"
                                       f"from {message.author.display_name}({message.author.id}) "
                                       f"deleted according due restrictions.")
        except Forbidden:
            LogBot.logger.warning("Failed to fulfill restriction.")
        except HTTPException:
            pass


class Moderator(Cog):

    def __init__(self, bot: Bot):
        self.bot = bot
        self.kick_mode = False

        self.config = ElementTree.parse("./data/config.xml").getroot()
        self.kick_not_verified.start()

    # noinspection PyUnusedLocal
    @tasks.loop()
    async def kick_not_verified(self, *_):
        # await self.wait_until()
        self.config.find("Guilds")
        for guild_conf in self.config.find("Guilds"):
            guild_conf: ElementTree.Element
            guild: Guild = await self.bot.fetch_guild(int(guild_conf.tag.strip("Guild-")))

            kick_mode = strtobool(self.config
                                  .find("Guilds")
                                  .find(f"Guild-{guild.id}")
                                  .find("Cogs")
                                  .find("Moderator")
                                  .find("kick_mode")
                                  .text)
            if not kick_mode:
                continue

            moderator_conf = self.config \
                .find("Guilds") \
                .find(f"Guild-{guild.id}") \
                .find("Cogs") \
                .find("Moderator")

            roles_conf = self.config \
                .find("Guilds") \
                .find(f"Guild-{guild.id}") \
                .find("RoleIDs")

            support_channel = int(self.config
                                  .find("Guilds")
                                  .find(f"Guild-{guild.id}")
                                  .find("Channels")
                                  .find("HELP")
                                  .text)

            kick_after_days = int(moderator_conf.find("kick_after_days").text)
            warn_before_day_x = int(moderator_conf.find("warn_before_day_x").text)

            async for member in guild.fetch_members(limit=None):
                verified: set[Role] = {role.id for role in member.roles
                                       if role.id == int(roles_conf.find("VERIFIED").text)
                                       or role.id == int(roles_conf.find("BOT").text)
                                       or role.id == int(roles_conf.find("FRIENDS").text)}

                if not verified:
                    days_on_server = (datetime.datetime.now() - member.joined_at).days
                    if days_on_server >= kick_after_days:
                        # noinspection PyBroadException
                        try:
                            await member.send(
                                content=f"You will be kicked from {guild.name} because you have not been "
                                        "verified for too long. You can rejoin the server and "
                                        "submit a request for verification.",
                                delete_after=86400)
                        except Exception:
                            pass
                        # noinspection PyBroadException
                        try:
                            await member.kick(reason="Too long without verification")
                        except Exception:
                            channel = await self.bot.fetch_channel(support_channel)
                            await channel.send(f"Failed to kick <@{member.id}>.")
                        else:
                            LogBot.logger.info(f"Kicked: {member} for being not verified")
                    elif days_on_server > kick_after_days - warn_before_day_x - 1:

                        channel = await self.bot.fetch_channel(support_channel)

                        await channel.send(f"<@{member.id}>\n"
                                           f"You will be removed from this server in "
                                           f"{kick_after_days - days_on_server} days "
                                           f"because you do not have a role.\n"
                                           f"To avoid this, you need to get verified by a moderator.",
                                           delete_after=86400)
                    if days_on_server > kick_after_days - warn_before_day_x - 1:
                        await asyncio.sleep(1)

    @staticmethod
    async def wait_until() -> None:
        """
        Wait until 6 am.
        """
        now = datetime.datetime.now()
        until_time = now.replace(hour=6, minute=0, second=0, microsecond=0) + datetime.timedelta(days=1)
        until_time = (until_time.year, until_time.month, until_time.day, until_time.hour)
        await asyncio.sleep((datetime.datetime(*until_time) - now).total_seconds())

    @commands.command(
        name="kick-mode",
        description="Enable or disable time based kicking",
        brief="Enable or disable time based kicking",
        aliases=[]
    )
    @commands.guild_only()
    @commands.is_owner()
    async def kick_mode(self, _, boolean: strtobool):
        self.kick_mode = boolean

    @kick_mode.error
    async def kick_mode_error(self, ctx: Context, error):
        if isinstance(error, MissingRole):
            await ctx.send(
                f"<@!{ctx.author.id}>\n"
                f"This command is not intended for you. Please avoid sending this command.",
                delete_after=60
            )


def setup(bot):
    bot.add_cog(Moderator(bot))
