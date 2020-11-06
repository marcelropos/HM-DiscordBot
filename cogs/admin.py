# noinspection PyUnresolvedReferences
import sys
# noinspection PyUnresolvedReferences
import asyncio
# noinspection PyUnresolvedReferences
import discord
# noinspection PyUnresolvedReferences
from discord.ext import commands
from utils import *


# noinspection PyUnusedLocal
class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.is_owner()
    async def shutdown(self, ctx):
        status = discord.Status.offline
        await discord.Client.change_presence(self=self.bot, status=status)
        await discord.Client.logout(self.bot)
        await discord.Client.close(self.bot)
        sys.exit(0)

    @commands.command()
    @commands.is_owner()
    async def activity(self, ctx, *, arg):
        activity = discord.Game(name=arg)
        await discord.Client.change_presence(self=self.bot, activity=activity)

    @commands.command()
    @commands.is_owner()
    async def status(self, ctx, *, arg: str):
        arg = arg.lower()
        if arg == "online":
            status = discord.Status.online
        elif arg == "offline":
            status = discord.Status.offline
        elif arg == "idle":
            status = discord.Status.idle
        else:
            status = discord.Status.dnd

        await discord.Client.change_presence(self=self.bot, status=status)

    @commands.command()
    @commands.is_owner()
    async def unload(self, ctx, cog: str):
        if cog == "cogs.admin":
            raise ModuleError("Das Modul 'Admin' darf nicht deaktiviert werden.")
        try:
            self.bot.unload_extension(cog)
        except Exception as e:
            raise ModuleError("Could not unload cog")
        await ctx.send("Cog unloaded")

    @commands.command()
    @commands.is_owner()
    async def load(self, ctx, cog: str):
        try:
            self.bot.load_extension(cog)
        except Exception as e:
            raise ModuleError("Could not load cog")
        await ctx.send("Cog loaded")

    @commands.command()
    @commands.is_owner()
    async def reload(self, ctx, cog: str):
        try:
            self.bot.unload_extension(cog)
            self.bot.load_extension(cog)
        except Exception as e:
            raise ModuleError("Could not reload cog")
        await ctx.send("Cog reloaded")

    @commands.command()
    @commands.is_owner()
    async def purge(self, ctx, arg: int):
        await ctx.channel.purge(limit=arg, bulk=True)
        await ctx.send("Purged messages")

    @commands.command()
    @commands.is_owner()
    async def reply(self, ctx, *, args):
        print(args)
        message = await ctx.send(args)
        print(message.channel.id)
        print(message.id)

    @commands.command()
    @commands.is_owner()
    async def msg(self, ctx, channel_id, *, args):
        channel = await self.bot.fetch_channel(channel_id)
        await channel.send(args)


def setup(bot):
    bot.add_cog(Admin(bot))
