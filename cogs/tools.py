# noinspection PyPackageRequirements
from discord.ext import commands
# noinspection PyUnresolvedReferences
import discord
from settings_files._global import ServerIds
from utils.utils import DictSort


class Tools(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=["get-members"])
    @commands.has_role(ServerIds.HM)
    async def get_members(self, ctx, sort_type="ByName", rev="False"):
        role_count = dict()
        reply = "Liste aller Rollen und ihre Mitgliederzahl:\n"
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


def setup(bot):
    bot.add_cog(Tools(bot))
