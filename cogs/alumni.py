import datetime
import re

import discord
from discord import TextChannel, Role
from discord.ext.commands import Cog, Bot, Context, command, BadArgument
from discord.ext.tasks import loop

from cogs.bot_status import listener
from cogs.util.ainit_ctx_mgr import AinitManager
from cogs.util.assign_variables import assign_role
from cogs.util.placeholder import Placeholder
from cogs.util.study_subject_util import StudySubjectUtil
from core import global_enum
from core.global_enum import ConfigurationNameEnum, SubjectsOrGroupsEnum, CollectionEnum
from core.logger import get_discord_child_logger
from core.predicates import has_role_plus, bot_chat
from mongo.alumni_roles import AlumniRoles, AlumniRole
from mongo.primitive_mongo_data import PrimitiveMongoData
from mongo.subjects_or_groups import SubjectsOrGroups, SubjectOrGroup

first_init = True
plus7_roles: set[Role] = set()
bot_channels: set[TextChannel] = set()
logger = get_discord_child_logger("alumni")
alumni_role: Placeholder = Placeholder()


class Alumni(Cog):
    """
    Some small role commands.
    """

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
        global plus7_roles, bot_channels, alumni_role
        # noinspection PyTypeChecker
        async with AinitManager(bot=self.bot,
                                loop=self.ainit,
                                need_init=self.need_init,
                                bot_channels=bot_channels) as need_init:
            if need_init:
                if7_plus_role: Role = await assign_role(self.bot, ConfigurationNameEnum.IF7_PLUS_ROLE)
                ib7_plus_role: Role = await assign_role(self.bot, ConfigurationNameEnum.IB7_PLUS_ROLE)
                dc7_plus_role: Role = await assign_role(self.bot, ConfigurationNameEnum.DC7_PLUS_ROLE)
                plus7_roles: set[Role] = {if7_plus_role, ib7_plus_role, dc7_plus_role}
                alumni_role.item = await assign_role(self.bot, ConfigurationNameEnum.ALUMNI_ROLE)
        logger.info(f"The cog is online.")

    def cog_unload(self):
        logger.warning("Cog has been unloaded.")

    @command(pass_context=True,
             name="graduationSeparator",
             brief="Sets the separator role.",
             help="The separator must be mentioned.")
    async def graduation_separator(self, ctx: Context, role):  # parameter only for pretty help.
        """
        Saves the graduation roles separator role:

        Args:
            ctx: The command context provided by the discord.py wrapper.

            role: The mentioned role.
        """
        if len(ctx.message.role_mentions) > 1:
            raise BadArgument

        role: Role = ctx.message.role_mentions[0]
        db = PrimitiveMongoData(CollectionEnum.ROLES)
        key = ConfigurationNameEnum.GRADUATION_SEPARATOR_ROLE
        msg = "separator"
        await StudySubjectUtil.update_category_and_separator(role.id, ctx, db, key, msg)

    @command(name="alumni",
             help="Mark yourself as an Alumni")
    @has_role_plus(plus7_roles)
    @bot_chat(bot_channels)
    async def alumni(self, ctx: Context):
        alumni_db = AlumniRoles(self.bot)
        graduation_roles: list[Role] = [document.role for document in await alumni_db.find({})]

        plus7_role: Role = [role for role in ctx.author.roles if role in plus7_roles][0]
        match = re.compile(r"([a-z]+)([0-9]+)\+", re.I)
        study_master, _ = re.match(match, plus7_role.name).groups()

        # People doing this command from January to Juni most likely graduated in the WS of the previous year
        is_ws: bool = datetime.datetime.now().month >= 1 or datetime.datetime.now().month < 7
        if is_ws:
            year = datetime.datetime.now().year - 2000
            current_graduation_name: str = f"WS{year - 1}/{year}"
        else:
            current_graduation_name: str = f"SS{datetime.datetime.now().year - 2000}"
        current_graduation_name = f"{study_master} " + current_graduation_name
        graduation_role: list[Role] = [role for role in graduation_roles if role.name == current_graduation_name]

        if not graduation_role:
            # make new graduation Role
            color = global_enum.colors.get(study_master, discord.Color.default())
            role: Role = await ctx.guild.create_role(name=current_graduation_name, reason="", color=color, hoist=False)

            graduation_separator: Role = await assign_role(self.bot, ConfigurationNameEnum.GRADUATION_SEPARATOR_ROLE)

            entry: AlumniRole = await alumni_db.insert_one(role)
            await entry.role.edit(position=graduation_separator.position - 1)
            logger.info(f"Created new graduation role: {current_graduation_name}")
            graduation_role = [entry.role]

        # assign the new Roles
        await ctx.author.add_roles(alumni_role.item, *graduation_role, reason="request by user")

        subject_db = SubjectsOrGroups(self.bot, SubjectsOrGroupsEnum.SUBJECT)
        subjects_documents: list[SubjectOrGroup] = await subject_db.find({})
        subject_roles: list[Role] = [document.role for document in subjects_documents]

        # remove the 7+ role and all subjects
        await ctx.author.remove_roles(
            *[role for role in ctx.author.roles if (role in plus7_roles) or (role in subject_roles)],
            reason="request by user")
        await ctx.reply(content=f"{ctx.author.mention} you are now an Alumni."
                                "Congratulation!"
                                "If your graduation Date-Role is wrong please contact an Admin.")


async def setup(bot: Bot):
    await bot.add_cog(Alumni(bot))
