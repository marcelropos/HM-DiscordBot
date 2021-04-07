# noinspection PyUnresolvedReferences
from discord import Forbidden, DiscordServerError, LoginFailure
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
