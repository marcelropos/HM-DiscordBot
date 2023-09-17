import datetime
import os
import re
from typing import Union, Sequence
from asyncio import sleep

import discord
from discord import Guild, Member, Role, TextChannel, NotFound, PermissionOverwrite, Color
from discord.ext.commands import Cog, Bot, Context, command, is_owner, has_guild_permissions, ExtensionNotLoaded

from cogs.util.assign_variables import assign_role
from core import global_enum
from core.global_enum import SubjectsOrGroupsEnum, DBKeyWrapperEnum, ConfigurationNameEnum, CollectionEnum
from core.logger import get_discord_child_logger

from mongo.primitive_mongo_data import PrimitiveMongoData
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
        if7_plus_role: Role = await assign_role(self.bot, ConfigurationNameEnum.IF7_PLUS_ROLE)
        ib7_plus_role: Role = await assign_role(self.bot, ConfigurationNameEnum.IB7_PLUS_ROLE)
        dc7_plus_role: Role = await assign_role(self.bot, ConfigurationNameEnum.DC7_PLUS_ROLE)
        plus_roles: dict[str, Role] = {"IF": if7_plus_role, "IB": ib7_plus_role, "DC": dc7_plus_role}

        subject_db = SubjectsOrGroups(self.bot, SubjectsOrGroupsEnum.SUBJECT)
        subjects_documents: list[SubjectOrGroup] = await subject_db.find({})
        subject_roles: list[Role] = [document.role for document in subjects_documents]

        links_db = StudySubjectRelations(self.bot)
        links_documents: list[StudySubjectRelation] = await links_db.find({})

        match = re.compile(r"([a-z]+)([0-9]+)", re.I)

        # remove every subject from everyone:
        logger.info("Starting to remove subjects from everyone")
        count = len(members)
        for i, member in enumerate(members):
            logger.info(f"Checking {member.display_name} | {round((i + 1) / count * 100, 2)}%")

            roles_to_remove: set[Role] = {role for role in subject_roles}.intersection(set(member.roles))
            if roles_to_remove:
                logger.info(f"remove {[role.name for role in roles_to_remove]} from {member.display_name}")
                await member.remove_roles(*roles_to_remove, reason="upgrade")
                await sleep(120)
            else:
                logger.info(f"No roles to remove from {member.display_name}")

        logger.info("Finished removing subjects from everyone")

        # recreate subject channels:
        logger.info("Starting to recreate the subject text channels")
        count = len(subjects_documents)
        for i, document in enumerate(subjects_documents):
            channel: TextChannel = document.chat
            name = channel.name
            logger.info(f"Checking {name} | {round((i + 1) / count * 100, 2)}%")
            if not [message async for message in channel.history(limit=1)]:
                logger.info(f"Skipped {name} channel")
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
            await sleep(120)
        logger.info("Finished to recreate the subject text channels")

        # rename the study groups to one semester up
        count = len(study_groups_documents)
        logger.info("Starting to rename study groups")
        documents_to_remove: list[SubjectOrGroup] = []
        for document in study_groups_documents:
            channel: TextChannel = document.chat
            role: Role = document.role

            study_master, study_semester = re.match(match, role.name).groups()

            if int(study_semester) == 7:
                documents_to_remove.append(document)

                # since the role and chat is deleted from the database here, it won't be renamed in the next upgrade
                await study_groups_db.delete_one({DBKeyWrapperEnum.ID.value: document.id})

                # add members of old XY7 Role to the XY7+ Role
                for member in role.members:
                    await member.add_roles(plus_roles[study_master], reason="upgrade")

                year = (datetime.datetime.now().year - ((int(study_semester) - 1) // 2)) - 2000
                new_name = f"{study_master} WS{year}/{year + 1}"
            else:
                new_name = f"{study_master}{int(study_semester) + 1}"

            logger.info(f"Renamed {role.name} to {new_name} | {round((i + 1) / count * 100, 2)}%")

            await channel.edit(name=new_name, reason="upgrade")
            await role.edit(name=new_name, reason="upgrade")
            await sleep(120)

        study_groups_documents = [document for document in study_groups_documents if
                                  document not in documents_to_remove]
        logger.info("Finished renaming study groups")

        # create 1st semester study groups
        logger.info("Creating first semester study groups")
        count = len(study_groups_documents)
        for i, document in enumerate(study_groups_documents):
            channel: TextChannel = document.chat

            study_master, study_semester = re.match(match, document.role.name).groups()

            if int(study_semester) == 2:
                name = f"{study_master}1"

                color_document = await PrimitiveMongoData(CollectionEnum.GROUP_COLOR).find_one(
                    {study_master: {"$exists": True}})
                color: Color = Color(color_document[study_master]) if color_document else Color.default()

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
                logger.info(f"Created {name} study group | {round((i + 1) / count * 100, 2)}%")
                await sleep(120)
        logger.info("Created first semester study groups")

        study_groups_documents: list[SubjectOrGroup] = await study_groups_db.find({})
        study_groups_roles: list[Role] = [document.role for document in study_groups_documents]

        # redo the links
        count = len(study_groups_documents)
        logger.info("Remapping the links")
        for i, document in enumerate(study_groups_documents):
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
                    logger.info(
                        f"Remapping {link.subject.name} from {link.group.name} to {lower_semester_role.name} "
                        f"| {round((i + 1) / count * 100, 2)}%")
        logger.info("Done remapping the links")

        links_documents: list[StudySubjectRelation] = await links_db.find({})

        # assign everyone to their new subjects
        count = len(members)
        logger.info("Assigning everyone to their new subjects")
        for i, member in enumerate(members):
            logger.info(f"Assigning {member.display_name} to his/her new subjects | {round((i + 1) / count * 100, 2)}%")
            groups: list[Role] = [role for role in member.roles if role in study_groups_roles]
            roles_to_add = [document.subject for document in links_documents if
                            (document.group in groups and document.default)]

            if roles_to_add:
                logger.info(f"add {[role.name for role in roles_to_add]} to {member.display_name}")
                await member.add_roles(*roles_to_add, reason="upgrade")
            else:
                logger.info(f"No roles to add to {member.display_name}")
            await sleep(120)

        logger.info("Assigned everyone to their new subjects")

        logger.info("Finished upgrade")

        logger.warning("You need to restart the Bot")
        await ctx.reply(content="Please restart the bot")


async def setup(bot: Bot):
    await bot.add_cog(Upgrade(bot))
