from asyncio import sleep
from collections import namedtuple
from typing import Union, Optional

from discord import VoiceState, Member, User, VoiceChannel, Guild, TextChannel, RawReactionActionEvent
from discord.ext.commands import Cog, Bot, has_guild_permissions, group, Context, BadArgument
from discord.ext.tasks import loop

from cogs.bot_status import listener
from cogs.util.ainit_ctx_mgr import AinitManager
from cogs.util.tmp_channel_util import TmpChannelUtil
from cogs.util.voice_state_change import EventType
from core.global_enum import CollectionEnum, ConfigurationNameEnum, DBKeyWrapperEnum
from core.predicates import bot_chat
from mongo.join_temp_channels import JoinTempChannel, JoinTempChannels
from mongo.primitive_mongo_data import PrimitiveMongoData
from mongo.temp_channels import TempChannels

bot_channels: set[TextChannel] = set()
event = namedtuple("DeleteTime", ["hour", "min"])
temp_channels: set[VoiceChannel] = set()
first_init = True

logger = TmpChannelUtil.logger()


class StudyTmpChannels(Cog):
    """
    Configure study tmp settings.
    """

    def __init__(self, bot: Bot):
        self.bot = bot
        self.config_db: PrimitiveMongoData = PrimitiveMongoData(CollectionEnum.TEMP_CHANNELS_CONFIGURATION)
        self.db: TempChannels = TempChannels(self.bot)
        self.join_db: JoinTempChannels = JoinTempChannels(self.bot)
        self.need_init = True
        if not first_init:
            self.ainit.start()
        logger.info(f"The cog is online.")

    @loop()
    async def ainit(self):
        """
        Loads the configuration for the module.
        """
        global temp_channels, bot_channels
        # noinspection PyTypeChecker
        async with AinitManager(bot=self.bot, loop=self.ainit, need_init=self.need_init,
                                bot_channels=bot_channels) as need_init:
            if need_init:
                temp_channels = await TmpChannelUtil.ainit_helper(self.db)

                key = ConfigurationNameEnum.DEFAULT_KEEP_TIME.value
                default_keep_time = await self.config_db.find_one({key: {"$exists": True}})
                if not default_keep_time:
                    await self.config_db.insert_one({key: event(hour=24, min=0)})
            self.need_init = False

    def cog_unload(self):
        self.delete_old_channels.stop()
        logger.warning("Cog has been unloaded.")

    @listener()
    async def on_ready(self):
        global first_init
        if first_init:
            first_init = False
            self.ainit.start()
            self.delete_old_channels.start()

    @listener()
    async def on_raw_reaction_add(self, payload: RawReactionActionEvent):
        member: Union[Member, User] = payload.member
        if member.bot:
            return
        await self.wait_for_init()

        document = [document for document in await self.db.find({}) if payload.message_id in document.message_ids]

        if not document:
            return

        document = document[0]

        await document.voice.set_permissions(member, view_channel=True, connect=True)
        await document.chat.set_permissions(member, view_channel=True)

        try:
            await member.move_to(document.voice, reason="Joined via Token")
        except Exception:
            pass

    @listener()
    async def on_voice_state_update(self, member: Union[Member, User], before: VoiceState, after: VoiceState):
        if member.bot:
            return
        await self.wait_for_init()

        global temp_channels
        guild: Guild = self.bot.guilds[0]

        event_type: EventType = EventType.status(before, after)

        if event_type == EventType.LEFT or event_type == EventType.SWITCHED:
            voice_channel: VoiceChannel = before.channel
            if voice_channel in temp_channels:
                logger.info("Some user has left a temp channel.")
                if await TmpChannelUtil.check_delete_channel(voice_channel, self.db,
                                                             reset_delete_at=(True, self.config_db)):
                    temp_channels.remove(voice_channel)

        if event_type == EventType.JOINED or event_type == EventType.SWITCHED:
            await TmpChannelUtil.joined_voice_channel(self.db, temp_channels, after.channel, guild,
                                                      member, self.bot, self.join_db)

    @group(pass_context=True,
           name="tempChannel",
           help="Configure study channel settings.")
    @bot_chat(bot_channels)
    @has_guild_permissions(administrator=True)
    async def temp_channel(self, ctx: Context):
        if not ctx.invoked_subcommand:
            raise BadArgument
        member: Union[Member, User] = ctx.author
        logger.info(f'User="{member.name}#{member.discriminator}({member.id})", Command="{ctx.message.content}"')

    @temp_channel.command(pass_context=True,
                          name="join-add",
                          brief="Sets a join channel.",
                          help="Joining the chosen channel will create a tmp channel.\n"
                               "The channel must be given as an int value.")
    async def study_channel_join_add(self, ctx: Context, channel: VoiceChannel, pattern: str, persistent: bool):
        """
        Saves enter point of tmp study channels:

        Args:
            ctx: The command context provided by the discord.py wrapper.

            channel: The voice_channel id.

            pattern: The pattern of the default name: Example: Study-{0:02d}.

            persistent: The possibility that the created channel may persist.
        """
        await self.join_db.insert_one((channel, pattern, persistent))
        indicator = "" if persistent else "none"
        await ctx.reply(f"You can now create {indicator} persistent channels with {channel.category}:{channel.mention}.")

    @temp_channel.command(pass_context=True,
                          name="join-edit",
                          brief="Edits a join channel.",
                          help="The persistent indicator can be set to influence the possible behavior after exiting.")
    async def study_channel_join_edit(self, ctx: Context, channel: VoiceChannel, persistent: bool):
        """
        Edits enter point of tmp study channels:

        Args:
            ctx: The command context provided by the discord.py wrapper.

            channel: The voice_channel id.

            persistent: The possibility that the created channel may persist.
        """
        await self.join_db.update_one({DBKeyWrapperEnum.VOICE.value: channel.id},
                                      {DBKeyWrapperEnum.PERSIST.value: persistent})
        indicator = "" if persistent else "only none"
        await ctx.reply(f"{channel.category}:{channel.mention} allows now {indicator} persistent temp channel creation")

    @temp_channel.command(pass_context=True,
                          name="join-remove",
                          aliases=["join-rem", "join-rm"],
                          brief="Deletes a join channel.",
                          help="You will no longer be able to create channels.\n"
                               "This command does not delete the join channel itself.")
    async def study_channel_join_remove(self, ctx: Context, channel: VoiceChannel):
        """
        Edits enter point of tmp study channels:

        Args:
            ctx: The command context provided by the discord.py wrapper.

            channel: The voice_channel id.
        """
        channel: Optional[JoinTempChannel] = await self.join_db.find_one({DBKeyWrapperEnum.VOICE.value: channel.id})
        if channel:
            await self.join_db.delete_one(channel.document())
        await ctx.reply("No matter if the channel could be used to create other channels or not,"
                        "now it doesn't work anymore.")

    @loop(minutes=10)
    async def delete_old_channels(self):
        channels = temp_channels.copy()
        for voice_channel in channels:
            if await TmpChannelUtil.check_delete_channel(voice_channel, self.db):
                temp_channels.remove(voice_channel)

    async def wait_for_init(self):
        while self.need_init:
            await sleep(2)


def setup(bot: Bot):
    bot.add_cog(StudyTmpChannels(bot))
