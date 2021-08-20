from typing import Optional

from discord import TextChannel, Role
from discord.ext.commands import Bot

from core.error.error_collection import BrokenConfigurationError
from core.globalEnum import CollectionEnum, ConfigurationNameEnum
from mongo.primitiveMongoData import PrimitiveMongoData


async def assign_accepted_chats(bot: Bot, channels: set[TextChannel]):
    """
    Save accepted chats to a variable.

    Args:
        bot: The bot class.

        channels: A set in which the accepted chats should be stored.
    """

    channels.clear()
    db = PrimitiveMongoData(CollectionEnum.CHANNELS)

    command_key = ConfigurationNameEnum.BOT_COMMAND_CHAT.value
    command: Optional[dict] = await db.find_one({command_key: {"$exists": True}})
    debug_key = ConfigurationNameEnum.DEBUG_CHAT.value
    debug: Optional[dict] = await db.find_one({debug_key: {"$exists": True}})

    if command and debug:
        channels.add(bot.get_channel(command[command_key]))
        channels.add(bot.get_channel(debug[debug_key]))
    else:
        raise BrokenConfigurationError
    if None in channels:
        raise BrokenConfigurationError


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
        raise BrokenConfigurationError

    return role