# noinspection PyUnresolvedReferences
from discord.ext import commands
from utils.utils import *
# noinspection PyUnresolvedReferences
from settings import ServerRoles


class Moderator(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


def setup(bot):
    bot.add_cog(Moderator(bot))
