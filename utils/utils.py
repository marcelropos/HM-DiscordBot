from discord.ext import commands
# noinspection PyUnresolvedReferences
import discord
# noinspection PyUnresolvedReferences
from settings import ServerRoles, ServerIds, ReadWrite, EmojiIds
# noinspection PyUnresolvedReferences

from collections import namedtuple
import pyotp
from settings_files.all_errors import *


def mods_or_owner():
    # noinspection PyUnusedLocal
    def predicate(ctx):
        return commands.check_any(commands.is_owner(), commands.has_role(ServerIds.MODERATOR))

    return commands.check(predicate)


def is_study():
    # noinspection PyUnusedLocal
    def predicate(ctx):
        return commands.has_any_role(ServerIds.INFORMATIK, ServerIds.WIRTSCHAFTSINFORMATIK,
                                     ServerIds.DATA_SCIENCE)

    return commands.check(predicate)


def is_in_group():
    # noinspection PyUnusedLocal
    def predicate(ctx):
        return commands.has_any_role(ServerIds.IF1A, ServerIds.IF1B, ServerIds.IB1A, ServerIds.IB1B,
                                     ServerIds.IB1C)

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
