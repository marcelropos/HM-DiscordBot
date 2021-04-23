import asyncio
from enum import Enum

import aiohttp
from discord import Message
from discord.ext import commands
from discord.ext.commands import Context, Bot

from settings_files._global import ServerIds
from settings_files.all_errors import *
from utils.logbot import LogBot
from utils.utils import strtobool


class SortType(Enum):
    BY_NAME = "byname"
    BY_COUNT = "bycount"


def sort_type_converter(arg: str):
    arg = arg.lower()
    try:
        sort_type = SortType(arg)
    except ValueError:
        raise BadArgument("Sort type not found")
    return sort_type


class Tools(commands.Cog):
    """Various commands"""

    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.command(brief="current ping",
                      help="evaluates the bot ping")
    async def ping(self, ctx: Context):
        reply: Message = await ctx.reply("Pong")
        msg: Message = ctx.message
        await reply.edit(content=f"{reply.created_at.timestamp() - msg.created_at.timestamp()}")
        print(reply.created_at.timestamp())

    @commands.command(name="member-count",
                      brief="Lists the roles and their member count.",
                      help="""sort_type:
                      - ByName
                      - ByCount (default)
                      Invert:
                      - True (default)
                      - False""")
    @commands.has_role(ServerIds.HM)
    async def member_count(self, ctx: Context, rev: strtobool = True,
                           sort_type: sort_type_converter = SortType.BY_COUNT):
        # Because of the framework, the implementation violates the PEP484 standard.
        role_count = dict()
        reply = "List of all roles und their member count:\n"
        async for member in ctx.guild.fetch_members(limit=None):
            for x in member.roles:
                name = x.name.replace("@", "")
                if name not in role_count:
                    role_count[name] = 1
                else:
                    role_count[name] += 1

        if sort_type == sort_type.BY_NAME:
            counted_roles = sorted(role_count.items(), key=lambda t: t[0], reverse=rev)
        elif sort_type == sort_type.BY_COUNT:
            counted_roles = sorted(role_count.items(), key=lambda t: t[1], reverse=rev)
        else:
            raise BadArgument("Sort type not supported.")

        for key, value in counted_roles:
            reply += f"{key}: {value}\n"
        await ctx.send(reply)

    @staticmethod
    async def get_page(url, priority=0):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    pass
                return priority, response
        except aiohttp.ClientError:
            return priority, None

    @commands.command(aliases=["manpage"],
                      brief="Find a suitable manpage ",
                      help="The best matching man page is selected from the deposited sources:\n"
                           "1) http://man.openbsd.org/ (default)\n"
                           "2) https://wiki.archlinux.org/ (flag: linux)\n"
                           "You can force a specific source with the following flags:\n"
                           "- linux")
    async def man(self, ctx: Context, arg: str, flag: str = ""):

        flag = flag.lower()
        if flag == "linux":
            result = await Tools.get_page(f"https://wiki.archlinux.org/index.php/{arg}")
        else:

            result = await asyncio.gather(
                Tools.get_page(f"http://man.openbsd.org/{arg}", 1),
                Tools.get_page(f"https://wiki.archlinux.org/index.php/{arg}", 2)
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

        else:
            _, page = result
            if page.ok:
                await ctx.send(f"`$ man {arg}`\n"
                               f"{page.url}")
            else:
                raise ManPageNotFound(arg)

    @man.error
    async def man_error(self, ctx, error):
        if isinstance(error, CommandInvokeError):
            error = error.original

        if isinstance(error, ManPageNotFound):
            await ctx.send(f"No manpage for `{error.__context__}` could be found.")
        else:
            LogBot.logger.exception("Issue while fetching Page")


def setup(bot):
    bot.add_cog(Tools(bot))
