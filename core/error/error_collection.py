from discord import TextChannel, Role
from discord.ext.commands import CommandError

from core.globalEnum import CollectionEnum


class ManPageNotFound(Exception):
    pass


class CouldNotEditEntryError(Exception):
    def __init__(self, collection: CollectionEnum, key: str, value: str = "<value>"):
        self.collection = collection
        self.key = key
        self.value = value


class NoBotChatError(CommandError):
    def __init__(self, channels: set[TextChannel]):
        self.channels = channels


class NoMultipleGroupsError(CommandError):
    def __init__(self, role: Role):
        self.role = role


class MayNotUseCommandError(CommandError):
    pass


class NoRulesError(CommandError):
    pass
