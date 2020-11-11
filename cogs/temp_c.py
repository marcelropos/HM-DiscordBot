# noinspection PyUnresolvedReferences
import discord
# noinspection PyUnresolvedReferences
from discord.ext import commands
import re
# noinspection PyUnresolvedReferences
from settings import Embedgenerator
from utils import *


class PrivateChannelsAlreadyExistsError(UserError):
    pass


class TempChannelNotFound(UserError):
    pass


class CouldNotSendMessage(UserError):
    pass


# noinspection PyUnusedLocal,PyUnresolvedReferences,PyDunderSlots
class TempChannels(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # noinspection PyBroadException
    @commands.group()
    async def tmpc(self, ctx):
        if ctx.invoked_subcommand is None:
            raise ModuleError("Befehl nicht gefunden")

    @tmpc.command()
    @commands.has_role(ServerRoles.HM)
    async def mk(self, ctx, *, arg):
        member = await ctx.guild.fetch_member(ctx.author.id)
        if member.id in TMP_CHANNELS.tmp_channels:
            raise PrivateChannelsAlreadyExistsError("Du hast bereits einen Privaten Channel erstellt.")

        voice_c = await ctx.guild.create_voice_channel(arg,
                                                       category=TMP_CHANNELS,
                                                       reason=f"request by {str(ctx.author)}")

        text_c = await ctx.guild.create_text_channel(arg,
                                                     category=TMP_CHANNELS,
                                                     reason=f"request by {str(ctx.author)}",
                                                     topic=f"Erstellt von: {str(ctx.author)}")
        token = mk_token()

        overwrite = discord.PermissionOverwrite()
        overwrite.mute_members = True
        overwrite.deafen_members = True
        overwrite.move_members = True
        overwrite.connect = True
        overwrite.read_messages = True

        await voice_c.set_permissions(member, overwrite=overwrite, reason="owner")
        await text_c.set_permissions(member, overwrite=overwrite, reason="owner")
        # noinspection PyBroadException
        try:
            await member.move_to(voice_c, reason="created this channel.")

            gen = Embedgenerator("tmpc-func")
            embed = gen.generate()
            embed.add_field(name="Kommilitonen einladen",
                            value=f"Mit ```!tmpc join {token}``` "
                                  f"können deine Kommilitonen ebenfalls dem (Voice-)Chat beitreten.",
                            inline=False)

            await text_c.send(content=f"<@!{ctx.author.id}>",
                              embed=embed)
        except Exception:
            pass

        TMP_CHANNELS.update(member, text_c, voice_c, token)

    # noinspection PyBroadException
    @tmpc.command()
    async def join(self, ctx, arg):
        try:
            await ctx.message.delete()
        except Exception:
            pass
        my_guild = await self.bot.fetch_guild(ServerIds.GUILD_ID)
        member = await my_guild.fetch_member(ctx.author.id)

        if arg in TMP_CHANNELS.token:
            text_c, voice_c = TMP_CHANNELS.token[arg]

            await TMP_CHANNELS.join(ctx.author, voice_c, text_c)

        else:
            raise TempChannelNotFound("Sorry, dieser Channel scheint nicht zu existieren.")

    @tmpc.command()
    async def token(self, ctx, command: str, *, args=None):
        text, voice, token, invites = await TMP_CHANNELS.get_ids(ctx.author)

        if command.startswith("gen"):
            token = mk_token()
            embed = invite_embed(ctx.author, "Abgelaufen")

            loop = invites.copy()  # Avoid RuntimeError: dictionary changed size during iteration
            for x in loop:
                await TMP_CHANNELS.delete_invite(ctx.author.id, invites[x].channel, x, ctx)

        TMP_CHANNELS.update(ctx.author, text, voice, token)

        if command.startswith("place"):
            embed = invite_embed(ctx.author, f"```!tmpc join {token}```")
            message = await ctx.send(embed=embed)
            await TMP_CHANNELS.save_invite(ctx.author, message)
            await message.add_reaction(emoji="🔓")

        if command.startswith("send") and args:
            embed = invite_embed(ctx.author, f"```!tmpc join {token}```")

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
                    await TMP_CHANNELS.save_invite(ctx.author, message)
                    await message.add_reaction(emoji="🔓")
                except Exception:
                    error_user.add(str(user))
                    send_error = True

                if send_error:
                    raise CouldNotSendMessage(f"Einladung konnte nicht an: {error_user} gesendet werden."
                                              f"Möglicherweise liegt dies an den Einstellungen der User")

    @tmpc.command()
    @commands.has_role(ServerRoles.MODERATOR_ROLE_NAME)
    async def nomod(self, ctx):
        text_c, voice_c, *_ = TMP_CHANNELS.tmp_channels[ctx.author.id]
        if ctx.author.id in TMP_CHANNELS.tmp_channels:
            overwrite = discord.PermissionOverwrite()
            mod = role = discord.utils.get(ctx.guild.roles, name=ServerRoles.MODERATOR_ROLE_NAME)
            await voice_c.set_permissions(mod,
                                          overwrite=None,
                                          reason="access by token")

            await text_c.set_permissions(mod,
                                         overwrite=None,
                                         reason="access by token")
            pass
        else:
            raise TempChannelNotFound("Anscheindend besitzt du keinen Channel")

    @tmpc.command()
    @commands.has_role(ServerRoles.HM)
    async def rem(self, ctx):
        member = ctx.author.id
        text_c, voice_c, token = TMP_CHANNELS.tmp_channels[member]
        await TMP_CHANNELS.rem_channel(member, text_c, voice_c, token, ctx)


def setup(bot):
    bot.add_cog(TempChannels(bot))
