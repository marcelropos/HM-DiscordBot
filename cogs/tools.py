import asyncio
import datetime
import logging
from enum import Enum
from io import BytesIO
from typing import Union

import aiohttp
import discord
from discord import Message, User, Member
from discord.ext import commands
from discord.ext.commands import Context, Bot
from prettytable import PrettyTable

from settings_files._global import ServerIds
from settings_files.all_errors import *

logger = logging.getLogger("discord")


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

    @commands.command(name="list-guild-member",
                      brief="Show a list of all guild member, their roles and join date",
                      help="Show a list of all guild member, their roles and join date")
    @commands.has_role(ServerIds.HM)
    async def list_guild_member(self, ctx: Context):
        column = ["name", "roles", "joined_at", "pending"]
        table = PrettyTable(column)
        members = await ctx.guild.fetch_members(limit=None).flatten()
        for member in members:
            member: Union[Member, User]

            roles = reversed(member.roles)
            role_list = ""
            for role in roles:
                if role.name != "@everyone":
                    role_list += role.name + "\n"

            joined = member.joined_at.strftime("%d.%m.%Y")

            nick = f"Nick: {str(member.nick)}\n" if member.nick else ""
            names = nick + f"Name: {str(member.name)}#{str(member.discriminator)}"

            table.add_row((names, role_list, joined, member.pending))

        table.title = f"List status from {datetime.datetime.now().strftime('%d.%m.%Y, %H:%M:%S')}" \
                      f" - there are {len(members)} members"

        await ctx.reply(
            file=discord.File(
                BytesIO(bytes(str(table), encoding='utf-8')),
                filename="List_of_all_members.text"),
            content="Here is a list of all members that are currently on this server.",
            delete_after=600)

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
    async def man_error(self, ctx: Context, error):
        if isinstance(error, CommandInvokeError):
            error = error.original

        if isinstance(error, ManPageNotFound):
            await ctx.message.delete(delay=60)
            await ctx.reply(f"No manpage for `{error.__context__}` could be found.",
                            delete_after=60)
        else:
            logger.exception("Issue while fetching Page")


def setup(bot):
    bot.add_cog(Tools(bot))
