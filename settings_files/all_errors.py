# noinspection PyUnresolvedReferences
from discord import Forbidden, DiscordServerError, LoginFailure, HTTPException, NotFound, NotificationLevel, \
    NoMoreItems, ClientException, ConnectionClosed
from discord.ext.commands.errors import *


class NoCommandError(CommandNotFound):
    pass


class UserError(CommandError):
    pass


class WrongChatError(UserError):
    pass


class ModuleError(CommandError):
    pass


class ChannelNotFoundError(UserError):
    pass


class RoleNotFoundError(UserError):
    pass


class MultipleGroupsError(UserError):
    pass


class RequestError(ModuleError):
    pass


class PrivateChannelsAlreadyExistsError(UserError):
    pass


class TempChannelNotFound(UserError):
    pass


class CouldNotSendMessage(UserError):
    pass


class ManPageNotFound(Exception):
    pass


class IncorrectConfigurationException(Exception):
    pass


class IncorrectBotConfigurationException(IncorrectConfigurationException):
    pass


class IncorrectServerConfigurationException(IncorrectConfigurationException):
    pass


class ModeratedCommandError(UserError):
    pass


class IncorrectUserInputError(UserError):
    pass


def global_only_handled_errors() -> tuple:
    result = (
        CommandNotFound,
        MissingRequiredArgument,
        BadArgument,
        MissingPermissions,
        WrongChatError,
        NoPrivateMessage,
        IncorrectConfigurationException,
        MissingRole,
    )
    return result


def local_only_handled_errors() -> tuple:
    result = (
        UserError,
        CheckFailure,
        RoleNotFoundError,
        MultipleGroupsError
    )
    return result
