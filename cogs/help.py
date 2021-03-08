# noinspection PyUnresolvedReferences
from discord.ext import commands
from utils.utils import *
from utils.embed_generator import EmbedGenerator
import aiohttp
import asyncio


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

    @staticmethod
    async def get_page(url, priority=0):
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                pass
            return priority, response

    @commands.command(aliases=["manpage"])
    async def man(self, ctx, arg: str = None, flag: str = ""):
        if arg is None:
            await ctx.send(content="Bitte ein UNIX Kommando angeben")
        else:

            flag = flag.lower()
            if flag == "linux":
                result = await Help.get_page(f"https://wiki.archlinux.org/index.php/{arg}")
            elif flag == "ubuntu":
                result = await Help.get_page(f"https://wiki.ubuntuusers.de/{arg}")
            else:

                result = await asyncio.gather(
                    Help.get_page(f"http://man.openbsd.org/{arg}", 1),
                    Help.get_page(f"https://wiki.archlinux.org/index.php/{arg}", 2),
                    Help.get_page(f"https://wiki.ubuntuusers.de/{arg}", 3)
                )

        # noinspection PyUnboundLocalVariable
        if type(result) is list:
            result.sort(key=lambda x: x[0])

        for _, page in result:
            if page.ok:
                await ctx.send(f"`$ man {arg}`\n"
                               f"{page.url}")
                return

        raise ManPageNotFound(arg)

    @man.error
    async def man_error(self, ctx, error: ManPageNotFound):
        await ctx.send(f"Es konnte keine Manpage für `{error.__context__}` gefunden werden.")


def setup(bot):
    bot.add_cog(Help(bot))
