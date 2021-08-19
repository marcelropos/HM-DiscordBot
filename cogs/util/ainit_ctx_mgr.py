from discord.ext.commands import Bot
from discord.ext.tasks import Loop
from pymongo.errors import ServerSelectionTimeoutError

from core.error.error_collection import BrokenConfigurationError
from core.error.error_reply import startup_error_reply
from core.globalEnum import ConfigurationNameEnum
from core.logger import get_mongo_child_logger, get_discord_child_logger

error_msg = "Due to the previous reason, all commands limited to chats are out of function!"


class AinitManager:
    """
    Manages the asynchronous start of a module.

    This manager is used if a task is to be run once after (re)loading a module and then terminates the task.
    Defined errors are handled.
    """

    def __init__(self, bot: Bot, loop: Loop, need_init: bool):
        self.bot = bot
        self.loop = loop
        self.need_init = need_init

    async def __aenter__(self):
        return self.need_init

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.need_init = False
        self.loop.stop()
        result = None

        if exc_type in {TypeError, BrokenConfigurationError}:
            await handle_broken_config(self.bot)
            result = exc_type
        elif exc_type in {ServerSelectionTimeoutError}:
            await handle_db_connection(self.bot)
            result = exc_type

        return result


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
