# noinspection PyUnresolvedReferences
from discord.ext import commands
from utils import *
# noinspection PyUnresolvedReferences
from settings import Roles


class Moderator(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # noinspection PyUnusedLocal
    @commands.command(aliases=["no-hm"])
    async def no_hm(self, ctx):
        members = await ctx.guild.fetch_members(limit=None).flatten()


def setup(bot):
    bot.add_cog(Moderator(bot))
