import logging
import string
import xml.etree.ElementTree as ElementTree
from asyncio import Lock
from typing import Union

import discord
from aiosqlite import Cursor, Connection
from discord import Guild, Role, User
from discord.channel import TextChannel, VoiceChannel
from discord.ext import commands
from discord.ext.commands import Bot, Context, Cog
from discord.member import Member

from settings_files.all_errors import *
from utils.embed_generator import EmbedGenerator
from utils.tempchannels.database import TempChannelDB
from utils.tempchannels.maintainchannels import MaintainChannel
from utils.tempchannels.token import Token
from utils.utils import ServerIds, mk_token, accepted_channels

logger = logging.getLogger("discord")


class Database:
    _lock = Lock()
    _database = None

    @classmethod
    async def make(cls):
        if not isinstance(cls._database, TempChannelDB):
            cls._database = await TempChannelDB().make()

    @classmethod
    def db(cls) -> Connection:
        if isinstance(cls._database.db, Connection):
            return cls._database.db
        else:
            raise TypeError("Database is probably not initialized.")

    @classmethod
    async def __aenter__(cls):
        await cls._lock.acquire()
        return cls.db()

    @classmethod
    async def __aexit__(cls, exc_type, exc_val, exc_tb):
        cls._lock.release()


class Activities(Cog):

    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: Union[Member, User], *_):
        if member.bot:
            return
        await Database().make()
        async with Database() as db:
            db: Connection
            await MaintainChannel.rem_channels(member, self.bot, db)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        try:
            if payload.member.bot:
                return
        except AttributeError:
            pass

        await Database().make()
        # noinspection PyBroadException
        try:
            message_id = payload.message_id
            member_id = payload.user_id
            async with Database() as db:
                cursor: Cursor = await db.execute(
                    f"""SELECT token FROM Invites where message_id=?""",
                    (message_id,))
                token = await cursor.fetchone()
            if token:
                async with Database() as db:
                    cursor: Cursor = await db.execute(
                        f"""SELECT textChannel, voiceChannel FROM TempChannels where token=?""",
                        (token[0],))
                    text_channel_id, voice_channel_id = await cursor.fetchone()
                text_channel: TextChannel = await self.bot.fetch_channel(text_channel_id)
                voice_channel: VoiceChannel = await self.bot.fetch_channel(voice_channel_id)
                guild: Guild = text_channel.guild
                member = await guild.fetch_member(member_id)
                await MaintainChannel.join(member, voice_channel, text_channel)
        except Exception:
            logger.exception("Activity error")


