# noinspection PyUnresolvedReferences
import discord
from discord.ext import commands, tasks
from utils.utils import ServerIds, EmojiIds
from settings import DefaultMessages
import re
from cogs.temp_c import MaintainChannel
from utils.database import DB
from utils.logbot import LogBot


# noinspection PyUnusedLocal,PyPep8Naming
class Activities(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.fetch_emojis.start()

    @commands.Cog.listener()
    async def on_ready(self):
        activity = discord.Game(name=DefaultMessages.ACTIVITY)
        await self.bot.change_presence(status=discord.Status.online,
                                       activity=discord.Activity(type=discord.ActivityType.listening,
                                                                 name=DefaultMessages.ACTIVITY))
        channel = discord.Client.get_channel(self=self.bot,
                                             id=ServerIds.DEBUG_CHAT)
        await channel.send(DefaultMessages.GREETINGS)
        print(DefaultMessages.GREETINGS)

    @tasks.loop(minutes=15)
    async def fetch_emojis(self):
        guild = await discord.Client.fetch_guild(self.bot, ServerIds.GUILD_ID)
        emojis = dict()
        for x in guild.emojis:
            emojis[re.sub(r"[^a-zA-Z0-9]", "", x.name.lower())] = x.id
        EmojiIds.nameset = emojis

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if member.bot:
            return

        if after.channel == await self.bot.fetch_channel(ServerIds.AFK_CHANNEL):
            await member.move_to(None, reason="AFK")

        await MaintainChannel.rem_channels(member)

        #TODO: Implement this again

        # await Channel_Functions.auto_bot_kick(before)

        # await Channel_Functions.nerd_ecke(self.bot, member)

        await Channel_Functions.nerd_ecke(self.bot, member)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        try:
            if payload.member.bot:
                return
        except AttributeError:
            pass

        if payload.member:
            member = payload.member  # For Guild
        else:
            member = await discord.Client.fetch_user(self.bot, payload.user_id)  # For private Messages

        # noinspection PyBroadException
        try:
            message_id = payload.message_id
            token = DB.conn.execute(f"""SELECT token FROM Invites where message_id={message_id}""").fetchone()[0]
            text_c, voice_c = DB.conn.execute(f"""SELECT textChannel, voiceChannel FROM TempChannels where token={token}""")\
                .fetchone()
            text_c = await self.bot.fetch_channel(text_c)
            voice_c = await self.bot.fetch_channel(voice_c)
            await MaintainChannel.join(member, voice_c, text_c)
        except Exception:
            LogBot.logger.exception("Activite error")


def setup(bot):
    bot.add_cog(Activities(bot))


class Channel_Functions:

    # noinspection PyBroadException
    @staticmethod
    async def auto_bot_kick(before):
        bot = []
        user = []
        try:
            for x in before.channel.members:
                if x.bot:
                    bot.append(x)
                else:
                    user.append(x)
            if len(user) == 0:
                for x in bot:
                    await x.move_to(None, reason="No longer used")
        except Exception:
            pass

    @staticmethod
    async def nerd_ecke(bot, member):
        all_roles = member.guild.roles
        role = None
        for x in all_roles:
            if x.name == "@everyone":
                role = x

        channel = await bot.fetch_channel(ServerIds.NERD_ECKE)
        members = len(channel.members)

        if members > 0:
            await channel.set_permissions(role, connect=True, reason="Nerd is here.")
        else:
            await channel.set_permissions(role, connect=False, reason="No nerds are here.")
