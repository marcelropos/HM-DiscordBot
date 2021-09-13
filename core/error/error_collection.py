from typing import Union

from discord import TextChannel, Role, Member, User
from discord.ext.commands import CommandError, Context

from core.global_enum import CollectionEnum, SubjectsOrGroupsEnum


class ManPageNotFound(Exception):
    pass


class CouldNotEditEntryError(Exception):
    def __init__(self, collection: CollectionEnum, key: str, value: str = "<value>"):
        self.collection = collection
        self.key = key
        self.value = value


class BrokenConfigurationError(Exception):
    def __init__(self, collection: str, keys: Union[str, list[str]]):
        self.collection: str = collection
        if keys is str:
            self.keys: list[str] = [keys]
        else:
            self.keys: list[str] = keys

    def key_representation(self) -> str:
        output: str = str(self.keys).replace("'", "`")
        if "`" not in output:
            output = "`" + output + "`"
        return output


class NoBotChatError(CommandError):
    def __init__(self, channels: set[TextChannel]):
        self.channels = channels


class NoMultipleGroupsError(CommandError):
    def __init__(self, role: Role):
        self.role = role


class FailedToGrantRoleError(CommandError):
    def __init__(self, role: Role, member: Union[Member, User]):
        self.role = role
        self.member = member


class MayNotUseCommandError(CommandError):
    pass


class NoRulesError(CommandError):
    pass


class YouAlreadyHaveThisRoleError(CommandError):
    pass


class GroupOrSubjectNotFoundError(CommandError):
    def __init__(self, group: str, _type: SubjectsOrGroupsEnum):
        self.group = group
        self.type = _type


class LinkingNotFoundError(CommandError):
    def __init__(self, ctx: Context):
        self.prefix = ctx.bot.command_prefix


class HasNoHandlerException(Exception):
    pass


class DatabaseIllegalState(Exception):
    pass


class WrongChatForCommand(CommandError):
    pass


class CantAssignToSubject(CommandError):
    pass


class CantRemoveSubject(CommandError):
    pass


class NoStudyGroupAssigned(CommandError):
    pass


class CouldNotFindToken(CommandError):
    pass


class CanOnlyHaveOneChannel(CommandError):
    pass
