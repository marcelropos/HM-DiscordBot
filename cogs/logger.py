import logging
from typing import Union

from discord import Member, User, Embed
from discord.ext.commands import Cog, Bot, command, bot_has_guild_permissions, Context

from cogs.bot_status import listener
from core.global_enum import LoggingLevel, CollectionEnum, LoggerEnum
from core.logger import get_discord_child_logger, loggerInstance
from mongo.primitive_mongo_data import PrimitiveMongoData

logger = get_discord_child_logger("logger")

pretty_logger_help = "You can assign one of these verbose levels:\n{}\n to one of these logger: \n{}"


class Logger(Cog):
    """
    Modifies the main logger.
    """

    def __init__(self, bot: Bot):
        self.bot = bot
        self.db: PrimitiveMongoData = PrimitiveMongoData(CollectionEnum.LOGGER)

    @listener()
    async def on_ready(self):
        """
        Assigns to each logger the stored level or sets a default if not given.
        """
        logger.info("Load and assign saved level to the logger.")
        for _logger in LoggerEnum:
            _logger: LoggerEnum
            result = await self.db.find_one({_logger.value: {"$exists": True}})
            if result:
                level = result[_logger.value]
                self.set_level(LoggingLevel(level), _logger)
                logger.info(f"The level of {_logger.value} has been loaded and assigned.")
            else:
                default = LoggingLevel.INFO
                self.set_level(default, _logger)
                await self.db.insert_one({_logger.value: default.value})
                logger.info(f"No default for {_logger.value} has been found, default is now set to {default.name}")
        logger.info("All levels has been applied.")

    @command(brief="Modifies a main logger.",
             help=pretty_logger_help.format(
                 [e.name for e in LoggingLevel],
                 [e.value for e in LoggerEnum]))
    @bot_has_guild_permissions(administrator=True)
    async def logger(self, ctx: Context, _logger: LoggerEnum, level: str):
        """
        Assigns the verbose level for a given logger

        Args:
            ctx: The command context provided by the discord.py wrapper.

            _logger: The logger which has to be modified.

            level: The name of the applying level.

        Replies:
            A success message.
        """
        level = level.lower()
        level_enum = {e.name.lower(): e for e in LoggingLevel}
        _level = level_enum[level]
        member: Union[Member, User] = ctx.author
        logger.info(f'User="{member.name}#{member.discriminator}({member.id})", Command="{ctx.message.content}"')
        await self.db.update_one({_logger.value: {"$exists": True}}, {_logger.value: _level})
        self.set_level(_level, _logger)
        embed = Embed(title="Logging",
                      description=f"The `{_logger.value}` logger is now on `{level.upper()}` level.")
        await ctx.reply(embed=embed)

    @staticmethod
    def set_level(level: LoggingLevel, _logger: LoggerEnum):
        """
        Sets the level and logs the change.
        """
        loggerInstance.loggerLogger.warning(f"{_logger.value} Logger set to new logger level :" + level.name)
        logging.getLogger(_logger.value).setLevel(level.value)


def setup(bot: Bot):
    bot.add_cog(Logger(bot))
