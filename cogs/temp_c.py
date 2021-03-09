# noinspection PyUnresolvedReferences
import discord
from discord.ext.commands import Context, Bot
from discord.member import Member
from discord.channel import TextChannel, VoiceChannel
from discord.message import Message
from discord.abc import GuildChannel
from utils.embed_generator import EmbedGenerator
from utils.database import DB
from utils.logbot import LogBot
from utils.utils import *


# noinspection SqlResolve,SqlDialectInspection,SqlNoDataSourceInspection
class TempChannels(commands.Cog):
    """Create, edit or delete your temporary channel."""

    def __init__(self, bot: Bot):
        self.bot = bot
        self.logger = LogBot.logger

    @commands.group(pass_context=True,
                    aliases=["temp", "tempc"],
                    brief="Create, edit or delete your temporary channel.",
                    help="Command group")
    @commands.has_role(ServerIds.HM)
    async def tmpc(self, ctx: Context):
        if ctx.invoked_subcommand is None:
            raise ModuleError()

    # noinspection SqlNoDataSourceInspection,SqlDialectInspection
    @tmpc.command(pass_context=True,
                  brief="Create a channel.",
                  help="This channel will be deleted after you leave it.",
                  aliases=["make"])
    async def mk(self, ctx: Context, *, name: str):
        await accepted_channels(self.bot, ctx)
        member: Member = await ctx.guild.fetch_member(ctx.author.id)
        if DB.conn.execute(f"""SELECT * FROM TempChannels WHERE discordUser=?""",
                           (str(ctx.author.id),)).fetchone():
            raise PrivateChannelsAlreadyExistsError()

        category = ctx.guild.get_channel(ServerIds.CUSTOM_CHANNELS)

        voice_c: VoiceChannel = await ctx.guild.create_voice_channel(name,
                                                                     category=category,
                                                                     reason=f"request by {str(ctx.author)}")

        text_c: TextChannel = await ctx.guild.create_text_channel(name,
                                                                  category=category,
                                                                  reason=f"request by {str(ctx.author)}",
                                                                  topic=f"Created by: {str(ctx.author)}")
        token = mk_token()

        overwrite = TempChannels.get_permissions()

        await voice_c.set_permissions(member, overwrite=overwrite, reason="owner")
        await text_c.set_permissions(member, overwrite=overwrite, reason="owner")
        self.logger.debug(f"Created temporary channels: "
                          f"{ctx.author}-{ctx.author.id} owns text-{text_c.id},voice-{voice_c.id} with token-{token}")
        # noinspection PyBroadException
        try:
            await member.move_to(voice_c, reason="created this channel.")
        except Exception:
            pass

        # noinspection PyBroadException
        try:
            gen = EmbedGenerator("tmpc-func")
            embed = gen.generate()
            embed.add_field(name="Invite fellow students",
                            value=f"With ``!tmpc join {token}`` your fellow students can also join the (voice) chat.",
                            inline=False)

            await text_c.send(content=f"<@!{ctx.author.id}>",
                              embed=embed)
        except Exception:
            self.logger.exception("Can't send Message: ")
        # noinspection PyBroadException
        try:
            DB.conn.execute(f"INSERT INTO TempChannels("
                            f"discordUser, textChannel, voiceChannel, token) VALUES"
                            f"(?,?,?,?)",
                            (ctx.author.id, text_c.id, voice_c.id, token))
        except Exception:
            self.logger.exception("Database Error:")
        else:
            pass

    # noinspection PyDunderSlots,PyUnresolvedReferences
    @staticmethod
    def get_permissions():
        overwrite = discord.PermissionOverwrite()
        overwrite.mute_members = True
        overwrite.deafen_members = True
        overwrite.move_members = True
        overwrite.connect = True
        overwrite.read_messages = True
        return overwrite

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
            text_c, voice_c = DB.conn.execute("""SELECT textChannel, voiceChannel FROM TempChannels WHERE token=?""",
                                              (token,)).fetchone()
        except TypeError:
            raise TempChannelNotFound()
        else:
            text_c = await self.bot.fetch_channel(text_c)
            voice_c = await self.bot.fetch_channel(voice_c)
            await MaintainChannel.join(ctx.author, voice_c, text_c)

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
            member, text_c, voice_c, token = DB.conn.execute(f"""SELECT * FROM TempChannels WHERE discordUser=?""",
                                                             (str(ctx.author.id),)).fetchone()
        except TypeError:
            raise TempChannelNotFound()

        if mode.startswith("gen"):
            self.logger.debug("Generate new token")
            invites = DB.conn.execute(f"""SELECT * FROM Invites where token=?""",
                                      (str(token),)).fetchall()
            self.logger.debug(f"Deleting {len(invites)} invites")
            for message_id, _, member_id, channel_id in invites:
                await MaintainChannel.delete_invite(member_id, channel_id, message_id, ctx)

            token = mk_token()
            DB.conn.execute(f"""UPDATE TempChannels SET token = {token} WHERE discordUser=?""",
                            (str(ctx.author.id),))
            return

        if mode.startswith("place"):
            self.logger.debug(f"Place Token for {str(ctx.author)}")
            embed = MaintainChannel.invite_embed(ctx.author, f"```!tmpc join {token}```")
            message = await ctx.send(embed=embed)
            MaintainChannel.save_invite(ctx.author, message)
            await message.add_reaction(emoji="🔓")
            return

        if mode.startswith("send") and user:
            await accepted_channels(self.bot, ctx)
            embed = MaintainChannel.invite_embed(ctx.author, f"```!tmpc join {token}```")

            matches = re.finditer(r"[0-9]+", user)
            for match in matches:
                start, end = match.span()
                user_id = user[start:end]
                user = await discord.Client.fetch_user(self.bot, user_id)
                send_error = False
                error_user = set()

                # noinspection PyBroadException
                try:
                    message = await user.send(embed=embed)
                    await message.add_reaction(emoji="🔓")
                except Exception:
                    error_user.add(str(user))
                    send_error = True

                if send_error:
                    raise CouldNotSendMessage(f"Invitation could not be sent to: {error_user}.\n"
                                              f"Possibly this is caused by the settings of the users.")

    @tmpc.command(pass_context=True,
                  brief="Disable moderation",
                  help="Removes the access rights of the Moderator role to the channels.")
    @commands.has_role(ServerIds.MODERATOR)
    async def nomod(self, ctx):
        await accepted_channels(self.bot, ctx)
        try:
            text_c, voice_c = DB.conn.execute(
                """SELECT textChannel, voiceChannel FROM TempChannels WHERE discordUser=?""",
                str(ctx.author.id))

            role = discord.utils.get(ctx.guild.roles, id=ServerIds.MODERATOR)
            await voice_c.set_permissions(role,
                                          overwrite=None,
                                          reason="No mod active")

            await text_c.set_permissions(role,
                                         overwrite=None,
                                         reason="No mod active")
        except AttributeError:
            raise TempChannelNotFound()
        except Exception as e:
            self.logger.error("Unexpected issue: ", e)

    # noinspection SqlResolve
    @tmpc.command(pass_context=True,
                  brief="Delete the channel.",
                  help="With this command you can delete a channel manually.")
    async def rem(self, ctx: Context):
        # noinspection PyBroadException
        try:
            member, text_c, voice_c, token = DB.conn.execute("""SELECT * FROM TempChannels WHERE discordUser=?""",
                                                             (str(ctx.author.id),)).fetchone()
            if ctx.author.id == member:
                await MaintainChannel.rem_channel(member, text_c, voice_c, token, ctx)
        except TypeError:
            raise TempChannelNotFound()
        except Exception:
            self.logger.exception("Unexpected exception while remove temporary channels")

    @tmpc.error
    @mk.error
    @join.error
    @token.error
    @nomod.error
    @rem.error
    async def temp_errorhandler(self, ctx: Context, error):
        if isinstance(error, TempChannels):
            await ctx.send(f"<@!{ctx.author.id}>\n"
                           f"No channel was found that belongs to you.", delete_after=60)

        elif isinstance(error, CouldNotSendMessage):
            await ctx.send(str(error), delete_after=60)

        elif isinstance(error, PrivateChannelsAlreadyExistsError):
            await ctx.send(f"<@!{ctx.author.id}>\n"
                           f"You have already created a private channel.\n"
                           f"With `!tmpc rem` you can delete this channel.",
                           delete_after=60)

        elif isinstance(error, ModuleError):
            embed = EmbedGenerator("tmpc")
            await ctx.send(content=f"<@!{ctx.author.id}>\n"
                                   f"This command was not found.",
                           embed=embed.generate(),
                           delete_after=60)
            embed = EmbedGenerator("tmpc-func")
            await ctx.send(embed=embed.generate(),
                           delete_after=60)

        elif isinstance(error, WrongChatError):
            await ctx.message.delete()
            await ctx.send(f"<@!{ctx.author.id}>\n"
                           f"This command must not be used in this chat.\n"
                           f"Please use the designated chat<#{ServerIds.BOT_COMMANDS_CHANNEL}>.",
                           delete_after=60)

        elif isinstance(error, TempChannelNotFound):
            await ctx.send(f"<@!{ctx.author.id}>\n"
                           f"You do not have a temporary channel.",
                           delete_after=60)

        else:
            # noinspection PyBroadException
            try:
                raise error
            except Exception:
                self.logger.exception("Unexpected error")