class TempChannels(Cog):
    """Create, edit or delete your temporary channel."""

    def __init__(self, bot: Bot):
        self.bot = bot
        self.config = ElementTree.parse("./data/config.xml").getroot()
        self.allowed_chars = self.config.find("global").find("allowedChars").text

    @commands.group(pass_context=True,
                    aliases=["temp", "tempc"],
                    brief="Create, edit or delete your temporary channel.",
                    help="Command group")
    @commands.has_role(ServerIds.HM)
    @commands.guild_only()
    async def tmpc(self, ctx: Context):
        await Database.make()
        if ctx.invoked_subcommand is None:
            raise ModuleError()

    # noinspection SqlNoDataSourceInspection,SqlDialectInspection
    @tmpc.command(pass_context=True,
                  brief="Create a channel.",
                  help="This channel will be deleted after you leave it.",
                  aliases=["make"])
    async def mk(self, ctx: Context, *, name: str):

        illegal_symbols = {x for x in name} \
            .difference({x for x in
                         string.ascii_uppercase + string.ascii_lowercase + string.digits + "-_" + self.allowed_chars})

        if len(illegal_symbols):
            raise UserError(
                f"The name may only contain alphanumeric characters, as well as the characters '-' and '_'. "
            )
        if len(name) > 100:
            raise UserError("The length of the channel name may only between 1 and 100 characters")

        await accepted_channels(self.bot, ctx)
        member: Union[Member, User] = ctx.author
        async with Database() as db:
            cursor: Cursor = await db.execute(
                f"""SELECT * FROM TempChannels WHERE discordUser=?""",
                (str(ctx.author.id),))
            if await cursor.fetchone():
                raise PrivateChannelsAlreadyExistsError()

            category = ctx.guild.get_channel(ServerIds.CUSTOM_CHANNELS)

            voice_c: VoiceChannel = await ctx.guild.create_voice_channel(name,
                                                                         category=category,
                                                                         reason=f"request by {member.display_name}")

            text_c: TextChannel = await ctx.guild.create_text_channel(name,
                                                                      category=category,
                                                                      reason=f"request by {member.display_name}",
                                                                      topic=f"Created by: {member.display_name}")
            token = mk_token()

            overwrite = discord.PermissionOverwrite(mute_members=True,
                                                    deafen_members=True,
                                                    move_members=True,
                                                    connect=True,
                                                    read_messages=True)

            await voice_c.set_permissions(member, overwrite=overwrite, reason="owner")
            await text_c.set_permissions(member, overwrite=overwrite, reason="owner")

            for role in member.roles:
                role: Role
                if role.id == ServerIds.MODERATOR:
                    await voice_c.set_permissions(role,
                                                  overwrite=None,
                                                  reason="No mod active")
                    await text_c.set_permissions(role,
                                                 overwrite=None,
                                                 reason="No mod active")
                    break

            # noinspection PyBroadException
            try:
                await member.move_to(voice_c, reason="created this channel.")
            except Forbidden as error:
                raise error
            except HTTPException:
                pass

            # noinspection PyBroadException
            try:
                await db.execute(f"INSERT INTO TempChannels("
                                 f"discordUser, textChannel, voiceChannel, token) VALUES"
                                 f"(?,?,?,?)",
                                 (ctx.author.id, text_c.id, voice_c.id, token))

            except Exception:
                # noinspection PyBroadException
                try:
                    await db.execute(f"INSERT INTO TempChannels("
                                     f"discordUser, textChannel, voiceChannel, token) VALUES"
                                     f"(?,?,?,?)",
                                     (ctx.author.id, text_c.id, voice_c.id, token))
                except Exception:
                    await voice_c.delete()
                    await text_c.delete()
                    logger.exception("Database Error:")
            else:
                logger.debug(f"Created temporary channels: "
                             f"{ctx.author}-{ctx.author.id} "
                             f"owns text-{text_c.id},voice-{voice_c.id} with token-{token}")

            # noinspection PyBroadException
            try:
                gen = EmbedGenerator("tmpc-func")
                embed = gen.generate()
                embed.add_field(name="Invite fellow students",
                                value=f"With ``!tmpc join {token}`` "
                                      f"your fellow students can also join the (voice) chat.",
                                inline=False)

                await text_c.send(content=f"<@!{ctx.author.id}>",
                                  embed=embed)
            except Forbidden as error:
                raise error
            except Exception:
                logger.exception("Can't send Message: ")

    # noinspection SqlNoDataSourceInspection
    @tmpc.command(pass_context=True,
                  brief="Join a temporary channel.",
                  help="As long as the token is valid, you can use it to join the channel.")
    async def join(self, ctx: Context, token):
        try:
            await ctx.message.delete()
        except Forbidden:
            pass
        await accepted_channels(self.bot, ctx)

        try:
            async with Database() as db:
                cursor: Cursor = await db.execute(
                    """SELECT textChannel, voiceChannel FROM TempChannels WHERE token=?""",
                    (token,))
                text_channel_id, voice_channel_id = await cursor.fetchone()
        except TypeError:
            raise TempChannelNotFound()
        else:
            text_channel = await self.bot.fetch_channel(text_channel_id)
            voice_channel = await self.bot.fetch_channel(voice_channel_id)
            await MaintainChannel.join(ctx.author, voice_channel, text_channel)

    # noinspection SqlNoDataSourceInspection
    @tmpc.command(pass_context=True,
                  brief="Manage invitations",
                  help="""
                            modes:
                            - gen: generates new invitation token.
                            - place: places an invitation.
                            - send <@user>: sends an invitation to a user.""")
    async def token(self, ctx: Context, mode: str, *, user=None):
        try:
            async with Database() as db:
                cursor: Cursor = await db.execute(
                    f"""SELECT * FROM TempChannels WHERE discordUser=?""",
                    (str(ctx.author.id),))
                member, text_channel_id, voice_channel_id, token = await cursor.fetchone()
        except TypeError:
            raise TempChannelNotFound()

        async with Database() as db:
            if mode.startswith("gen"):
                await MaintainChannel.update(ctx, mk_token(), self.bot, db)
            elif mode.startswith("place"):
                await Token.token_place(ctx, token, db)
            elif mode.startswith("send") and user:
                await Token.token_send(self.bot, ctx, token, user, db)

    @tmpc.command(pass_context=True,
                  brief="Disable moderation",
                  help="Removes the access rights of the Moderator role to the channels.")
    @commands.has_role(ServerIds.MODERATOR)
    async def nomod(self, ctx):
        await accepted_channels(self.bot, ctx)
        try:
            async with Database() as db:
                cursor: Cursor = await db.execute(
                    """SELECT textChannel, voiceChannel FROM TempChannels WHERE discordUser=?""",
                    (str(ctx.author.id),))
                text_channel_id, voice_channel_id = await cursor.fetchone()
            role = discord.utils.get(ctx.guild.roles, id=ServerIds.MODERATOR)
            voice_channel = await self.bot.fetch_channel(voice_channel_id)
            text_channel = await self.bot.fetch_channel(text_channel_id)
            await voice_channel.set_permissions(role,
                                                overwrite=None,
                                                reason="No mod active")

            await text_channel.set_permissions(role,
                                               overwrite=None,
                                               reason="No mod active")
        except AttributeError:
            raise TempChannelNotFound()

    # noinspection SqlResolve
    @tmpc.command(pass_context=True,
                  brief="Delete the channel.",
                  help="With this command you can delete a channel manually.")
    async def rem(self, ctx: Context):
        # noinspection PyBroadException
        try:
            async with Database() as db:
                db: Connection
                cursor: Cursor = await db.execute(
                    """SELECT * FROM TempChannels WHERE discordUser=?""",
                    (str(ctx.author.id),))
                member_id, text_channel_id, voice_channel_id, token = await cursor.fetchone()
            if ctx.author.id == member_id:
                await MaintainChannel.rem_channel(member_id, text_channel_id, voice_channel_id, token, self.bot, db)
        except TypeError:
            raise TempChannelNotFound()
        except Exception:
            logger.exception("Unexpected exception while remove temporary channels")

    async def cog_command_error(self, ctx: Context, error):
        if isinstance(error, CommandInvokeError):
            error = error.original

        if isinstance(error, UserError):
            await ctx.reply(content=str(error))

        if isinstance(error, TempChannels):
            await ctx.reply(f"<@!{ctx.author.id}>\n"
                            f"No channel was found that belongs to you.", delete_after=60)

        elif isinstance(error, CouldNotSendMessage):
            await ctx.reply(str(error), delete_after=60)

        elif isinstance(error, PrivateChannelsAlreadyExistsError):
            await ctx.reply(f"<@!{ctx.author.id}>\n"
                            f"You have already created a private channel.\n"
                            f"With `!tmpc rem` you can delete this channel.",
                            delete_after=60)

        elif isinstance(error, ModuleError):
            embed = EmbedGenerator("tmpc")
            await ctx.reply(content=f"<@!{ctx.author.id}>\n"
                                    f"This command was not found.",
                            embed=embed.generate(),
                            delete_after=60)
            embed = EmbedGenerator("tmpc-func")
            await ctx.reply(embed=embed.generate(),
                            delete_after=60)

        elif isinstance(error, TempChannelNotFound):
            await ctx.reply(f"<@!{ctx.author.id}>\n"
                            f"You do not have a temporary channel.",
                            delete_after=60)

        elif isinstance(error, global_only_handled_errors()):
            pass

        else:
            # noinspection PyBroadException
            try:
                raise error
            except Exception:
                logger.exception("Unexpected error")


def setup(bot: Bot):
    bot.add_cog(TempChannels(bot))
    bot.add_cog(Activities(bot))
