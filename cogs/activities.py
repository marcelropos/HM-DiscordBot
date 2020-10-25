# noinspection PyUnresolvedReferences
import discord
from discord.ext import commands
from utils import TMP_CHANNELS, ServerIds
from settings import DefaultMessages


# noinspection PyUnusedLocal,PyPep8Naming
class Activities(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        TMP_CHANNELS(self.bot)
        activity = discord.Game(name=DefaultMessages.ACTIVITY)
        await discord.Client.change_presence(self=self.bot, status=discord.Status.online, activity=activity)
        channel = discord.Client.get_channel(self=self.bot, id=ServerIds.DEBUG_CHAT)
        await channel.send(DefaultMessages.GREETINGS)
        print(DefaultMessages.GREETINGS)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if member.bot:
            return
        # noinspection PyBroadException
        try:
            await TMP_CHANNELS.rem_channel()
        except Exception:
            pass

    # noinspection PyUnresolvedReferences
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        message_id = payload.message_id
        channel_id = payload.channel_id
        channel = await self.bot.fetch_channel(channel_id)
        message = await channel.fetch_message(message_id)
        print(message.reactions)


def setup(bot):
    bot.add_cog(Activities(bot))
