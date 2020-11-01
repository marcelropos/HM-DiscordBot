# noinspection PyPackageRequirements
from discord.ext import commands
# noinspection PyUnresolvedReferences
import discord
from utils import ServerRoles, DictSort


class Tools(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=["get-members"])
    @commands.has_role(ServerRoles.HM)
    async def get_members(self, ctx, sort_type="ByName", rev="False"):
        rolecount = dict()
        reply = "Liste aller Rollen und ihre Mitgliederzahl:\n"
        async for member in ctx.guild.fetch_members(limit=None):
            for x in member.roles:
                name = x.name.replace("@", "")
                if name not in rolecount:
                    rolecount[name] = 1
                else:
                    rolecount[name] += 1

        if rev.lower() == "true":
            rev = True
        else:
            rev = False

        if "bycount" == sort_type.lower():
            rolecount = DictSort.sort_by_value(rolecount, rev)
        else:
            rolecount = DictSort.sort_by_key(rolecount, rev)

        for x in rolecount:
            reply += f"{x}: {rolecount[x]}\n"

        await ctx.send(reply)


def setup(bot):
    bot.add_cog(Tools(bot))
