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
        sys.exit(0)

    @commands.command()
    @commands.is_owner()
    async def activity(self, ctx, *, arg):
        activity = discord.Game(name=arg)
        await discord.Client.change_presence(self=self.bot, activity=activity)
        channel = discord.Client.get_channel(self=self.bot, id=762736695116169217)

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
        channel = discord.Client.get_channel(self=self.bot, id=762736695116169217)

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
        await ctx.channel.purge(limit=arg, bulk=False)
        await ctx.send("Purged messages")

    @commands.command()
    @commands.is_owner()
    async def reply(self, ctx, *, args):
        await ctx.send(args)

    @commands.command()
    @commands.is_owner()
    async def get_members(self, ctx):
        rolecount = dict()
        reply = ""
        async for member in ctx.guild.fetch_members(limit=500):
            for x in member.roles:
                if x.name not in rolecount:
                    rolecount[x.name] = 1
                else:
                    rolecount[x.name] += 1


def setup(bot):
    bot.add_cog(Admin(bot))

#Test
