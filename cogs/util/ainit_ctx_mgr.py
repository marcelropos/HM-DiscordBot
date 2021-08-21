from discord import TextChannel
from discord.ext.commands import Bot
from discord.ext.tasks import Loop
from pymongo.errors import ServerSelectionTimeoutError

from cogs.util.assign_variables import assign_accepted_chats, assign_role
from cogs.util.placeholder import Placeholder
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

    def __init__(self,
                 bot: Bot,
                 loop: Loop,
                 need_init: bool,
                 bot_channels: set[TextChannel] = None,
                 verified: Placeholder = Placeholder(),
                 moderator: Placeholder = Placeholder()):
        self.bot = bot
        self.loop = loop
        self.need_init = need_init
        self.bot_channels = bot_channels if bot_channels is not None else set()
        self.verified = verified
        self.moderator = moderator

    async def __aenter__(self):

        try:
            await assign_accepted_chats(self.bot, self.bot_channels)
            self.verified.item = await assign_role(self.bot, ConfigurationNameEnum.STUDENTY)
            self.moderator.item = await assign_role(self.bot, ConfigurationNameEnum.MODERATOR_ROLE)

        except (TypeError, BrokenConfigurationError):
            await handle_broken_config(self.bot)

        except ServerSelectionTimeoutError:
            await handle_db_connection(self.bot)

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
