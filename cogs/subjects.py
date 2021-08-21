from discord import Role, TextChannel
from discord.ext.commands import Cog, Bot
from discord.ext.tasks import loop
from discord_components import DiscordComponents

from cogs.botStatus import listener
from cogs.util.ainit_ctx_mgr import AinitManager
from cogs.util.assign_variables import assign_set_of_roles
from cogs.util.placeholder import Placeholder
from core.globalEnum import SubjectsOrGroupsEnum
from core.logger import get_discord_child_logger
from mongo.subjectsorgroups import SubjectsOrGroups

bot_channels: set[TextChannel] = set()
verified: Placeholder = Placeholder()
moderator: Placeholder = Placeholder()
subjects: set[Role] = set()
first_init = True

logger = get_discord_child_logger("Subjects")


class Subjects(Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
        self.db = SubjectsOrGroups(self.bot, SubjectsOrGroupsEnum.GROUP)
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
        global bot_channels, subjects, verified, moderator
        # noinspection PyTypeChecker
        async with AinitManager(bot=self.bot,
                                loop=self.ainit,
                                need_init=self.need_init,
                                bot_channels=bot_channels,
                                verified=verified,
                                moderator=moderator) as need_init:
            if need_init:
                DiscordComponents(self.bot)
                await assign_set_of_roles(self.bot.guilds[0], self.db, subjects)

    # commands


def setup(bot: Bot):
    bot.add_cog(Subjects(bot))
