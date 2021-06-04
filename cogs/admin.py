import logging
import sys

import discord
from discord.ext.commands import Cog

from utils.embed_generator import BugReport
from utils.utils import *

logger = logging.getLogger("discord").getChild("cogs").getChild("admin")


class Admin(Cog):
    """Bot und Server administrations commands"""

    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.command(help="Bot shutdown")
    @commands.is_owner()
    async def shutdown(self, _):
        status = discord.Status.offline
        await discord.Client.change_presence(self=self.bot,
                                             status=status)

        await discord.Client.close(self.bot)
        sys.exit(0)

    @commands.command(help="Disable a module")
    @commands.is_owner()
    async def unload(self, ctx: Context, cog: str):
        if cog == "cogs.admin":
            raise ModuleError("The 'Admin' module may not be disabled.")
        try:
            self.bot.unload_extension(f"cogs.{cog}")
        except Exception:
            msg_log = "Could not unload cog"
            logger.exception(msg_log)
            await ctx.reply(msg_log)
            return
        msg_log = "Cog unloaded"
        logger.info(msg_log)
        await ctx.send(msg_log)

    @commands.command(help="Load and enable a module")
    @commands.is_owner()
    async def load(self, ctx: Context, cog: str):
        try:
            self.bot.load_extension(f"cogs.{cog}")
        except Exception:
            msg_log = "Could not load cog"
            logger.exception(msg_log)
            await ctx.reply(msg_log)
            return
        msg_log = "Cog loaded"
        logger.info(msg_log)
        await ctx.send(msg_log)

    @commands.command(help="reload and enable a module")
    @commands.is_owner()
    async def reload(self, ctx: Context, cog: str):
        try:
            self.bot.unload_extension(f"cogs.{cog}")
        except Exception:
            msg_log = "Could not unload cog"
            logger.exception(msg_log)
            await ctx.reply(msg_log)
            return
        try:
            self.bot.load_extension(f"cogs.{cog}")
        except Exception:
            msg_log = "Could not load cog"
            logger.exception(msg_log)
            await ctx.reply(msg_log)
            return
        msg_log = "Cog reloaded"
        logger.info(msg_log)
        await ctx.send(msg_log)

    @commands.command(brief="Delete chat history",
                      help="Put the command in the chat, which should be purged. "
                           "Enter the number of messages to be deleted.")
    @commands.is_owner()
    async def purge(self, ctx: Context, count: int):
        await ctx.channel.purge(limit=count, bulk=True)
        await ctx.send("Purged messages")

    @commands.command(help="Write the specific text in the specified chat.")
    @commands.is_owner()
    async def msg(self, _, channel_id: int, *, args: str):
        channel = await self.bot.fetch_channel(channel_id)
        await channel.send(args)

    async def cog_command_error(self, ctx, error):
        if isinstance(error, CommandInvokeError):
            error = error.original
        if isinstance(error, MissingRole):
            await ctx.send(f"<@!{ctx.author.id}>\n"
                           f"This command is reserved for the admin.")
        elif isinstance(error, ModuleError):
            await ctx.send(error.__context__)
        else:
            error = BugReport(self.bot, ctx, error)
            await error.reply()


def setup(bot: Bot):
    bot.add_cog(Admin(bot))
