# noinspection PyUnresolvedReferences
import discord
# noinspection PyUnresolvedReferences
from discord.ext import commands

# noinspection PyUnresolvedReferences
from utils import *


class PrivateChannelsAlreadyExistsError(UserError):
    pass


class TempChannelNotFound(UserError):
    pass


# noinspection PyUnusedLocal,PyUnresolvedReferences,PyDunderSlots
class TempChannels(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # noinspection PyBroadException
    @commands.command()
    @commands.has_role(ServerRoles.HM)
    async def tmpc(self, ctx, *, arg):
        member = await ctx.guild.fetch_member(ctx.author.id)
        if member.id in TMP_CHANNELS.tmp_channels:
            raise PrivateChannelsAlreadyExistsError("Du hast bereits einen Privaten Channel erstellt.")
        voice_c = await ctx.guild.create_voice_channel(arg, category=TMP_CHANNELS,
                                                       reason=f"request by {str(ctx.author)}")
        text_c = await ctx.guild.create_text_channel(arg, category=TMP_CHANNELS, reason=f"request by {str(ctx.author)}",
                                                     topic=f"Erstellt von: {str(ctx.author)}")
        token = mk_token()

        TMP_CHANNELS.update(member, text_c, voice_c, token)

        await text_c.send(f"Mit ```!join {token}``` können deine Kommilitonen ebenfalls dem (Voice-)Chat beitreten.")
        overwrite = discord.PermissionOverwrite()
        overwrite.manage_permissions = True
        overwrite.mute_members = True
        overwrite.deafen_members = True
        overwrite.move_members = True
        overwrite.connect = True
        overwrite.read_messages = True

        await voice_c.set_permissions(member, overwrite=overwrite, reason="owner")
        await text_c.set_permissions(member, overwrite=overwrite, reason="owner")
        try:
            await member.move_to(voice_c, reason="created this channel.")
        except Exception:
            pass

    # noinspection PyBroadException
    @commands.command()
    async def join(self, ctx, arg):
        my_guild = await self.bot.fetch_guild(ServerIds.GUILD_ID)
        member = await my_guild.fetch_member(ctx.author.id)
        if arg in TMP_CHANNELS.token:
            text_c, voice_c = TMP_CHANNELS.token[arg]
            overwrite = discord.PermissionOverwrite()
            overwrite.connect = True
            overwrite.read_messages = True
            await voice_c.set_permissions(member, overwrite=overwrite, reason="access by token")
            await text_c.set_permissions(member, overwrite=overwrite, reason="access by token")
            try:
                await member.move_to(voice_c, reason="want to join this Channel.")
            except Exception:
                pass
        else:
            raise TempChannelNotFound("Sorry, dieser Channel scheint nicht zu existieren.")


def setup(bot):
    bot.add_cog(TempChannels(bot))
