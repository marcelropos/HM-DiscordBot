import logging
from enum import Enum

import discord


class MagicNumbers(Enum):
    DISCORD_FIELD_LENGTH_LIMIT = 1024


class CollectionEnum(Enum):
    ROLES = "roles"
    CHANNELS = "channels"
    CATEGORIES = "categories"
    MESSAGES = "messages"
    AUDIO_FILES = "audioFiles"
    EMOJIS = "emojis"
    KICK_GHOSTS = "kickGhosts"
    LOGGER = "logger"
    COOLDOWN = "cooldown"
    GROUP_SUBJECT_RELATION = "groupSubjectRelation"
    TEMP_CHANNELS = "tempChannels"
    JOIN_TEMP_CHANNELS = "joinTempChannels"
    TEMP_CHANNELS_CONFIGURATION = "channelConfiguration"


class ConfigurationNameEnum(Enum):
    MODERATOR_ROLE = "moderator"
    MOD_CHAT = "modChat"
    STUDENTY = "studenty"
    FRIEND = "friend"
    TMP_STUDENTY = "tmp_studenty"
    NSFW = "nsfw"
    NEWSLETTER = "newsletter"
    STUDY_SEPARATOR_ROLE = "studySeparator"
    SUBJECTS_SEPARATOR_ROLE = "subjectsSeparator"
    GROUP_CATEGORY = "groupCategory"
    SUBJECTS_CATEGORY = "subjectsCategory"
    NERD_VOICE_CHANNEL = "NerdVoiceChannel"
    ENABLED = "enabled"
    DEADLINE = "deadline"
    WARNING = "warning"
    SAFE_ROLES_LIST = "safeRoles"
    DEBUG_CHAT = "debug"
    BOT_COMMAND_CHAT = "botChat"
    HELP_CHAT = "help"
    TIME = "time"
    DEFAULT_KEEP_TIME = "defaultTime"
    DEFAULT_STUDY_NAME = "studyDefaultName"
    DEFAULT_GAMING_NAME = "gamingDefaultName"


class DBKeyWrapperEnum(Enum):
    ID = "_id"
    OWNER = "owner"
    CHAT = "chat"
    VOICE = "voice"
    DEFAULT_CHANNEL_NAME = "defaultChannelName"
    TOKEN = "token"
    DELETE_AT = "deleteAt"
    ROLE = "role"
    GROUP = "group"
    SUBJECT = "subject"
    DEFAULT = "default"
    MESSAGES = "messages"
    PERSIST = "persist"


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


colors: dict[str, discord.Color] = {
    "IF": discord.Color(0xd79921),
    "IB": discord.Color.green(),
    "DC": discord.Color.blue()
}


def no_intersection():
    """
    Checks if CollectionEnum and SubjectsOrGroupsEnum does not contain the same collection.
    """
    if {e.value for e in CollectionEnum}.intersection({e.value for e in SubjectsOrGroupsEnum}):
        raise KeyError("The collection value must be unique.")


no_intersection()
