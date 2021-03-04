# noinspection PyUnresolvedReferences
from discord.ext import commands
# noinspection PyUnresolvedReferences
from settings_files._global import ServerRoles


class Moderator(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


def setup(bot):
    bot.add_cog(Moderator(bot))
