import datetime

import discord
from discord.ext import commands, tasks
from discord.ext.commands import Context

from settings_files._global import ServerIds
from settings_files.all_errors import *
from utils.logbot import LogBot
from utils.utils import strtobool


class Moderator(commands.Cog):
    kick_after_days = 60
    warn_before_day_x = 7

    def __init__(self, bot):
        self.bot = bot
        self.kick_mode = False
        self.kick_not_verified.start()

    # noinspection PyUnusedLocal
    @tasks.loop(hours=24)
    async def kick_not_verified(self, *_):
        if self.kick_mode:
            guild = await discord.Client.fetch_guild(self.bot, ServerIds.GUILD_ID)
            async for member in guild.fetch_members(limit=None):
                got_roles = {role.name for role in member.roles}
                if len(got_roles) == 1:
                    days_on_server = (datetime.datetime.now() - member.joined_at).days
                    if days_on_server >= self.__class__.kick_after_days:
                        # noinspection PyBroadException
                        try:
                            await member.send(content="You will be kicked from the server because you have not been "
                                                      "verified for too long. You can rejoin the server and "
                                                      "submit a request for verification.", delete_after=86400)
                        except Exception:
                            pass
                        # noinspection PyBroadException
                        try:
                            await member.kick(reason="Too long without verification")
                        except Exception:
                            channel = await self.bot.fetch_channel(ServerIds.DEBUG_CHAT)
                            await channel.send(f"Failed to kick <@{member.id}>.")
                        else:
                            LogBot.logger.info(f"Kicked: {member} for being not verified")
                    elif days_on_server >= self.__class__.kick_after_days - self.__class__.warn_before_day_x:

                        channel = await self.bot.fetch_channel(ServerIds.HELP)

                        await channel.send(f"<@{member.id}>\n"
                                           f"You will be removed from this server in "
                                           f"{self.__class__.kick_after_days - days_on_server} days "
                                           f"because you do not have a role.\n"
                                           f"To avoid this, you need to get verified by a moderator.")

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
