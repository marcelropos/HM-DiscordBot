# noinspection PyUnresolvedReferences
import discord
# noinspection PyUnresolvedReferences
from discord.ext import commands

# noinspection PyUnresolvedReferences
from utils import *
from settings import Embedgenerator


class PrivateChannelsAlreadyExistsError(UserError):
    pass


class TempChannelNotFound(UserError):
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
        except Exception:
            pass

        gen = Embedgenerator("tmpc_func")
        embed = gen.generate()
        embed.add_field(name="Kommilitonen einladen",
                        value=f"Mit ```!tmpc join {token}``` "
                              f"können deine Kommilitonen ebenfalls dem (Voice-)Chat beitreten.",
                        inline=False)
        await text_c.send(content=f"<@!{ctx.author.id}>",
                          embed=embed)

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
        else:
            raise TempChannelNotFound("Sorry, dieser Channel scheint nicht zu existieren.")

    @tmpc.command()
    @commands.has_role(ServerRoles.MODERATOR_ROLE_NAME)
    async def nomod(self, ctx):
        text_c, voice_c, _ = TMP_CHANNELS.tmp_channels[ctx.author.id]
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
        await TMP_CHANNELS.rem_channel(member, text_c, voice_c, token)


def setup(bot):
    bot.add_cog(TempChannels(bot))
