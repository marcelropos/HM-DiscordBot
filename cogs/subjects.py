from typing import Union

from discord import Role, TextChannel, Member, User, Guild
from discord.ext.commands import Cog, Bot, has_guild_permissions, group, Context, BadArgument
from discord.ext.tasks import loop
from discord_components import DiscordComponents

from cogs.botStatus import listener
from cogs.util.ainit_ctx_mgr import AinitManager
from cogs.util.assign_variables import assign_set_of_roles
from cogs.util.placeholder import Placeholder
from cogs.util.study_subject_util import StudySubjectUtil
from core.globalEnum import SubjectsOrGroupsEnum, ConfigurationNameEnum, CollectionEnum
from core.logger import get_discord_child_logger
from core.predicates import bot_chat
from mongo.primitiveMongoData import PrimitiveMongoData
from mongo.subjectsorgroups import SubjectsOrGroups

bot_channels: set[TextChannel] = set()
verified: Placeholder = Placeholder()
moderator: Placeholder = Placeholder()
subjects_roles: set[Role] = set()
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
        global bot_channels, subjects_roles, verified, moderator
        # noinspection PyTypeChecker
        async with AinitManager(bot=self.bot,
                                loop=self.ainit,
                                need_init=self.need_init,
                                bot_channels=bot_channels,
                                verified=verified,
                                moderator=moderator) as need_init:
            if need_init:
                DiscordComponents(self.bot)
                await assign_set_of_roles(self.bot.guilds[0], self.db, subjects_roles)

    # subjects group

    @group(pass_context=True,
           name="subjects")
    @bot_chat(bot_channels)
    @has_guild_permissions(administrator=True)
    async def subjects(self, ctx: Context):
        if not ctx.invoked_subcommand:
            raise BadArgument
        member: Union[Member, User] = ctx.author
        logger.info(f'User="{member.name}#{member.discriminator}({member.id})", Command="{ctx.message.content}"')

    @subjects.command(pass_context=True,
                      name="add")
    async def subjects_add(self, ctx: Context, name: str):
        """
        Adds a new role-channel pair as a group.

        Args:
            ctx: The command context provided by the discord.py wrapper.

            name: The name of the role and the chat.
        """
        guild: Guild = ctx.guild
        category_key = ConfigurationNameEnum.SUBJECTS_CATEGORY
        separator_key = ConfigurationNameEnum.SUBJECTS_SEPARATOR_ROLE

        await StudySubjectUtil.get_server_objects(category_key,
                                                  guild,
                                                  name,
                                                  separator_key,
                                                  self.db)

    @subjects.command(pass_context=True,
                      name="category")
    async def subjects_category(self, ctx: Context, category: int):
        """
                Saves the group separator role:

                Args:
                    ctx: The command context provided by the discord.py wrapper.

                    category: The category id for the channels.
                """

        db = PrimitiveMongoData(CollectionEnum.CATEGORIES)
        key = ConfigurationNameEnum.SUBJECTS_CATEGORY
        msg = "category"
        await StudySubjectUtil.update_category_and_separator(category, ctx, db, key, msg)

    @subjects.command(pass_context=True,
                      name="separator")
    async def subjects_separator(self, ctx: Context, role):  # parameter only for pretty help.
        """
        Saves the group separator role:

        Args:
            ctx: The command context provided by the discord.py wrapper.

            role: The mentioned role.
        """
        if len(ctx.message.role_mentions) > 1:
            raise BadArgument

        role: Role = ctx.message.role_mentions[0]
        key = ConfigurationNameEnum.SUBJECTS_SEPARATOR_ROLE

        db = PrimitiveMongoData(CollectionEnum.ROLES)
        msg = "separator"
        await StudySubjectUtil.update_category_and_separator(role.id, ctx, db, key, msg)


def setup(bot: Bot):
    bot.add_cog(Subjects(bot))
