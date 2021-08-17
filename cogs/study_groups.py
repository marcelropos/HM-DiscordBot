import asyncio
import re
from typing import Union

from discord import Guild, Role, Member, User
from discord.ext.commands import Cog, Bot, command, Context, group, bot_has_guild_permissions, BadArgument
from discord_components import DiscordComponents, Interaction, Select, \
    SelectOption

from cogs.botStatus import listener
from cogs.util.study_subject_util import StudySubjectUtil
from core.globalEnum import SubjectsOrGroupsEnum, CollectionEnum, ConfigurationNameEnum
from mongo.primitiveMongoData import PrimitiveMongoData
from mongo.subjectsorgroups import SubjectsOrGroups


class StudyGroups(Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
        self.match = re.compile(r"([a-z]+)([0-9]+)", re.I)
        self.db = SubjectsOrGroups(self.bot, SubjectsOrGroupsEnum.GROUP)
        self.startup = True
        self.groups = {}

    @listener()
    async def on_ready(self):
        if self.startup:
            DiscordComponents(self.bot)
            self.startup = False

    def cog_unload(self):
        pass

    @command()
    async def study(self, ctx: Context):
        guild: Guild = ctx.guild
        member: Union[Member, User] = ctx.author
        groups = sorted({guild.get_role(document.role_id) for document in await self.db.find({})},
                        key=lambda role: role.name)
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

    async def get_role(self, member, groups: list[Role], group_names, group_semester) -> Role:
        a, b = await asyncio.gather(
            self.wait_for_group(group_names, member),
            self.wait_for_semester(group_semester, member)
        )

        result = set()
        result.update({role for role in groups if role.name == a + b})
        result.update({role for role in groups if role.name == b + a})
        # noinspection PyTypeChecker
        return result.pop()

    async def wait_for_group(self, group_names, member):
        res: Interaction = await self.bot.wait_for("select_option",
                                                   check=lambda x: self.check(x, group_names, member))
        await res.respond(content=f"I received your group input.")
        # noinspection PyUnresolvedReferences
        return res.component[0].value

    async def wait_for_semester(self, group_semester, member):
        res: Interaction = await self.bot.wait_for("select_option",
                                                   check=lambda x: self.check(x, group_semester, member))
        await res.respond(content="I received your semester input.")
        # noinspection PyUnresolvedReferences
        return res.component[0].value

    @staticmethod
    def check(res, collection: dict, member: Member) -> bool:
        return res.component[0].value in collection and res.user.id == member.id

    @group.command(pass_context=True,
                   name="add")
    async def group_add(self, ctx: Context, name: str):
        guild: Guild = ctx.guild
        category_key = ConfigurationNameEnum.STUDY_CATEGORY
        separator_key = ConfigurationNameEnum.STUDY_SEPARATOR_ROLE

        await StudySubjectUtil.get_server_objects(category_key,
                                                  guild,
                                                  name,
                                                  separator_key,
                                                  self.db)

    @group.command(pass_context=True,
                   name="rename")
    async def group_rename(self):
        pass

    @group.command(pass_context=True,
                   name="category")
    async def group_category(self, ctx: Context, category: int):
        db = PrimitiveMongoData(CollectionEnum.CATEGORIES)
        key = ConfigurationNameEnum.STUDY_CATEGORY
        msg = "category"
        await StudySubjectUtil.update_category_and_separator(category, ctx, db, key, msg)

    @group.command(pass_context=True,
                   name="separator")
    async def group_separator(self, ctx: Context, role):
        # noinspection PyStatementEffect
        role
        if len(ctx.message.role_mentions) > 1:
            raise BadArgument

        role: Role = ctx.message.role_mentions[0]
        db = PrimitiveMongoData(CollectionEnum.ROLES)
        key = ConfigurationNameEnum.STUDY_SEPARATOR_ROLE
        msg = "separator"
        await StudySubjectUtil.update_category_and_separator(role.id, ctx, db, key, msg)


def setup(bot: Bot):
    bot.add_cog(StudyGroups(bot))
