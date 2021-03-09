# noinspection PyPackageRequirements
from discord.ext import commands
# noinspection PyUnresolvedReferences
import discord
from discord.ext.commands import Context, Bot
from settings_files._global import ServerIds
from settings_files.all_errors import *
import asyncio
import aiohttp
from utils.utils import DictSort


class Tools(commands.Cog):
    """Various commands"""

    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.command(name="member-count",
                      brief="Lists the roles and their member count.",
                      help="""sort_type:
                      - ByName
                      - ByCount
                      Invert:
                      - True
                      - False""")
    @commands.has_role(ServerIds.HM)
    async def member_count(self, ctx: Context, sort_type="ByName", rev="True"):
        role_count = dict()
        reply = "List of all roles und their member count:\n"
        async for member in ctx.guild.fetch_members(limit=None):
            for x in member.roles:
                name = x.name.replace("@", "")
                if name not in role_count:
                    role_count[name] = 1
                else:
                    role_count[name] += 1

        if rev.lower() == "true":
            rev = True
        else:
            rev = False

        if "bycount" == sort_type.lower():
            role_count = DictSort.sort_by_value(role_count, rev)
        else:
            role_count = DictSort.sort_by_key(role_count, rev)

        for x in role_count:
            reply += f"{x}: {role_count[x]}\n"

        await ctx.send(reply)

    @staticmethod
    async def get_page(url, priority=0):
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                pass
            return priority, response

    @commands.command(aliases=["manpage"],
                      brief="Find a suitable manpage ",
                      help="The best matching man page is selected from the deposited sources:\n"
                           "1) http://man.openbsd.org/\n"
                           "2) https://wiki.archlinux.org/\n"
                           "You can force a specific source with the following flags:\n"
                           "- linux")
    async def man(self, ctx: Context, arg: str = None, flag: str = ""):
        if arg is None:
            await ctx.send(content="Please type in a command")
        else:

            flag = flag.lower()
            if flag == "linux":
                result = await Tools.get_page(f"https://wiki.archlinux.org/index.php/{arg}")
            elif flag == "ubuntu":
                result = await Tools.get_page(f"https://wiki.ubuntuusers.de/{arg}")
            else:

                result = await asyncio.gather(
                    Tools.get_page(f"http://man.openbsd.org/{arg}", 1),
                    Tools.get_page(f"https://wiki.archlinux.org/index.php/{arg}", 2),
                    Tools.get_page(f"https://wiki.ubuntuusers.de/{arg}", 3)
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
    async def man_error(self, ctx, error: ManPageNotFound):
        await ctx.send(f"No manpage for `{error.__context__}` could be found.")


def setup(bot):
    bot.add_cog(Tools(bot))
