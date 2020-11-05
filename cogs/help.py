# noinspection PyUnresolvedReferences
from discord.ext import commands
from utils import *
from settings import Embedgenerator


class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def help(self, ctx, arg=None):

        print(arg)
        if arg is None:
            embed = Embedgenerator("help")
        else:
            embed = Embedgenerator(arg)
        await ctx.send(content=f"<@!{ctx.author.id}> vielen Dank für deine Frage.",
                       embed=embed.generate())


def setup(bot):
    bot.add_cog(Help(bot))
