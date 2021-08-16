import logging
from enum import Enum


class CollectionEnum(Enum):
    ROLES = "roles"
    CHANNELS = "channels"
    MESSAGES = "messages"
    AUDIO_FILES = "audioFiles"
    EMOJIS = "emojis"
    KICK_GHOSTS = "kickGhosts"
    LOGGER = "logger"


class ConfigurationNameEnum(Enum):
    ADMIN_ROLE = "admin"
    MODERATOR_ROLE = "moderator"
    STUDY_SEPARATOR_ROLE = "studySeparator"
    SUBJECTS_SEPARATOR_ROLE = "subjectsSeparator"
    ENABLED = "enabled"
    DEADLINE = "deadline"
    WARNING = "warning"
    SAFE_ROLES_LIST = "safeRoles"
    DEBUG_CHAT = "debug"
    BOT_COMMAND_CHAT = "botChat"
    HELP_CHAT = "help"
    ROLE_NOT_FOUND_MESSAGE = "roleNotFound"


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


class LoggerEnum(Enum):
    DISCORD = "discord"
    MONGO = "mongo"
    LOGGER_LOGGER = "logger"


class SubjectsOrGroupsEnum(Enum):
    SUBJECT = "subject"
    GROUP = "group"


def no_intersection():
    """
    Checks if CollectionEnum and SubjectsOrGroupsEnum does not contain the same collection.
    """
    if {e.value for e in CollectionEnum}.intersection({e.value for e in SubjectsOrGroupsEnum}):
        raise KeyError("The collection value must be unique.")


no_intersection()
