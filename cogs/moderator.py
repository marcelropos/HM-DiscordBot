# noinspection PyUnresolvedReferences
from discord.ext import commands, tasks
import discord
# noinspection PyUnresolvedReferences
from settings_files._global import ServerRoles, ServerIds, DEBUG_STATUS
import datetime
from utils.logbot import LogBot


class Moderator(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        #  self.kick_not_verified.start()

    # noinspection PyUnusedLocal
    @tasks.loop(hours=24)
    async def kick_not_verified(self, ctx=None):
        if DEBUG_STATUS():
            guild = await discord.Client.fetch_guild(self.bot, ServerIds.GUILD_ID)
            async for member in guild.fetch_members(limit=None):
                got_roles = {role.name for role in member.roles}
                if len(got_roles) == 1:
                    if (datetime.datetime.now() - member.joined_at).days > 60:
                        # noinspection PyBroadException
                        try:
                            await member.send(content="Du wirst vom Server geickt, "
                                                      "da du zu lange nicht verifiziert wurdest."
                                                      "Du kannst dem Server erneut beitreten und einen Antrag auf eine "
                                                      "Verifikation stellen.", delete_after=86400)
                        except Exception:
                            pass
                        # noinspection PyBroadException
                        try:
                            await member.kick(reason="Zu lange ohne Verifikation")
                        except Exception:
                            channel = await self.bot.fetch_channel(ServerIds.DEBUG_CHAT)
                            await channel.send(f"Failed to kick <@{member.id}>.")
                        else:
                            LogBot.logger.info(f"Kicked: {member} for being not verified")


def setup(bot):
    bot.add_cog(Moderator(bot))
