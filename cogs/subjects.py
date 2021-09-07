import re
from typing import Union

from discord import Role, TextChannel, Member, User, Guild, Embed
from discord.ext.commands import Cog, Bot, has_guild_permissions, group, Context, BadArgument
from discord.ext.tasks import loop
from discord_components import DiscordComponents

from cogs.bot_status import listener
from cogs.util.ainit_ctx_mgr import AinitManager
from cogs.util.assign_variables import assign_set_of_roles
from cogs.util.placeholder import Placeholder
from cogs.util.study_subject_util import StudySubjectUtil
from core.error.error_collection import CantAssignToSubject, YouAlreadyHaveThisRoleError, NoStudyGroupAssigned, \
    CantRemoveSubject
from core.global_enum import SubjectsOrGroupsEnum, ConfigurationNameEnum, CollectionEnum
from core.logger import get_discord_child_logger
from core.predicates import bot_chat, has_role_plus
from mongo.primitive_mongo_data import PrimitiveMongoData
from mongo.study_subject_relation import StudySubjectRelations
from mongo.subjects_or_groups import SubjectsOrGroups

bot_channels: set[TextChannel] = set()
verified: Placeholder = Placeholder()
moderator: Placeholder = Placeholder()
subjects_roles: set[Role] = set()
first_init = True

logger = get_discord_child_logger("Subjects")


class Subjects(Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
        self.match = re.compile(r"([a-z]+)([0-9]+)", re.I)
        self.db = SubjectsOrGroups(self.bot, SubjectsOrGroupsEnum.SUBJECT)
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

    # subject group

    @group(pass_context=True,
           name="subject")
    @bot_chat(bot_channels)
    @has_role_plus(verified)
    async def subject(self, ctx: Context):
        if not ctx.invoked_subcommand:
            raise BadArgument
        member: Union[Member, User] = ctx.author
        logger.info(f'User="{member.name}#{member.discriminator}({member.id})", Command="{ctx.message.content}"')

    @subject.command(pass_context=True,
                     name="show")
    async def subject_show(self, ctx: Context):
        """
        Shows all possible opt-in and opt-out subjects of the user

        Args:
            ctx: The command context provided by the discord.py wrapper.
        """
        member: Union[Member, User] = ctx.author
        roles: list[Role] = member.roles

        subjects: list[Role] = await self.get_possible_subjects(roles)

        embed = Embed(title="Subjects",
                      description="You can opt-in/out of following subjects:")
        subjects_text: str = str([subject.name for subject in subjects if subject in roles])[1:-1]
        if subjects_text:
            embed.add_field(name="Opt-out Subjects", value=subjects_text.replace("'", "`").replace(",", "\n"),
                            inline=False)
        subjects_text: str = str([subject.name for subject in subjects if subject not in roles])[1:-1]
        if subjects_text:
            embed.add_field(name="Opt-in Subjects", value=subjects_text.replace("'", "`").replace(",", "\n"),
                            inline=False)

        await ctx.reply(embed=embed)

    @subject.command(pass_context=True,
                     name="add")
    async def subject_add(self, ctx: Context, subject: str):
        """
        opts-in a user into the specified subject

        Args:
            ctx: The command context provided by the discord.py wrapper.

            subject: The Subject to opt into
        """
        member: Union[Member, User] = ctx.author
        roles: list[Role] = member.roles

        subjects: list[Role] = await self.get_possible_subjects(roles)

        subject = subject.lower()

        if subject not in [subject.name.lower() for subject in subjects]:
            raise CantAssignToSubject

        if subject not in [subject.name.lower() for subject in subjects if subject not in roles]:
            raise YouAlreadyHaveThisRoleError

        role: Role = [role for role in subjects if role.name.lower() == subject][0]
        await member.add_roles(role)
        embed = Embed(title="successfully assigned",
                      description=f"Assigned you to {role.mention}")
        await ctx.reply(content=member.mention, embed=embed)
        return

    @subject.command(pass_context=True,
                     aliases=["rem", "rm"],
                     name="remove")
    async def subject_remove(self, ctx: Context, subject: str):
        """
        opts-out a user into the specified subject

        Args:
            ctx: The command context provided by the discord.py wrapper.

            subject: The Subject to opt into
        """
        member: Union[Member, User] = ctx.author
        roles: list[Role] = member.roles

        subjects: list[Role] = await self.get_possible_subjects(roles)

        if subject not in [subject.name for subject in subjects if subject in roles]:
            raise CantRemoveSubject

        role: Role = [role for role in subjects if role.name == subject][0]
        await member.add_roles(role)
        embed = Embed(title="successfully Opted out of subject",
                      description=f"Removed you from {role.mention}")
        await ctx.reply(content=member.mention, embed=embed)
        return

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
        if len(ctx.message.role_mentions) != 1:
            raise BadArgument

        role: Role = ctx.message.role_mentions[0]
        key = ConfigurationNameEnum.SUBJECTS_SEPARATOR_ROLE

        db = PrimitiveMongoData(CollectionEnum.ROLES)
        msg = "separator"
        await StudySubjectUtil.update_category_and_separator(role.id, ctx, db, key, msg)

    async def get_possible_subjects(self, roles: list[Role]) -> list[Role]:
        all_study_groups = await SubjectsOrGroups(self.bot, SubjectsOrGroupsEnum.GROUP).find({})
        study_group: list[Role] = [document.role for document in all_study_groups if document.role in roles]
        if not study_group:
            raise NoStudyGroupAssigned
        study_group: Role = study_group[0]
        study_master, study_semester = re.match(self.match, study_group.name).groups()
        study_semester = int(study_semester)
        compatible_study_groups: list[Role] = [study_group]
        for i in range(study_semester):
            compatible_study_groups += [document.role for document in all_study_groups if
                                        document.role.name == study_master + str(i)]
        return [document.subject for document in
                await StudySubjectRelations(self.bot).find({}) if
                document.group in compatible_study_groups]


def setup(bot: Bot):
    bot.add_cog(Subjects(bot))
