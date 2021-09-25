from typing import Union

from discord import TextChannel, Role
from discord.ext.commands import Context, check, NoPrivateMessage, BotMissingRole

from cogs.util.placeholder import Placeholder
from core.error.error_collection import NoBotChatError, NoMultipleGroupsError, NoRulesError


def bot_chat(channels: set[TextChannel]):
    def predicate(ctx: Context):
        if ctx.guild is None:
            raise NoPrivateMessage()
        if not channels:
            raise NoRulesError

        if {channel for channel in channels if channel.id == ctx.channel.id}:
            return True
        else:
            raise NoBotChatError(channels)

    return check(predicate)


def is_not_in_group(check_roles: set[Role]):
    def predicate(ctx: Context):
        if ctx.guild is None:
            raise NoPrivateMessage()
        if not check_roles:
            raise NoRulesError

        roles: set[Role] = set(ctx.author.roles)
        have_roles = roles.intersection(check_roles)
        if have_roles:
            raise NoMultipleGroupsError(have_roles.pop())
        return True

    return check(predicate)


def has_role_plus(item: Union[Placeholder, set[Role]]):
    def predicate(ctx):
        if ctx.guild is None:
            raise NoPrivateMessage()

        if not item:
            raise NoRulesError

        if isinstance(item, Placeholder):
            _item = {item.item}
        else:
            _item = item

        _item: set[Role]

        if {_ for _ in set(ctx.author.roles) if _ in _item}:
            return True
        else:
            raise BotMissingRole([role.name for role in _item])

    return check(predicate)
