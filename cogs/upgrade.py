import os
import re
from typing import Union, Sequence

import discord
from discord import Guild, Member, Role, TextChannel, NotFound, PermissionOverwrite
from discord.ext.commands import Cog, Bot, Context, command, is_owner, has_guild_permissions, ExtensionNotLoaded

from core import global_enum
from core.global_enum import SubjectsOrGroupsEnum, DBKeyWrapperEnum
from core.logger import get_discord_child_logger
from mongo.study_subject_relation import StudySubjectRelations, StudySubjectRelation
from mongo.subjects_or_groups import SubjectsOrGroups, SubjectOrGroup

logger = get_discord_child_logger("upgrade")


class Upgrade(Cog):
    """
    Provides the upgrade command
    """

    def __init__(self, bot: Bot):
        self.bot = bot
        logger.info(f"The cog is online.")

    def cog_unload(self):
        logger.warning("Cog has been unloaded.")

    @command(help="Performs the upgrade")
    @is_owner()
    @has_guild_permissions(administrator=True)
    async def upgrade(self, ctx: Context):
        logger.info("Started doing upgrade")

        logger.info("Disabling all commands")
        for filename in os.listdir("./cogs"):
            if filename.endswith(".py") and filename != "upgrade.py":
                try:
                    await ctx.bot.unload_extension(f"cogs.{filename[:-3]}")
                    logger.info(f"Unloaded: cogs.{filename[:-3]}")
                except ExtensionNotLoaded:
                    logger.info(f"Already Unloaded: cogs.{filename[:-3]}")
        logger.info("Disabled all commands")

        guild: Guild = ctx.guild
        members: Sequence[Member] = guild.members

        study_groups_db = SubjectsOrGroups(self.bot, SubjectsOrGroupsEnum.GROUP)
        study_groups_documents: list[SubjectOrGroup] = await study_groups_db.find({})

        subject_db = SubjectsOrGroups(self.bot, SubjectsOrGroupsEnum.SUBJECT)
        subjects_documents: list[SubjectOrGroup] = await subject_db.find({})
        subject_roles: list[Role] = [document.role for document in subjects_documents]

        links_db = StudySubjectRelations(self.bot)
        links_documents: list[StudySubjectRelation] = await links_db.find({})

        match = re.compile(r"([a-z]+)([0-9]+)", re.I)

        # remove every subject from everyone:
        logger.info("Starting to remove subjects from everyone")
        for member in members:
            logger.info(f"Checking {member.display_name}")
            roles_to_remove = [role for role in subject_roles]
            await member.remove_roles(*roles_to_remove, reason="upgrade")
        logger.info("Finished removing subjects from everyone")

        # recreate subject channels:
        logger.info("Starting to recreate the subject text channels")
        for document in subjects_documents:
            channel: TextChannel = document.chat
            name = channel.name
            if len([message async for message in channel.history(limit=1)]) == 0:
                logger.info(f"Don't need the recreate {name} channel")
                continue
            category = channel.category
            permissions = channel.overwrites
            new_channel = await guild.create_text_channel(name=name,
                                                          category=category,
                                                          overwrites=permissions,
                                                          nsfw=False,
                                                          reason="upgrade")
            try:
                await channel.delete(reason="upgrade")
            except NotFound:
                pass

            logger.info(f"Recreated {name} channel")

            new_document = {
                DBKeyWrapperEnum.CHAT.value: new_channel.id,
                DBKeyWrapperEnum.ROLE.value: document.role_id
            }
            await subject_db.update_one(document.document, new_document)
        logger.info("Finished to recreate the subject text channels")

        # rename the study groups to one semester up
        logger.info("Starting to rename study groups")
        for document in study_groups_documents:
            channel: TextChannel = document.chat
            role: Role = document.role

            study_master, study_semester = re.match(match, role.name).groups()
            new_name = f"{study_master}{int(study_semester) + 1}"

            logger.info(f"Renamed {role.name} to {new_name}")

            await channel.edit(name=new_name, reason="upgrade")
            await role.edit(name=new_name, reason="upgrade")

        logger.info("Finished renaming study groups")

        # create 1st semester study groups
        logger.info("Creating first semester study groups")
        for document in study_groups_documents:
            channel: TextChannel = document.chat

            study_master, study_semester = re.match(match, document.role.name).groups()

            color = global_enum.colors.get(study_master, discord.Color.default())
            if int(study_semester) == 2:
                name = f"{study_master}1"
                category = channel.category
                permissions: dict[Union[Role, Member], PermissionOverwrite] = channel.overwrites

                role: Role = await guild.create_role(name=name, reason="upgrade", color=color, hoist=True)
                permissions[role] = permissions.pop(document.role)
                channel: TextChannel = await guild.create_text_channel(name=name,
                                                                       category=category,
                                                                       overwrites=permissions,
                                                                       nsfw=False,
                                                                       reason="upgrade")
                await study_groups_db.insert_one((channel, role))
                await role.edit(position=document.role.position)
                logger.info(f"Created {name} study group")
        logger.info("Created first semester study groups")

        study_groups_documents: list[SubjectOrGroup] = await study_groups_db.find({})
        study_groups_roles: list[Role] = [document.role for document in study_groups_documents]

        # redo the links
        logger.info("Remapping the links")
        for document in study_groups_documents:
            role: Role = document.role

            study_master, study_semester = re.match(match, role.name).groups()
            if int(study_semester) != 1:
                links = [link for link in links_documents if link.group == document.role]
                lower_semester_role: Role = \
                    [role for role in study_groups_roles if role.name == f"{study_master}{int(study_semester) - 1}"][0]
                for link in links:
                    new_link = {
                        DBKeyWrapperEnum.GROUP.value: lower_semester_role.id,
                        DBKeyWrapperEnum.SUBJECT.value: link.subject.id,
                        DBKeyWrapperEnum.DEFAULT.value: link.default
                    }
                    await links_db.update_one(link.document, new_link)
                    logger.info(f"Remapping {link.subject.name} from {link.group.name} to {lower_semester_role.name}")
        logger.info("Done remapping the links")

        links_documents: list[StudySubjectRelation] = await links_db.find({})

        # assign everyone to their new subjects
        logger.info("Assigning everyone to their new subjects")
        for member in members:
            logger.info(f"Assigning {member.display_name} to his/her new subjects")
            groups: list[Role] = [role for role in member.roles if role in study_groups_roles]
            roles_to_add = [document.subject for document in links_documents if
                            (document.group in groups and document.default)]
            await member.add_roles(*roles_to_add, reason="upgrade")
        logger.info("Assigned everyone to their new subjects")

        logger.info("Finished upgrade")

        logger.warning("You need to restart the Bot")
        await ctx.reply(content="Please restart the bot")


async def setup(bot: Bot):
    await bot.add_cog(Upgrade(bot))
