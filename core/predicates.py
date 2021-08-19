from discord import TextChannel, Role
from discord.ext.commands import Context, check, has_role

from cogs.util.place_holder import Placeholder
from core.error.error_collection import NoBotChatError, NoMultipleGroupsError, NoRulesError


def bot_chat(channels: set[TextChannel]):
    def predicate(ctx: Context):
        if not channels:
            raise NoRulesError

        if {channel for channel in channels if channel.id == ctx.channel.id}:
            return True
        else:
            raise NoBotChatError(channels)

    return check(predicate)


def is_not_in_group(check_roles: set[Role]):
    def predicate(ctx: Context):
        if not check_roles:
            raise NoRulesError

        roles: set[Role] = set(ctx.author.roles)
        have_roles = roles.intersection(check_roles)
        if have_roles:
            raise NoMultipleGroupsError(have_roles.pop())
        return True

    return check(predicate)


def has_role_plus(item: Placeholder):
    def predicate(ctx):
        _predicate = has_role(item.item)
        if not item:
            raise NoRulesError
        return _predicate(ctx)

    return check(predicate)
