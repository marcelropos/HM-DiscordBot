import re
from typing import Union

import discord
from discord import Guild, Role, Member, User, TextChannel, Embed
from discord.ext.commands import Cog, Bot, command, Context, group, BadArgument, has_guild_permissions
from discord.ext.tasks import loop

from cogs.bot_status import listener
from cogs.util.ainit_ctx_mgr import AinitManager
from cogs.util.assign_variables import assign_set_of_roles
from cogs.util.custom_select import CustomSelect
from cogs.util.placeholder import Placeholder
from cogs.util.select_view import SelectRoleView
from cogs.util.study_subject_util import StudySubjectUtil
from core import global_enum
from core.error.error_collection import FailedToGrantRoleError, MissingInteractionError
from core.global_enum import SubjectsOrGroupsEnum, CollectionEnum, ConfigurationNameEnum, DBKeyWrapperEnum
from core.logger import get_discord_child_logger
from core.predicates import bot_chat, is_not_in_group, has_role_plus
from mongo.primitive_mongo_data import PrimitiveMongoData
from mongo.study_subject_relation import StudySubjectRelations
from mongo.subjects_or_groups import SubjectsOrGroups

bot_channels: set[TextChannel] = set()
verified: set[Role] = set()
moderator: Placeholder = Placeholder()
study_groups: set[Role] = set()
first_init = True

logger = get_discord_child_logger("StudyGroups")


