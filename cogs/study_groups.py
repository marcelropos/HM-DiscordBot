import asyncio
import re
from typing import Union

from discord import Guild, Role, Member, User, TextChannel
from discord.ext.commands import Cog, Bot, command, Context, group, BadArgument
from discord.ext.tasks import loop
from discord_components import DiscordComponents, Interaction, Select, \
    SelectOption

from cogs.botStatus import listener
from cogs.util.accepted_chats import assign_accepted_chats, assign_verified_role
from cogs.util.ainit_ctx_mgr import AinitManager
from cogs.util.place_holder import Placeholder
from cogs.util.study_subject_util import StudySubjectUtil
from core.globalEnum import SubjectsOrGroupsEnum, CollectionEnum, ConfigurationNameEnum
from core.logger import get_discord_child_logger
from core.predicates import bot_chat, is_not_in_group, has_role_plus
from mongo.primitiveMongoData import PrimitiveMongoData
from mongo.subjectsorgroups import SubjectsOrGroups

bot_channels: set[TextChannel] = set()
verified: Placeholder = Placeholder()
study_groups: set[Role] = set()
first_init = True

logger = get_discord_child_logger("StudyGroups")


class StudyGroups(Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
        self.match = re.compile(r"([a-z]+)([0-9]+)", re.I)
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
        global bot_channels, study_groups, verified
        # noinspection PyTypeChecker
        async with AinitManager(self.bot, self.ainit, self.need_init) as need_init:
            if need_init:
                DiscordComponents(self.bot)

                await assign_accepted_chats(self.bot, bot_channels)

                verified.item = await assign_verified_role(self.bot)

                guild: Guild = self.bot.guilds[0]
                study_groups.clear()
                study_groups.update({guild.get_role(document.role_id) for document in await self.db.find({})})

    # commands

    @command()
    @bot_chat(bot_channels)
    @is_not_in_group(study_groups)
    @has_role_plus(verified)
    async def study(self, ctx: Context):
        guild: Guild = ctx.guild
        member: Union[Member, User] = ctx.author
        groups = sorted({guild.get_role(document.role_id) for document in await self.db.find({})},
                        key=lambda _role: _role.name)
        groups: list[Role]
        # limit self assigment to semester one and two
        groups = [_group for _group in groups if (int((re.match(self.match, _group.name).groups())[1]) < 3)]

        group_names = {str((re.match(self.match, _role.name).groups())[0])
                       for _role in groups}
        group_names_options = Select(
            placeholder="Select your group",
            options=[SelectOption(label=name, value=name) for name in group_names])

        group_semester = {str((re.match(self.match, _role.name).groups())[1]) for _role in groups}
        group_semester_options = Select(
            placeholder="Select your semester",
            options=[SelectOption(label=semester, value=semester) for semester in group_semester])

        await ctx.reply(content="Please select **one** of the following groups.",
                        components=[group_names_options, group_semester_options])

        role: Role = await self.get_role(member, groups, group_names, group_semester)
        await member.add_roles(role)

    # group group

    @group(pass_context=True,
           name="group")
    async def _group(self, ctx: Context):
        if not ctx.invoked_subcommand:
            raise BadArgument
        member: Union[Member, User] = ctx.author
        logger.info(f'User="{member.name}#{member.discriminator}({member.id})", Command="{ctx.message.content}"')

    @_group.command(pass_context=True,
                    name="add")
    async def group_add(self, ctx: Context, name: str):
        """
        Adds a new role-channel pair as a group.

        Args:
            ctx: The command context provided by the discord.py wrapper.

            name: The name of the role and the chat.
        """
        guild: Guild = ctx.guild
        category_key = ConfigurationNameEnum.STUDY_CATEGORY
        separator_key = ConfigurationNameEnum.STUDY_SEPARATOR_ROLE

        await StudySubjectUtil.get_server_objects(category_key,
                                                  guild,
                                                  name,
                                                  separator_key,
                                                  self.db)

    @_group.command(pass_context=True,
                    name="category")
    async def group_category(self, ctx: Context, category: int):
        """
                Saves the group separator role:

                Args:
                    ctx: The command context provided by the discord.py wrapper.

                    category: The category id for the channels.
                """

        db = PrimitiveMongoData(CollectionEnum.CATEGORIES)
        key = ConfigurationNameEnum.STUDY_CATEGORY
        msg = "category"
        await StudySubjectUtil.update_category_and_separator(category, ctx, db, key, msg)

    @_group.command(pass_context=True,
                    name="separator")
    async def group_separator(self, ctx: Context, role):  # parameter only for pretty help.
        """
        Saves the group separator role:

        Args:
            ctx: The command context provided by the discord.py wrapper.

            role: The mentioned role.
        """
        if len(ctx.message.role_mentions) > 1:
            raise BadArgument

        role: Role = ctx.message.role_mentions[0]
        db = PrimitiveMongoData(CollectionEnum.ROLES)
        key = ConfigurationNameEnum.STUDY_SEPARATOR_ROLE
        msg = "separator"
        await StudySubjectUtil.update_category_and_separator(role.id, ctx, db, key, msg)

    # help methods

    async def get_role(self, member, groups: list[Role], group_names: set[str], group_semester: set[str]) -> Role:
        """
        Expects multiple inputs in unknown order processes them to an existing role.

        Args:
            member: The Member whose input is requested.

            groups: All available groups.

            group_semester: All available group names.

            group_names: All available semester yrs.
        """
        a, b = await asyncio.gather(
            self.wait_for_group(group_names, member),
            self.wait_for_semester(group_semester, member)
        )

        result = set()
        result.update({role for role in groups if role.name == a + b})
        result.update({role for role in groups if role.name == b + a})
        # noinspection PyTypeChecker
        return result.pop()

    async def wait_for_group(self, group_names: set[str], member: Member) -> str:
        """
        Waits for a selection.

        Args:
            group_names: A set of all courses.

            member: The Member whose input is requested.

        Returns:
            The course name.
        """
        res: Interaction = await self.bot.wait_for("select_option",
                                                   check=lambda x: self.check(x, group_names, member))
        await res.respond(content=f"I received your group input.")
        # noinspection PyUnresolvedReferences
        return res.component[0].value

    async def wait_for_semester(self, group_semester: set[str], member: Member) -> Union[str, int]:
        """
        Waits for a selection.

        Args:
            group_semester: A set of all  semester yrs.

            member: The Member whose input is requested.

        Returns:
            Semester yr.
        """
        res: Interaction = await self.bot.wait_for("select_option",
                                                   check=lambda x: self.check(x, group_semester, member))
        await res.respond(content="I received your semester input.")
        # noinspection PyUnresolvedReferences
        return res.component[0].value

    @staticmethod
    def check(res, collection: set[str], member: Member) -> bool:
        return res.component[0].value in collection and res.user.id == member.id


def setup(bot: Bot):
    bot.add_cog(StudyGroups(bot))
