from functools import reduce
from typing import Union

from discord import Role, TextChannel, Member, User, Embed
from discord.ext.commands import Cog, Bot, has_guild_permissions, group, Context, BadArgument
from discord.ext.tasks import loop
from discord_components import DiscordComponents

from cogs.bot_status import listener
from cogs.util.ainit_ctx_mgr import AinitManager
from core.error.error_collection import GroupOrSubjectNotFoundError, LinkingNotFoundError
from core.global_enum import SubjectsOrGroupsEnum, DBKeyWrapperEnum
from core.logger import get_discord_child_logger
from core.predicates import bot_chat
from mongo.study_subject_relation import StudySubjectRelations
from mongo.subjects_or_groups import SubjectsOrGroups

bot_channels: set[TextChannel] = set()
first_init = True

logger = get_discord_child_logger("Linking")


class Linking(Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
        self.db = StudySubjectRelations(self.bot)
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
        global bot_channels
        # noinspection PyTypeChecker
        async with AinitManager(bot=self.bot,
                                loop=self.ainit,
                                need_init=self.need_init,
                                bot_channels=bot_channels) as need_init:
            if need_init:
                DiscordComponents(self.bot)

    # link group

    @group(pass_context=True,
           name="link")
    @bot_chat(bot_channels)
    @has_guild_permissions(administrator=True)
    async def link(self, ctx: Context):
        if not ctx.invoked_subcommand:
            raise BadArgument
        member: Union[Member, User] = ctx.author
        logger.info(f'User="{member.name}#{member.discriminator}({member.id})", Command="{ctx.message.content}"')

    @link.command(pass_context=True)
    async def add(self, ctx: Context,
                  study_role: Role,  # parameter only for pretty help.
                  subject_role: Role,  # parameter only for pretty help.
                  default: bool):
        """
        Adds a new subject to study link

        Args:
            ctx: The command context provided by the discord.py wrapper.

            study_role: The name of the study role

            subject_role: The name of the subject role

            default: If this link is assigned by default when joining the study group
        """

        study_role, subject_role = await self.check_mentions(ctx)

        existing_link = [document for document in await self.db.find({}) if
                         document.group == study_role and document.subject == subject_role]

        if existing_link:
            existing_link = existing_link[0].document
            new_link = {
                DBKeyWrapperEnum.GROUP.value: study_role.id,
                DBKeyWrapperEnum.SUBJECT.value: subject_role.id,
                DBKeyWrapperEnum.DEFAULT.value: default
            }
            await self.db.update_one(existing_link, new_link)
            embed = Embed(title="Linking Add",
                          description=f"Successfully updated <@&{study_role.id}> to <@&{subject_role.id}> "
                                      f"with default={default}")
        else:
            await self.db.insert_one((study_role, subject_role, default))
            embed = Embed(title="Linking Add",
                          description=f"Successfully linked <@&{study_role.id}> to <@&{subject_role.id}> "
                                      f"with default={default}")
        await ctx.reply(embed=embed)

    @link.command(pass_context=True,
                  aliases=["rem", "rm"])
    async def remove(self, ctx: Context,
                     study_role: Role,  # parameter only for pretty help.
                     subject_role: Role):  # parameter only for pretty help.
        """
        Removes a link between study group and subject

        Args:
            ctx: The command context provided by the discord.py wrapper.

            study_role: The name of the study role

            subject_role: The name of the subject role
        """

        study_role, subject_role = await self.check_mentions(ctx)

        link = [document for document in await self.db.find({}) if
                document.group == study_role and document.subject == subject_role]

        if not link:
            raise LinkingNotFoundError

        await self.db.delete_one(link[0].document)
        embed = Embed(title="Linking Remove",
                      description=f"Successfully deleted link <@&{study_role.id}> to <@&{subject_role.id}> "
                                  f"with default={link[0].default}")
        await ctx.reply(embed=embed)

    @link.command(pass_context=True)
    async def show(self, ctx: Context):
        """
        Shows all saved linking

        Args:
            ctx: The command context provided by the discord.py wrapper.
        """

        links = [document for document in await self.db.find({})]
        if links:
            default_links: dict[str, list[str]] = dict()
            non_default_links: dict[str, list[str]] = dict()
            links = [(f"<@&{link.group.id}>", f"<@&{link.subject.id}>", link.default) for link in links]
            for study, subject, default in links:
                if default:
                    if study in default_links:
                        default_links[study].append(subject)
                    else:
                        default_links[study] = [subject]
                else:
                    if study in non_default_links:
                        non_default_links[study].append(subject)
                    else:
                        non_default_links[study] = [subject]

            embed = Embed(title="Linking:",
                          description=f"At the moment there are following linking between study groups and subjects:")
            linking_text = ""
            for study, subjects in default_links.items():
                linking_text += f"{study} : {reduce((lambda x, y: x + ' ' + y), subjects)}\n"
            if linking_text:
                embed.add_field(name="Default = True", value=linking_text, inline=False)

            linking_text = ""
            for study, subjects in non_default_links.items():
                linking_text += f"{study} : {reduce((lambda x, y: x + ' ' + y), subjects)}\n"
            if linking_text:
                embed.add_field(name="Default = False", value=linking_text, inline=False)
        else:
            embed = Embed(title="Linking",
                          description="No linking saved")
        await ctx.reply(embed=embed)

    async def check_mentions(self, ctx: Context) -> tuple[Role, Role]:
        if len(ctx.message.role_mentions) != 2:
            raise BadArgument

        study_role: Role = ctx.message.role_mentions[0]
        subject_role: Role = ctx.message.role_mentions[1]

        groups: list[Role] = [document.role for document in
                              await SubjectsOrGroups(self.bot, SubjectsOrGroupsEnum.GROUP).find({})]
        subjects: list[Role] = [document.role for document in
                                await SubjectsOrGroups(self.bot, SubjectsOrGroupsEnum.SUBJECT).find({})]

        if study_role not in groups:
            if subject_role in groups:  # order was reversed
                tmp = study_role
                study_role = subject_role
                subject_role = tmp
            else:
                raise GroupOrSubjectNotFoundError(f"<@&{subject_role.name}>", SubjectsOrGroupsEnum.GROUP)
        if subject_role not in subjects:
            raise GroupOrSubjectNotFoundError(f"<@&{subject_role.name}>", SubjectsOrGroupsEnum.SUBJECT)

        return study_role, subject_role


def setup(bot: Bot):
    bot.add_cog(Linking(bot))
