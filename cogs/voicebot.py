import asyncio
import datetime
import logging
import os
import random
import xml.etree.ElementTree as ET
from asyncio import Lock
from enum import IntEnum
from os import listdir
from os.path import isfile, join
from typing import Union

from discord import Member, VoiceChannel, FFmpegPCMAudio, VoiceClient, VoiceState
from discord.abc import User
from discord.ext import commands, tasks
from discord.ext.commands import Cog, Bot, Context

logger = logging.getLogger("discord")


class EventType(IntEnum):
    NOTHING = 0
    JOINED = 1
    LEFT = 2

    @classmethod
    def status(cls, before: VoiceState, after: VoiceState):
        if after.channel == before.channel:
            return cls.NOTHING
        if after.channel is None:
            return cls.LEFT
        return cls.JOINED


class Player:
    lock = Lock()
    not_played_since = datetime.datetime.now().timestamp()

    async def __aenter__(self):
        await self.__class__.lock.acquire()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.__class__.not_played_since = datetime.datetime.now().timestamp()
        self.__class__.lock.release()

    @staticmethod
    async def play(vc, audio_source):
        vc.play(audio_source)
        while vc.is_playing():
            await asyncio.sleep(0.1)

    @staticmethod
    async def disconnect(bot: Bot):
        if bot.voice_clients:
            vc: VoiceClient = bot.voice_clients[0]
            await vc.disconnect()

    @staticmethod
    async def connect(bot: Bot, voice_channel: VoiceChannel) -> VoiceClient:
        assert isinstance(voice_channel, VoiceChannel), "want an instance of VoiceChannel not something else."
        assert isinstance(bot, Bot), "want an instance of Bot not something else."
        if bot.voice_clients:
            vc: VoiceClient = bot.voice_clients[0]
            if vc.channel.id != voice_channel.id:
                await vc.move_to(voice_channel)
        else:
            await voice_channel.connect()
        vc: VoiceClient = bot.voice_clients[0]
        assert isinstance(vc, VoiceClient)
        await asyncio.sleep(0.3)
        return vc


class Greet:
    def __init__(self, bot: Bot):
        self.bot = bot
        self.lock = Player()
        self.last_greetings = dict()

    async def greet(self, member: Union[Member, User], channel: VoiceChannel):
        if member.id not in self.last_greetings:
            self.last_greetings[member.id] = datetime.datetime.now().timestamp() - 2 * 60 * 60
        time_delta = (datetime.datetime.now().timestamp() - self.last_greetings[member.id])
        hours, _ = divmod(time_delta, 3600)
        if hours > 1:
            source_dir = f"./data/audio/greeting/member/{member.id}"
            if not os.path.isdir(source_dir):
                return
            only_files = [f for f in listdir(source_dir) if isfile(join(source_dir, f))]
            audio_source_file = random.choice(only_files)
            audio_source = FFmpegPCMAudio(f"{source_dir}/{audio_source_file}")
            async with self.lock as player:
                vc = await player.connect(self.bot, channel)
                await player.play(vc, audio_source)
            self.last_greetings[member.id] = datetime.datetime.now().timestamp()


class Event(Cog):

    def __init__(self, bot: Bot):
        self.bot = bot
        self.greet = Greet(bot)
        self.config = ET.parse("./data/config.xml").getroot()
        guild_id = self.config.find("global").find("main-guild").text
        self.nerd_ecke_id = int(self.config
                                .find("Guilds")
                                .find(f"Guild-{guild_id}")
                                .find("Channels")
                                .find("NERD_ECKE")
                                .text)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: Union[Member, User], before: VoiceState, after: VoiceState):
        if member.bot and self.bot.user.id != member.id:
            return
        event_type = EventType.status(before, after)

        if event_type == EventType.JOINED and not member.bot:
            channel: VoiceChannel = after.channel

            if channel.id == self.nerd_ecke_id:
                await self.greet.greet(member, channel)

        elif event_type == EventType.LEFT and self.bot.voice_clients:
            channel: VoiceChannel = before.channel
            vc: VoiceClient = self.bot.voice_clients[0]

            if not member.bot \
                    and channel.id == vc.channel.id \
                    and not {member for member in channel.members if not member.bot}:
                async with Player() as player:
                    await player.disconnect(self.bot)


# noinspection PyTypeChecker
class AudioBot(Cog):

    def __init__(self, bot: Bot):

        self.bot = bot

        self.swallow_counter: int = 0

        self.swallow.start()

        self.config = ET.parse("./data/config.xml").getroot()
        guild_id = self.config.find("global").find("main-guild").text
        self.voice_bot_conf = self.config \
            .find("Guilds") \
            .find(f"Guild-{guild_id}") \
            .find("Cogs") \
            .find("VoiceBot")

    @commands.command(name="disconnect",
                      aliases=["dc"],
                      help="dc from the channel you are.",
                      brief="Disconnect from voicechannel")
    async def disconnect(self, ctx: Context):
        if self.bot.voice_clients \
                and ctx.channel \
                and ctx.channel.id == self.bot.voice_clients[0].id:
            async with Player() as player:
                await player.disconnect(self.bot)
        else:
            await ctx.reply(content="I cannot leave a channel in that I am not in.",
                            delete_after=60)

    @tasks.loop(minutes=1)
    async def swallow(self):
        guild_id = self.config.find("global").find("main-guild").text
        nerd_ecke_id = int(self.config
                           .find("Guilds")
                           .find(f"Guild-{guild_id}")
                           .find("Channels")
                           .find("NERD_ECKE")
                           .text)
        channel = await self.bot.fetch_channel(nerd_ecke_id)
        try:
            members: set[Union[Member, User]] = {member for member in channel.members if not member.bot}
        except AttributeError as error:
            if str(error) == "'Object' object has no attribute '_voice_states'":
                return None  # If this error occurs, the first execution is too early.
            else:
                raise

        if members:
            self.swallow_counter += 1
        else:
            self.swallow_counter = 0

        if self.swallow_counter > int(self.voice_bot_conf.find("intervall").text) - 1:
            audio_source = FFmpegPCMAudio(self.voice_bot_conf.find("swallow").text)

            async with Player() as player:
                vc = await player.connect(self.bot, channel)
                await player.play(vc, audio_source)
            self.swallow_counter = 0


def setup(bot: Bot):
    bot.add_cog(AudioBot(bot))
    bot.add_cog(Event(bot))