def setup(bot: Bot):
    bot.add_cog(TempChannels(bot))
    MaintainChannel(bot)


# noinspection SqlResolve,SqlNoDataSourceInspection,PyBroadException,SqlDialectInspection
class MaintainChannel:
    bot = None

    @classmethod
    def __init__(cls, bot: Bot):
        cls.bot = bot

    @staticmethod
    async def update(ctx: Context, new_token):
        token = DB.conn.execute(f"""SELECT token FROM TempChannels where discordUser=?""",
                                (str(ctx.author.id),)).fetchone()
        invites = DB.conn.execute(f"""SELECT message_id FROM Invites where token=?""", (token,)).fetchall()
        for invite in invites:
            await MaintainChannel.delete_invite(invite, ctx)
        DB.conn.execute(f"""UPDATE TempChannels SET token=? where discordUser=?""",
                        (new_token, ctx.author.id))

    @staticmethod
    def save_invite(member: Member, message: Message):
        try:

            token = DB.conn.execute(f"""SELECT token FROM TempChannels where discordUser=?""",
                                    (member.id,)).fetchone()[0]
            LogBot.logger.debug(f"Save invite with token {token}")
            DB.conn.execute(f"""INSERT into Invites(message_id,token,member_id,channel_id)
            VALUES(?,?,?,?)""", (message.id, token, member.id, message.channel.id))
        except Exception:
            LogBot.logger.exception("Failed to insert Data")

    @classmethod
    async def delete_invite(cls, member_id: int, channel_id: int, message_id: int, ctx: Context):
        # noinspection PyBroadException
        try:
            member = await ctx.guild.fetch_member(member_id)

            embed = MaintainChannel.invite_embed(member, "Expired")
            channel = await discord.Client.fetch_channel(cls.bot, channel_id)
            message = await channel.fetch_message(message_id)
            await message.edit(embed=embed)
        except Exception:
            LogBot.logger.exception("Can't edit message: ")
        finally:
            DB.conn.execute(f"""delete from Invites where message_id=?""", (message_id,))

    @classmethod
    async def rem_channels(cls, ctx):

        channels = DB.conn.execute(f"""SELECT * FROM TempChannels""").fetchall()

        for user_id, text, voice_id, token in channels:
            # noinspection PyBroadException
            try:
                member: list = cls.bot.get_channel(voice_id).members
                if len(member) == 0:
                    await MaintainChannel.rem_channel(user_id, text, voice_id, token, ctx)
            except Exception:
                LogBot.logger.exception("Could not get member")

    # noinspection PyBroadException
    @classmethod
    async def rem_channel(cls, user_id: int, text: int, voice: int, token: int, ctx: Context):
        LogBot.logger.debug("Delete Channel")
        invites = DB.conn.execute(f"""SELECT message_id FROM Invites where token=?""", (token,)).fetchall()
        for invite in invites:
            await MaintainChannel.delete_invite(invite, ctx)
        DB.conn.execute(f"""delete from TempChannels where discordUser=?""", (user_id,))
        try:
            text = await discord.Client.fetch_channel(cls.bot, text)
            await text.delete(reason="No longer used")
        except Exception:
            LogBot.logger.exception("Can't delete text channel")
        try:
            voice = await discord.Client.fetch_channel(cls.bot, voice)
            await voice.delete(reason="No longer used")
        except Exception:
            LogBot.logger.exception("Can't delete voice channel")

    # noinspection PyDunderSlots,PyUnresolvedReferences,PyBroadException
    @staticmethod
    async def join(member: Member, voice_c: GuildChannel, text_c: GuildChannel):
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
            LogBot.logger.exception("Could not move User")

    @staticmethod
    def invite_embed(member: Member, token):
        embed = discord.Embed(title="Temporary channel invite",
                              colour=discord.Colour(0x12d4ca),
                              description="")

        embed.add_field(name="Creator",
                        value=f"{member.nick if member.nick else member.display_name}",
                        inline=False)

        embed.add_field(name="Token",
                        value="The reaction with 🔓 is equivalent to token input.",
                        inline=False)

        embed.add_field(name="Token",
                        value=token,
                        inline=False)
        return embed
