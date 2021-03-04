# noinspection PyUnresolvedReferences
from discord.ext import commands
from utils.utils import *
from utils.embed_generator import EmbedGenerator


class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=["hilfe"])
    async def help(self, ctx, arg=None):

        if arg is None:
            embed = EmbedGenerator("help")
        else:
            embed = EmbedGenerator(arg)
        await ctx.send(content=f"<@!{ctx.author.id}> vielen Dank für deine Frage.",
                       embed=embed.generate())

    @commands.command(aliases=["manpage"])
    async def man(self, ctx, arg=None):
        if arg is None:
            await ctx.send(content="Bitte ein UNIX Kommando angeben")
        else:
            await ctx.send(content=f"<@!{ctx.author.id}> deine Manpage ist hier: http://man.openbsd.org/{arg}")


def setup(bot):
    bot.add_cog(Help(bot))
