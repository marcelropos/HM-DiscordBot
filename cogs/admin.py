import sys
from utils.embed_generator import BugReport
from utils.utils import *
from discord.ext.commands import Context, Bot


# noinspection PyUnusedLocal
class Admin(commands.Cog):
    """Bot und Server administrations commands"""

    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.command(help="Bot shutdown")
    @commands.is_owner()
    async def shutdown(self, ctx: Context):
        status = discord.Status.offline
        await discord.Client.change_presence(self=self.bot,
                                             status=status)

        await discord.Client.logout(self.bot)
        await discord.Client.close(self.bot)
        sys.exit(0)

    @commands.command(help="Disable a module")
    @commands.is_owner()
    async def unload(self, ctx: Context, cog: str):
        if cog == "cogs.admin":
            raise ModuleError("The 'Admin' module may not be disabled.")
        try:
            self.bot.unload_extension(cog)
        except Exception as e:
            raise ModuleError("Could not unload cog")
        await ctx.send("Cog unloaded")

    @commands.command(help="Load and enable a module")
    @commands.is_owner()
    async def load(self, ctx: Context, cog: str):
        try:
            self.bot.load_extension(cog)
        except Exception as e:
            raise ModuleError("Could not load cog")
        await ctx.send("Cog loaded")

    @commands.command(help="reload and enable a module")
    @commands.is_owner()
    async def reload(self, ctx: Context, cog: str):
        try:
            self.bot.unload_extension(cog)
            self.bot.load_extension(cog)
        except Exception as e:
            raise ModuleError("Could not reload cog")
        await ctx.send("Cog reloaded")

    @commands.command(brief="Delete chat history",
                      help="Put the command in the chat, which should be purged. "
                           "Enter the number of messages to be deleted.")
    @commands.is_owner()
    async def purge(self, ctx: Context, count: int):
        await ctx.channel.purge(limit=count, bulk=True)
        await ctx.send("Purged messages")

    @commands.command(help="Reply with the raw message.")
    @commands.is_owner()
    async def reply(self, ctx: Context, *, args: str):
        await ctx.send(ctx.message.content)

    @commands.command(help="Write the specific text in the specified chat.")
    @commands.is_owner()
    async def msg(self, ctx: Context, channel_id: int, *, args: str):
        channel = await self.bot.fetch_channel(channel_id)
        await channel.send(args)

    @shutdown.error
    @unload.error
    @reload.error
    @load.error
    @reply.error
    @msg.error
    @purge.error
    async def admin_errorhandler(self, ctx, error):
        if isinstance(error, MissingRole):
            await ctx.send(f"<@!{ctx.author.id}>\n"
                           f"This command is reserved for the admin.")
        else:
            error = BugReport(self.bot, ctx, error)
            error.user_details()
            await error.reply()


def setup(bot: Bot):
    bot.add_cog(Admin(bot))