class StudyGroups(Cog):
    """
    StudyGroup commands.
    """

    def __init__(self, bot: Bot):
        self.bot = bot
        self.match = re.compile(r"([a-z]+)([0-9]+)", re.I)
        self.db = SubjectsOrGroups(self.bot, SubjectsOrGroupsEnum.GROUP)
        self.need_init = True
        if not first_init:
            self.ainit.start()
        logger.info(f"The cog is online.")

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
        async with AinitManager(bot=self.bot,
                                loop=self.ainit,
                                need_init=self.need_init,
                                bot_channels=bot_channels,
                                verified=verified,
                                moderator=moderator) as need_init:
            if need_init:
                await assign_set_of_roles(self.bot.guilds[0], self.db, study_groups)

    def cog_unload(self):
        logger.warning("Cog has been unloaded.")

    # commands

    @command(brief="Gain a study role.",
             help="This Interactive Command will help you select your course and semester.\n"
                  "**CAUTION** Higher semesters can only be assigned by mods.")
    @bot_chat(bot_channels)
    @is_not_in_group(study_groups)
    @has_role_plus(verified)
    async def study(self, ctx: Context):
        """
        Assigns a study role to the user of the command.

        Args:
            ctx: The command context provided by the discord.py wrapper.
        """
        guild: Guild = ctx.guild
        member: Union[Member, User] = ctx.author

        groups: list[Role] = [guild.get_role(document.role_id) for document in await self.db.find({})]
        # limit self assigment to semester one and two
        groups = [_group for _group in groups if (int((re.match(self.match, _group.name).groups())[1]) < 3)]
        await self.assign_role(ctx, groups, member)

    @command(brief="Grant someone a study role.",
             help="Select the member and choose the appropriate subject and semester in the interactive menu.")
    @bot_chat(bot_channels)
    @has_role_plus(moderator)
    async def grant(self, ctx: Context, member):  # parameter only for pretty help.
        """
        Assigns a study role to the mentioned member.

        Args:
            ctx: The command context provided by the discord.py wrapper.

            member: The member who is to receive a role.

        Raises:
            FailedToGrantRoleError
        """
        global study_groups
        guild: Guild = ctx.guild
        member: Union[Member, User] = ctx.message.mentions[0]

        assigned_to = study_groups.intersection(set(member.roles))
        if assigned_to:
            raise FailedToGrantRoleError(assigned_to.pop(), member)

        groups: list[Role] = [guild.get_role(document.role_id) for document in await self.db.find({})]
        await self.assign_role(ctx, groups, member)

    # group group

    @group(pass_context=True,
           name="group",
           help="Manages the study groups.")
    @bot_chat(bot_channels)
    @has_guild_permissions(administrator=True)
    async def _group(self, ctx: Context):
        if not ctx.invoked_subcommand:
            raise BadArgument
        member: Union[Member, User] = ctx.author
        logger.info(f'User="{member.name}#{member.discriminator}({member.id})", Command="{ctx.message.content}"')

    @_group.command(pass_context=True,
                    name="add",
                    brief="Creates a Study group.",
                    help="The name must contain the tag and the semester number.")
    async def group_add(self, ctx: Context, name: str):
        """
        Adds a new role-channel pair as a group.

        Args:
            ctx: The command context provided by the discord.py wrapper.

            name: The name of the role and the chat.
        """
        guild: Guild = ctx.guild
        category_key = ConfigurationNameEnum.GROUP_CATEGORY
        separator_key = ConfigurationNameEnum.STUDY_SEPARATOR_ROLE

        study_master = re.match(self.match, name).groups()[0]

        color = global_enum.colors.get(study_master, discord.Color.default())

        study_groups.add((await StudySubjectUtil.get_server_objects(category_key,
                                                                    guild,
                                                                    name,
                                                                    separator_key,
                                                                    self.db,
                                                                    color=color)).role)

    @_group.command(pass_context=True,
                    name="edit",
                    brief="Edits the role of a study group",
                    help="Replaces the study group in the database with the new role and chat")
    async def group_edit(self, ctx: Context, channel: TextChannel, role: Role, channel2: TextChannel):
        """
        Edits a study group

        Args:
            ctx: The command context provided by the discord.py wrapper.

            channel: The old chat.

            role: the new role.

            channel2: the new chat.
        """
        document = (await self.db.find({DBKeyWrapperEnum.CHAT.value: channel.id}))[0]
        if not document:
            return
        new_document = {
            DBKeyWrapperEnum.CHAT.value: channel2.id,
            DBKeyWrapperEnum.ROLE.value: role.id
        }
        await self.db.update_one(document.document, new_document)

    @_group.command(pass_context=True,
                    name="category",
                    brief="Sets the category",
                    help="The category must be given as an int value.")
    async def group_category(self, ctx: Context, category: int):
        """
        Saves the group separator role:

        Args:
            ctx: The command context provided by the discord.py wrapper.

            category: The category id for the channels.
        """

        db = PrimitiveMongoData(CollectionEnum.CATEGORIES)
        key = ConfigurationNameEnum.GROUP_CATEGORY
        msg = "category"
        await StudySubjectUtil.update_category_and_separator(category, ctx, db, key, msg)

    @_group.command(pass_context=True,
                    name="separator",
                    brief="Sets the separator role.",
                    help="The separator must be mentioned.")
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

    async def assign_role(self, ctx: Context,
                          groups: list[Role],
                          member: Union[Member, User]):
        group_names = sorted({str((re.match(self.match, _role.name).groups())[0])
                              for _role in groups})
        group_semester = sorted({str((re.match(self.match, _role.name).groups())[1]) for _role in groups})
        custom_select1: CustomSelect = CustomSelect(0, "Select your group", group_names,
                                                    "I received your group input.")
        custom_select2: CustomSelect = CustomSelect(1, "Select your semester", group_semester,
                                                    "I received your semester input.")
        role_view: SelectRoleView = SelectRoleView([custom_select1, custom_select2])
        await ctx.reply(content="Please select **one** of the following groups.", view=role_view)

        if await role_view.wait():
            raise MissingInteractionError
        a: str = custom_select1.values[0]
        b: str = custom_select2.values[0]

        role: Role = {role for role in groups if role.name == a + b}.pop()

        subjects = [document.subject for document in await StudySubjectRelations(self.bot).find(
            {DBKeyWrapperEnum.GROUP.value: role.id, DBKeyWrapperEnum.DEFAULT.value: True})]
        await member.add_roles(role, *subjects)
        embed = Embed(title="Grant new role",
                      description=f"Congratulations, you have received the {role.mention} role.\n"
                                  f"You also received the appropriate subjects for this study group.")
        await ctx.reply(content=member.mention, embed=embed)


async def setup(bot: Bot):
    await bot.add_cog(StudyGroups(bot))
