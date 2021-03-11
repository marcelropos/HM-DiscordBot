import discord
from settings_files._global import ServerRoles, ServerIds
from discord.ext.commands import Context
from discord.member import Member
from discord.role import Role
import pyotp
from settings_files.all_errors import *
import re


def mods_or_owner():
    # noinspection PyUnusedLocal
    def predicate(ctx):
        return commands.check_any(commands.is_owner(), commands.has_role(ServerIds.MODERATOR))

    return commands.check(predicate)


def has_not_roles(check_roles: set):
    def predicate(ctx: Context):
        for x in ctx.author.roles:
            if x.name in check_roles:
                return False
        return True
    return commands.check(predicate)


def has_not_role(check_role):
    def predicate(ctx: Context):
        for x in ctx.author.roles:
            if x.id == check_role:
                return False
        return True
    return commands.check(predicate)


def is_in_group():
    # noinspection PyUnusedLocal
    def predicate(ctx):
        return commands.has_any_role(ServerRoles.ALL_GROUPS)

    return commands.check(predicate)


def mk_token():
    secret = pyotp.random_base32()
    totp = pyotp.TOTP(secret)
    otp = totp.now()
    return str(otp)


class DictSort:

    @staticmethod
    def sort_by_key(payload: dict, reverse=False):
        is_sorted = sorted(payload.items(), key=lambda t: t[0], reverse=reverse)
        return DictSort.make_dict(is_sorted)

    @staticmethod
    def sort_by_value(payload: dict, reverse=False):
        is_sorted = sorted(payload.items(), key=lambda t: t[1], reverse=reverse)
        return DictSort.make_dict(is_sorted)

    @staticmethod
    def make_dict(payload: list):
        result = dict()
        for x in payload:
            key, val = x
            result[key] = val
        return result


async def accepted_channels(bot, ctx):
    channels = {ServerIds.BOT_COMMANDS_CHANNEL,
                ServerIds.DEBUG_CHAT}
    try:
        channels.add(ctx.author.dm_channel.id)
    except AttributeError:
        pass

    for x in ctx.guild.channels:
        try:
            if ctx.channel.id == ServerIds.CUSTOM_CHANNELS:
                channels.add(x.category.id)
        except AttributeError:
            pass

    if ctx.channel.id not in channels:
        channel = discord.Client.get_channel(self=bot,
                                             id=ServerIds.BOT_COMMANDS_CHANNEL)
        await channel.send(f"<@!{ctx.author.id}>\n Schreibe mir doch bitte hier nochmal oder ggf. Privat.")
        raise WrongChatError("Falscher Chat")


def extract_id(content):
    matches = re.finditer(r"[0-9]+", content)
    user_id = None
    for match in matches:
        start, end = match.span()
        user_id = content[start:end]
    return user_id


def print_help(x):
    print(help(x))
