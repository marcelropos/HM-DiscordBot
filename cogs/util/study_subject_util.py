from typing import Optional

from discord import CategoryChannel, Role, PermissionOverwrite, TextChannel, Guild, Embed
from discord.ext.commands import Context

from core.error.error_collection import BrokenConfigurationError
from core.global_enum import CollectionEnum, ConfigurationNameEnum
from mongo.primitive_mongo_data import PrimitiveMongoData
from mongo.subjects_or_groups import SubjectOrGroup, SubjectsOrGroups


class StudySubjectUtil:
    @staticmethod
    async def get_server_objects(category_key: ConfigurationNameEnum,
                                 guild: Guild,
                                 name: str,
                                 separator_key: ConfigurationNameEnum,
                                 db: SubjectsOrGroups) -> SubjectOrGroup:
        """
        Creates a "role-chat" pair, saves it and places it correctly.

        Args:
            category_key: The category under which the chat should appear.

            guild: The server on which the bot is.

            name: The name of the role and the chat

            separator_key: The position under which the role should be.

            db: The database connection to be used.

        Returns:
            A SubjectOrGroup which contains the created pair.

        Raises:
            Forbidden,ServerSelectionTimeoutError
        """
        study_category: CategoryChannel = guild.get_channel(
            (await PrimitiveMongoData(CollectionEnum.CATEGORIES)
             .find_one({category_key.value: {"$exists": True}}))[category_key.value])

        study_separator: Role = guild.get_role(
            (await PrimitiveMongoData(CollectionEnum.ROLES)
             .find_one({separator_key.value: {"$exists": True}}))[separator_key.value])

        role: Role = await guild.create_role(name=name,
                                             reason="")

        role_id: Optional[dict] = await PrimitiveMongoData(CollectionEnum.ROLES).find_one(
            {ConfigurationNameEnum.RESTRICTED.value: {"$exists": True}})

        restricted_role = None
        if role_id:
            restricted_role = guild.get_role(role_id[ConfigurationNameEnum.RESTRICTED.value])

        if not restricted_role:
            raise BrokenConfigurationError(CollectionEnum.ROLES.value, ConfigurationNameEnum.RESTRICTED.value)

        overwrites = {role: PermissionOverwrite(view_channel=True),
                      restricted_role: PermissionOverwrite(send_messages=False),
                      guild.default_role: PermissionOverwrite(view_channel=False)}
        channel: TextChannel = await guild.create_text_channel(name=name,
                                                               category=study_category,
                                                               overwrites=overwrites,
                                                               nsfw=False,
                                                               reason="")
        entry: SubjectOrGroup = await db.insert_one((channel, role))
        await entry.role.edit(position=study_separator.position - 1)

        return entry

    @staticmethod
    async def update_category_and_separator(value: int,
                                            ctx: Context,
                                            db: PrimitiveMongoData,
                                            key: ConfigurationNameEnum,
                                            msg: str):
        """
        Updates a db entry.
        """
        find = {key.value: {"$exists": True}}
        if await db.find_one(find):
            await db.update_one(find, {key.value: value})
        else:
            await db.insert_one({key.value: value})
        embed = Embed(title="Study Groups",
                      description=f"Set {msg} successfully!")
        await ctx.reply(embed=embed)
