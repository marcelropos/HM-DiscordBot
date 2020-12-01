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


# noinspection PyPep8Naming
class TMP_CHANNELS:
    Channel_attr = namedtuple("Tempattr", ["text", "voice", "token", "invites"])
    Token_attr = namedtuple("Tokenattr", ["text", "voice"])
    Invite_attr = namedtuple("Invite", ["channel", "owner"])

    file_name = "TempChannelData"
    id = ServerIds.CUSTOM_CHANNELS
    tmp_channels = dict()
    token = dict()
    invite_dict = dict()
    bot = None

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
                    text_id, voice_id, token, invites = payload[x]
                    text_c = discord.Client.get_channel(self=cls.bot,
                                                        id=text_id)

                    voice_c = discord.Client.get_channel(self=cls.bot,
                                                         id=voice_id)

                    cls.tmp_channels[x] = cls.Channel_attr(text=text_c,
                                                           voice=voice_c,
                                                           token=token,
                                                           invites=invites)

                    cls.token[token] = cls.Token_attr(text=text_c,
                                                      voice=voice_c)
                    build_invites = dict()
                    for y in invites:
                        channel, owner = invites[y]
                        invite_attr = cls.Invite_attr(channel, owner)
                        build_invites[x] = invite_attr
                    cls.invite_dict.update(build_invites)

                except Exception:
                    pass
        except Exception as e:
            print(e)
            cls.tmp_channels = dict()

    @classmethod
    def update(cls, member, text, voice, token, invites=None):
        if not invites:
            invites = dict()
            invites.update(cls.invite_dict)
        # noinspection PyBroadException
        try:
            *_, existing_invites = cls.tmp_channels[member.id]
            invites.update(existing_invites)
        except Exception:
            pass
        channel_attr = cls.Channel_attr(text=text,
                                        voice=voice,
                                        token=token,
                                        invites=invites)

        token_attr = cls.Token_attr(text=text,
                                    voice=voice)

        channels_dict = dict()
        token_dict = dict()
        channels_dict[member.id] = channel_attr
        token_dict[token] = token_attr
        cls.tmp_channels.update(channels_dict)
        cls.token.update(token_dict)
        cls.save_data()

    @classmethod
    async def save_invite(cls, member, message):
        text, voice, token, invites = cls.tmp_channels[member.id]
        invite_attr = cls.Invite_attr(message.channel.id, member.id)
        cls.invite_dict[message.id] = invite_attr
        invites[message.id] = invite_attr
        cls.tmp_channels[member.id] = cls.Channel_attr(text=text,
                                                       voice=voice,
                                                       token=token,
                                                       invites=invites)
        cls.save_data()

    @classmethod
    async def delete_invite(cls, member_id, channel_id, message_id, ctx):
        # noinspection PyBroadException
        try:
            member = await ctx.guild.fetch_member(member_id)

            embed = invite_embed(member, "Abgelaufen")
            channel = await discord.Client.fetch_channel(cls.bot, channel_id)
            message = await channel.fetch_message(message_id)
            await message.edit(embed=embed)
            del cls.invite_dict[message_id]
            del cls.tmp_channels[member_id][3][message_id]
        except Exception:
            pass

    @classmethod
    async def get_ids(cls, member):
        if member.id in cls.tmp_channels:
            text, voice, token, invites = cls.tmp_channels[member.id]
            return text, voice, token, invites
        else:
            raise ChannelNotFoundError("Channel nicht gefunden.")

    @classmethod
    async def rem_channels(cls, ctx):
        # noinspection PyBroadException
        try:
            for x in cls.tmp_channels:
                text = cls.tmp_channels[x].text
                voice = cls.tmp_channels[x].voice
                token = cls.tmp_channels[x].token
                members = voice.members
                if len(members) == 0:
                    await cls.rem_channel(x, text, voice, token, ctx)
            cls.save_data()
        except Exception:
            pass

    @classmethod
    async def rem_channel(cls, user_id, text, voice, token, ctx):
        member = await ctx.guild.fetch_member(user_id)
        *_, invites = await TMP_CHANNELS.get_ids(member)
        loop = invites.copy()  # Avoid RuntimeError: dictionary changed size during iteration
        for x in loop:
            await cls.delete_invite(member.id, invites[x].channel, x, ctx)
        del cls.tmp_channels[user_id]
        del cls.token[token]
        await text.delete(reason="No longer used")
        await voice.delete(reason="No longer used")
        cls.save_data()

    # noinspection PyUnusedLocal,PyBroadException
    @classmethod
    def save_data(cls):
        tmp_channels = dict()
        for x in cls.tmp_channels:
            try:
                tmp_attrs = cls.tmp_channels[x]
                tmp_channels[x] = (tmp_attrs.text.id, tmp_attrs.voice.id, tmp_attrs.token, tmp_attrs.invites)

            except Exception as e:
                print(e)
                pass

        try:
            ReadWrite.write(tmp_channels, cls.file_name)
        except Exception:
            pass

    # noinspection PyDunderSlots,PyUnresolvedReferences,PyBroadException
    @staticmethod
    async def join(member, voice_c, text_c):
        overwrite = discord.PermissionOverwrite()
        overwrite.connect = True
        overwrite.read_messages = True
        await voice_c.set_permissions(member,
                                      overwrite=overwrite,
                                      reason="access by token")

        await text_c.set_permissions(member,
                                     overwrite=overwrite,
                                     reason="access by token")

        try:
            await member.move_to(voice_c, reason="want to join this Channel.")
        except Exception:
            pass


def invite_embed(member, token):
    embed = discord.Embed(title="Tempchannel Invite",
                          colour=discord.Colour(0x12d4ca),
                          description="")

    embed.add_field(name="Ersteller",
                    value=f"{member.nick}",
                    inline=False)

    embed.add_field(name="Token",
                    value="Die Reaktion mit 🔓 ist gleichbedeutend mit der Eingabe des Tokens.",
                    inline=False)

    embed.add_field(name="Token",
                    value=token,
                    inline=False)
    return embed


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
