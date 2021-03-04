# noinspection PyUnresolvedReferences
import discord
# noinspection PyUnresolvedReferences
from discord.ext import commands
import re
# noinspection PyUnresolvedReferences
from utils.embed_generator import EmbedGenerator, BugReport
# noinspection PyUnresolvedReferences
from settings_files.all_errors import *
# noinspection PyProtectedMember,PyUnresolvedReferences
from settings_files._global import ServerIds, ServerRoles
from utils.database import DB
from utils.logbot import LogBot
from utils.utils import *


# noinspection SqlResolve
class TempChannels(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = LogBot.logger

    @commands.group()
    async def tmpc(self, ctx):
        if ctx.invoked_subcommand is None:
            raise ModuleError()

    @tmpc.command()
    @commands.has_role(ServerIds.HM)
    async def mk(self, ctx, *, arg):
        await accepted_channels(self.bot, ctx)
        member = await ctx.guild.fetch_member(ctx.author.id)
        if DB.conn.execute(f"""SELECT * FROM TempChannels WHERE discordUser=?""",
                           (str(ctx.author.id),)).fetchone():
            raise PrivateChannelsAlreadyExistsError()

        category = ctx.guild.get_channel(ServerIds.CUSTOM_CHANNELS)

        voice_c = await ctx.guild.create_voice_channel(arg,
                                                       category=category,
                                                       reason=f"request by {str(ctx.author)}")

        text_c = await ctx.guild.create_text_channel(arg,
                                                     category=category,
                                                     reason=f"request by {str(ctx.author)}",
                                                     topic=f"Erstellt von: {str(ctx.author)}")
        token = mk_token()

        overwrite = self.get_permisssions()

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
            embed.add_field(name="Kommilitonen einladen",
                            value=f"Mit ```!tmpc join {token}``` "
                                  f"können deine Kommilitonen ebenfalls dem (Voice-)Chat beitreten.",
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
    def get_permisssions():
        overwrite = discord.PermissionOverwrite()
        overwrite.mute_members = True
        overwrite.deafen_members = True
        overwrite.move_members = True
        overwrite.connect = True
        overwrite.read_messages = True
        return overwrite

    @tmpc.command()
    async def join(self, ctx, arg):
        try:
            await ctx.message.delete()
        except Exception as e:
            self.logger.error("Cann not delete join command", e)
        await accepted_channels(self.bot, ctx)

        try:
            text_c, voice_c = DB.conn.execute("""SELECT textChannel, voiceChannel FROM TempChannels WHERE token=?""",
                                              (arg,)).fetchone()
        except TypeError:
            raise TempChannelNotFound()
        else:
            text_c = await self.bot.fetch_channel(text_c)
            voice_c = await self.bot.fetch_channel(voice_c)
            await MaintainChannel.join(ctx.author, voice_c, text_c)

    @tmpc.command()
    async def token(self, ctx, command: str, *, args=None):
        try:
            member, text_c, voice_c, token = DB.conn.execute(f"""SELECT * FROM TempChannels WHERE discordUser=?""",
                                                             (str(ctx.author.id),)).fetchone()
        except TypeError:
            raise TempChannelNotFound()

        if command.startswith("gen"):
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

        if command.startswith("place"):
            self.logger.debug(f"Place Token for {str(ctx.author)}")
            embed = MaintainChannel.invite_embed(ctx.author, f"```!tmpc join {token}```")
            message = await ctx.send(embed=embed)
            MaintainChannel.save_invite(ctx.author, message)
            await message.add_reaction(emoji="🔓")
            return

        if command.startswith("send") and args:
            await accepted_channels(self.bot, ctx)
            embed = MaintainChannel.invite_embed(ctx.author, f"```!tmpc join {token}```")

            matches = re.finditer(r"[0-9]+", args)
            for match in matches:
                start, end = match.span()
                user_id = args[start:end]
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
                    raise CouldNotSendMessage(f"Einladung konnte nicht an: {error_user} gesendet werden."
                                              f"M\u00f6glicherweise liegt dies an den Einstellungen der User")

    @tmpc.command()
    @commands.has_role(ServerRoles.MODERATOR_ROLE_NAME)
    async def nomod(self, ctx):
        await accepted_channels(self.bot, ctx)
        try:
            text_c, voice_c = DB.conn.execute(
                """SELECT textChannel, voiceChannel FROM TempChannels WHERE discordUser=?""",
                str(ctx.author.id))

            role = discord.utils.get(ctx.guild.roles, name=ServerRoles.MODERATOR_ROLE_NAME)
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
    @tmpc.command()
    @commands.has_role(ServerIds.HM)
    async def rem(self, ctx):

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
    async def temp_errorhandler(self, ctx, error):
        DB.conn.execute(f"UPDATE comand_ctx SET error_status = 1 WHERE ctx_id=?", (ctx.message.id,))
        if isinstance(error, TempChannels):
            await ctx.send(f"<@!{ctx.author.id}>\n"
                           f"Es wurde kein Channel gefunden, der dir geh\u00f6rt.", delete_after=60)

        elif isinstance(error, CouldNotSendMessage):
            await ctx.send(error, delete_after=60)

        elif isinstance(error, PrivateChannelsAlreadyExistsError):
            await ctx.send(f"<@!{ctx.author.id}>\n"
                           f"Du hast bereits einen Privaten Channel erstellt.\n"
                           f"Mit `!tmpc rem` kannst du diesen L\u00f6schen.",
                           delete_after=60)

        elif isinstance(error, ModuleError):
            embed = EmbedGenerator("tmpc")
            await ctx.send(content=f"<@!{ctx.author.id}>\n"
                                   f"Dieser Befehl wurde nicht gefunden.",
                           embed=embed.generate(),
                           delete_after=60)
            embed = EmbedGenerator("tmpc-func")
            await ctx.send(embed=embed.generate(),
                           delete_after=60)

        elif isinstance(error, WrongChatError):
            await ctx.message.delete()
            await ctx.send(f"<@!{ctx.author.id}>\n"
                           f"Dieser Befehl darf in diesem Chat nicht verwendet werden.\n"
                           f"Nutzebitte den dafür vorgesehenen Chat <#{ServerIds.BOT_COMMANDS_CHANNEL}>.",
                           delete_after=60)

        elif isinstance(error, TempChannelNotFound):
            await ctx.send(f"<@!{ctx.author.id}>\n"
                           f"Du besitzt keinen temporären Channel",
                           delete_after=60)

        else:
            # noinspection PyBroadException
            try:
                raise error
            except Exception:
                self.logger.exception("Unexpected error")


def setup(bot):
    bot.add_cog(TempChannels(bot))
    MaintainChannel(bot)


# noinspection SqlResolve,SqlNoDataSourceInspection,PyBroadException
class MaintainChannel:
    bot = None

    @classmethod
    def __init__(cls, bot):
        cls.bot = bot

    @staticmethod
    async def update(ctx, new_token):
        token = DB.conn.execute(f"""SELECT token FROM TempChannels where discordUser=?""",
                                (str(ctx.author.id),)).fetchone()
        invites = DB.conn.execute(f"""SELECT message_id FROM Invites where token=?""", (token,)).fetchall()
        for invite in invites:
            await MaintainChannel.delete_invite(invite, ctx)
        DB.conn.execute(f"""UPDATE TempChannels SET token=? where discordUser=?""",
                        (new_token, ctx.author.id))

    @staticmethod
    def save_invite(member, message):
        try:

            token = DB.conn.execute(f"""SELECT token FROM TempChannels where discordUser=?""",
                                    (member.id,)).fetchone()[0]
            LogBot.logger.debug(f"Save invite with token {token}")
            DB.conn.execute(f"""INSERT into Invites(message_id,token,member_id,channel_id)
            VALUES(?,?,?,?)""", (message.id, token, member.id, message.channel.id))
        except Exception:
            LogBot.logger.exception("Failed to insert Data")

    @classmethod
    async def delete_invite(cls, member_id, channel_id, message_id, ctx):
        # noinspection PyBroadException
        try:
            member = await ctx.guild.fetch_member(member_id)

            embed = MaintainChannel.invite_embed(member, "Abgelaufen")
            channel = await discord.Client.fetch_channel(cls.bot, channel_id)
            message = await channel.fetch_message(message_id)
            await message.edit(embed=embed)
        except Exception:
            LogBot.logger.exception("Can't edit message: ")
        finally:
            DB.conn.execute(f"""delete from Invites where message_id=?""", (message_id,))

    @staticmethod
    async def rem_channels(ctx):

        channels = DB.conn.execute(f"""SELECT * FROM TempChannels""").fetchall()

        for user_id, text, voice, token in channels:
            # noinspection PyBroadException
            try:
                members = voice.members
                if len(members) == 0:
                    await MaintainChannel.rem_channel(user_id, text, voice, token, ctx)
            except Exception:
                pass

    # noinspection PyBroadException
    @classmethod
    async def rem_channel(cls, user_id, text, voice, token, ctx):
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
            LogBot.logger.exception("Could not move User")

    @staticmethod
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
