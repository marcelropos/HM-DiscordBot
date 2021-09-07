import logging
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

from core.global_enum import LoggingLevel


class Logger:
    """Logger class containing the master Logger

    Do not use this Class, this Class should only be used from inside this file.
    """

    def __init__(self):
        # Formatter for all Loggers
        formatter = logging.Formatter("%(asctime)s %(name)s/%(levelname)s %(funcName)s %(lineno)d: %(message)s")

        # create log folder if it doesn't exist
        log_folder = "./data/logs"
        Path(log_folder).mkdir(parents=True, exist_ok=True)

        # File Handler to write all logs in the same File
        file_handler = TimedRotatingFileHandler(
            filename=log_folder + '/discord.log',
            encoding='utf-8',
            when='midnight',
            utc=True)
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.DEBUG)

        # Stream Handler to write all logs in the Terminal
        terminal_stream = logging.StreamHandler()
        terminal_stream.setFormatter(formatter)
        terminal_stream.setLevel(logging.DEBUG)

        # The main logger for anything related to Discord
        self.discordLogger = logging.getLogger("discord")
        self.discordLogger.setLevel(logging.INFO)
        self.discordLogger.addHandler(file_handler)
        self.discordLogger.addHandler(terminal_stream)

        # The main logger for anything related to Mongo
        self.mongoLogger = logging.getLogger("mongo")
        self.mongoLogger.setLevel(logging.DEBUG)
        self.mongoLogger.addHandler(file_handler)
        self.mongoLogger.addHandler(terminal_stream)

        # The main logger for anything related to this Logger
        # Yes we are keeping this meme like name
        self.loggerLogger = logging.getLogger("logger")
        self.loggerLogger.setLevel(logging.DEBUG)
        self.loggerLogger.addHandler(file_handler)
        self.loggerLogger.addHandler(terminal_stream)

        self.loggerLogger.info("Initialized all main Loggers")


loggerInstance = Logger()


def get_discord_child_logger(name: str) -> logging.Logger:
    """
    Generates a Child Logger from the Discord Logger

    Args:
        name (str): The name of the child Logger

    Returns:
        The child logger with the given name
    """
    loggerInstance.loggerLogger.debug("Created new child Logger for the Discord Logger")
    return loggerInstance.discordLogger.getChild(name)


def get_mongo_child_logger(name: str) -> logging.Logger:
    """
    Generates a Child Logger from the MongoDB Logger

    Args:
        name: The name of the child Logger

    Returns:
        The child logger with the given name
    """
    loggerInstance.loggerLogger.debug("Created new child Logger for the Mongo Logger")
    return loggerInstance.mongoLogger.getChild(name)


def set_discord_log_level(level: LoggingLevel):
    """
    Set the verbose logging level of the Discord Logger

    Args:
        level: The new Level of this logger
    """
    loggerInstance.loggerLogger.warning("Discord Logger set to new verbose level :" + level.name)
    loggerInstance.discordLogger.setLevel(level.value)


def set_mongo_log_level(level: LoggingLevel):
    """
    Set the verbose logging level of the Mongo DB Logger

    Args:
        level: The new Level of this logger
    """
    loggerInstance.loggerLogger.warning("Mongo Logger set to new verbose level :" + level.name)
    loggerInstance.mongoLogger.setLevel(level.value)


def set_logger_log_level(level: LoggingLevel):
    """
    Set the verbose logging level of the Logger Logger

    ( ๑‾̀◡‾́)σ »

    Args:
        level: The new Level of this logger
    """
    loggerInstance.loggerLogger.warning("Logger Logger set to new logger level :" + level.name)  # ( ๑‾̀◡‾́)σ »
    loggerInstance.loggerLogger.setLevel(level.value)
