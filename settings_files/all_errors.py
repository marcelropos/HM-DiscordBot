from discord.ext import commands
# noinspection PyUnresolvedReferences
from discord.ext.commands.errors import *
# noinspection PyUnresolvedReferences
from discord.errors import *


class NoCommandError(commands.CommandNotFound):
    pass


class UserError(commands.CommandError):
    pass


class WrongChatError(UserError):
    pass


class ModuleError(commands.CommandError):
    pass


class ChannelNotFoundError(UserError):
    pass


class RoleNotFoundError(UserError):
    pass


class MultipleGroupsError(UserError):
    pass


class MultipleCoursesError(UserError):
    pass


class RequestError(ModuleError):
    pass


class PrivateChannelsAlreadyExistsError(UserError):
    pass


class TempChannelNotFound(UserError):
    pass


class CouldNotSendMessage(UserError):
    pass
