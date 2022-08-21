from typing import Optional

from discord import TextChannel, Role, Guild, CategoryChannel
from discord.ext.commands import Bot

from core.error.error_collection import BrokenConfigurationError
from core.global_enum import CollectionEnum, ConfigurationNameEnum
from mongo.primitive_mongo_data import PrimitiveMongoData
from mongo.subjects_or_groups import SubjectsOrGroups


async def assign_accepted_chats(bot: Bot, channels: set[TextChannel]):
    """
    Save accepted chats to a variable.

    Args:
        bot: The bot class.

        channels: A set in which the accepted chats should be stored.
    """

    channels.clear()
    db = PrimitiveMongoData(CollectionEnum.CHANNELS)

    # noinspection PyTypeChecker
    command_key: str = ConfigurationNameEnum.BOT_COMMAND_CHAT.value
    command: Optional[dict] = await db.find_one({command_key: {"$exists": True}})
    # noinspection PyTypeChecker
    debug_key: str = ConfigurationNameEnum.DEBUG_CHAT.value
    debug: Optional[dict] = await db.find_one({debug_key: {"$exists": True}})

    if command and debug:
        channels.add(bot.get_channel(command[command_key]))
        channels.add(bot.get_channel(debug[debug_key]))
    else:
        raise BrokenConfigurationError(db.collection.name, [command_key, debug_key])
    if None in channels:
        raise BrokenConfigurationError(db.collection.name, [command_key, debug_key])


async def assign_role(bot: Bot, role_name: ConfigurationNameEnum) -> Optional[Role]:
    """
    Loads the verified role and takes care of possible errors.

    Args:
         bot: The bot class.

         role_name: The configured role.

    Return:
        If success verified role, otherwise none.
    """

    db = PrimitiveMongoData(CollectionEnum.ROLES)

    role_key = role_name.value
    role_id: Optional[dict] = await db.find_one({role_key: {"$exists": True}})

    role: Optional[Role]
    if role_id:
        role = bot.guilds[0].get_role(role_id[role_key])
    else:
        role = None

    if not role:
        # noinspection PyTypeChecker
        raise BrokenConfigurationError(db.collection.name, role_key)

    return role


async def assign_chat(bot: Bot, channel_name: ConfigurationNameEnum) -> Optional[TextChannel]:
    """
    Loads the verified channel and takes care of possible errors.

    Args:
         bot: The bot class.

         channel_name: The configured channel.

    Return:
        If success verified channel, otherwise none.
    """

    db = PrimitiveMongoData(CollectionEnum.CHANNELS)

    role_key = channel_name.value
    channel_id: Optional[dict] = await db.find_one({role_key: {"$exists": True}})

    channel: Optional[TextChannel]
    if channel_id:
        channel = bot.guilds[0].get_channel(channel_id[role_key])
    else:
        channel = None

    if not channel:
        # noinspection PyTypeChecker
        raise BrokenConfigurationError(db.collection.name, role_key)

    return channel


async def assign_category(bot: Bot, category_name: ConfigurationNameEnum) -> Optional[CategoryChannel]:
    """
    Loads the verified category and takes care of possible errors.

    Args:
         bot: The bot class.

         category_name: The configured category.

    Return:
        If success verified category, otherwise none.
    """

    db = PrimitiveMongoData(CollectionEnum.CATEGORIES)

    category_key = category_name.value
    category_id: Optional[dict] = await db.find_one({category_key: {"$exists": True}})

    category: Optional[CategoryChannel]
    if category_id:
        category = bot.guilds[0].get_channel(category_id[category_key])
    else:
        category = None

    if not category:
        # noinspection PyTypeChecker
        raise BrokenConfigurationError(db.collection.name, category_key)

    return category


async def assign_set_of_roles(guild: Guild, db: SubjectsOrGroups, roles: set[Role]):
    roles.clear()
    roles.update(document.role for document in await db.find({}))
