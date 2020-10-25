from discord.ext import commands
# noinspection PyUnresolvedReferences
import discord
# noinspection PyUnresolvedReferences
from settings import ServerRoles, ServerIds, ReadWrite
import pyotp


class UserError(commands.CommandError):
    pass


class ModuleError(commands.CommandError):
    pass


def mods_or_owner():
    # noinspection PyUnusedLocal
    def predicate(ctx):
        return commands.check_any(commands.is_owner(), commands.has_role(ServerRoles.MODERATOR_ROLE_NAME))

    return commands.check(predicate)


def is_study():
    # noinspection PyUnusedLocal
    def predicate(ctx):
        return commands.has_any_role(ServerRoles.INFORMATIK, ServerRoles.WIRTSCHAFTSINFORMATIK,
                                     ServerRoles.DATA_SCIENCE)

    return commands.check(predicate)


def is_in_group():
    # noinspection PyUnusedLocal
    def predicate(ctx):
        return commands.has_any_role(ServerRoles.IF1A, ServerRoles.IF1B, ServerRoles.IB1A, ServerRoles.IB1B,
                                     ServerRoles.IB1C, ServerRoles.IB1D)

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


# noinspection PyPep8Naming
class TMP_CHANNELS:
    file_name = "TempChannelData"
    id = ServerIds.CUSTOM_CHANNELS
    tmp_channels = dict()
    token = dict()
    bot = None

    @classmethod
    def update(cls, member, text, voice, token):
        channels_dict = dict()
        token_dict = dict()
        channels_dict[member.id] = (text, voice, token)
        token_dict[token] = (text, voice)
        cls.tmp_channels.update(channels_dict)
        cls.token.update(token_dict)
        cls.save_data()

    # noinspection PyBroadException
    @classmethod
    def __init__(cls, bot=None):

        if not cls.bot:
            cls.bot = bot
        else:
            # noinspection PyUnusedLocal
            bot = cls.bot

        try:
            payload = ReadWrite.read(cls.file_name)
            for x in payload:
                try:
                    text_id, voice_id, token = payload[x]
                    text_c = discord.Client.get_channel(self=cls.bot, id=text_id)
                    voice_c = discord.Client.get_channel(self=cls.bot, id=voice_id)
                    cls.tmp_channels[x] = (text_c, voice_c, token)
                    cls.token[token] = (text_c, voice_c)
                except Exception:
                    pass
        except Exception as e:
            print(e)
            cls.tmp_channels = dict()

    @classmethod
    async def rem_channel(cls):
        for x in cls.tmp_channels:
            text, voice, token = cls.tmp_channels[x]
            members = voice.members
            if len(members) == 0:
                del cls.tmp_channels[x]
                del cls.token[token]
                await text.delete()
                await voice.delete()
        cls.save_data()

    @classmethod
    def save_data(cls):
        # noinspection PyUnusedLocal,PyBroadException
        tmp_channels = dict()
        for x in cls.tmp_channels:
            text, voice, token = cls.tmp_channels[x]
            tmp_channels[x] = (text.id, voice.id, token)
        try:
            ReadWrite.write(tmp_channels, cls.file_name)
        except Exception as e:
            print(e)
            pass
