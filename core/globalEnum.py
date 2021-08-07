import logging
from enum import Enum


class CollectionEnum(Enum):
    ROLES = "roles"
    CHANNELS = "channels"
    MESSAGES = "messages"
    AUDIO_FILES = "audioFiles"
    EMOJIS = "emojis"
    KICK_GHOSTS = "kickGhosts"


class ConfigurationNameEnum(Enum):
    DELETE_AFTER = "deleteAfter"


class ConfigurationAttributeEnum(Enum):
    HOURS = "HOURS"


class DBKeyWrapperEnum(Enum):
    ID = "_id"
    OWNER = "owner"
    CHAT = "chat"
    VOICE = "voice"
    TOKEN = "token"
    DELETE_AT = "deleteAt"
    ROLE = "role"


class LoggingLevel(Enum):
    CRITICAL = logging.CRITICAL
    ERROR = logging.ERROR
    WARNING = logging.WARNING
    INFO = logging.INFO
    DEBUG = logging.DEBUG
