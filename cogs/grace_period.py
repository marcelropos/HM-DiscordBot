import os

from discord import Member
from discord.ext.commands import Cog, Bot
from discord.ext.tasks import loop

from cogs.bot_status import listener
from cogs.util.assign_variables import assign_role
from cogs.util.placeholder import Placeholder
from core.error.error_collection import BrokenConfigurationError
from core.global_enum import ConfigurationNameEnum
from core.logger import get_discord_child_logger

tmp_verified: Placeholder = Placeholder()
first_init = True
logger = get_discord_child_logger("GracePeriod")


class GracePeriod(Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
        self.need_init = True
        if not first_init:
            self.ainit.start()

    @listener()
    async def on_ready(self):
        global first_init
        if first_init:
            first_init = False
            self.ainit.start()

    @loop()
    async def ainit(self):
        """
        Loads the configuration for the module.
        """
        global tmp_verified
        try:
            tmp_verified.item = await assign_role(self.bot, ConfigurationNameEnum.TMP_STUDENTY)
        except BrokenConfigurationError:
            logger.info("Unloading Grace Period Cog since no TMP Verified role is set up")
            self.cog_unload()
        self.ainit.stop()

    @listener()
    async def on_member_join(self, member: Member):
        await member.add_roles(tmp_verified.item, reason="Grace Period")


def setup(bot: Bot):
    bot.add_cog(GracePeriod(bot))
