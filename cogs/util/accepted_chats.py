from typing import Optional

from discord import TextChannel, Role
from discord.ext.commands import Bot
from pymongo.errors import ServerSelectionTimeoutError

from core.error.error_collection import BrokenConfigurationError
from core.error.error_reply import startup_error_reply
from core.globalEnum import CollectionEnum, ConfigurationNameEnum
from core.logger import get_discord_child_logger, get_mongo_child_logger
from mongo.primitiveMongoData import PrimitiveMongoData

error_msg = "Due to the previous reason, all commands limited to chats are out of function!"


async def assign_accepted_chats(bot: Bot, channels: set[TextChannel]):
    """
    Save accepted chats to a variable.

    Args:
        bot: The bot class.

        channels: A set in which the accepted chats should be stored.
    """
    try:

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

    except (TypeError, BrokenConfigurationError):
        await handle_broken_config(bot)

    except ServerSelectionTimeoutError:
        await handle_db_connection(bot)


async def assign_verified_role(bot: Bot) -> Optional[Role]:
    """
    Loads the verified role and takes care of possible errors.

    Args:
         bot: The bot class.

    Return:
        If success verified role, otherwise none.
    """
    try:
        db = PrimitiveMongoData(CollectionEnum.ROLES)

        role_key = ConfigurationNameEnum.STUDENTY.value
        role_id: Optional[dict] = await db.find_one({role_key: {"$exists": True}})

        role: Optional[Role]
        if role_id:
            role = bot.guilds[0].get_role(role_id[role_key])
        else:
            role = None

        if not role:
            raise BrokenConfigurationError

        return role

    except (TypeError, BrokenConfigurationError):
        await handle_broken_config(bot)

    except ServerSelectionTimeoutError:
        await handle_db_connection(bot)


async def handle_db_connection(bot):
    title = "Error on Startup"
    cause = "Could not connect to database."
    solution = f"```\n" \
               f"1. Establish the connection to the database.\n" \
               f"2. Reload all modules." \
               f"```"
    get_mongo_child_logger(__name__).error(f"{cause} {error_msg}")
    await startup_error_reply(bot=bot, title=title, cause=cause, solution=solution)


async def handle_broken_config(bot):
    cause = "The bot chat configuration is broken."
    await startup_error_reply(bot=bot,
                              title="Invalid command Chat configuration.",
                              cause=cause,
                              solution=f"Please check {ConfigurationNameEnum.BOT_COMMAND_CHAT} "
                                       f"& {ConfigurationNameEnum.DEBUG_CHAT} and reload all modules.")
    get_discord_child_logger(__name__).error(f"{cause} {error_msg}")
