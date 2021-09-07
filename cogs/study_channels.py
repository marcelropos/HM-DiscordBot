from collections import namedtuple
from typing import Union

from discord import VoiceState, Member, User, VoiceChannel, Guild, TextChannel
from discord.ext.commands import Cog, Bot, has_guild_permissions, group, Context, BadArgument
from discord.ext.tasks import loop

from cogs.bot_status import listener
from cogs.util.ainit_ctx_mgr import AinitManager
from cogs.util.placeholder import Placeholder
from cogs.util.tmp_channel_util import TmpChannelUtil
from cogs.util.voice_state_change import EventType
from core.global_enum import CollectionEnum, ConfigurationNameEnum
from core.logger import get_discord_child_logger
from core.predicates import bot_chat
from mongo.primitive_mongo_data import PrimitiveMongoData
from mongo.study_channels import StudyChannels

bot_channels: set[TextChannel] = set()
event = namedtuple("DeleteTime", ["hour", "min"])
study_join_voice_channel: Placeholder = Placeholder()
default_study_channel_name = "Study-{0:02d}"
study_channels: set[VoiceChannel] = set()
first_init = True

logger = get_discord_child_logger("StudyChannels")


class StudyTmpChannels(Cog):

    def __init__(self, bot: Bot):
        self.bot = bot
        self.config_db: PrimitiveMongoData = PrimitiveMongoData(CollectionEnum.TEMP_CHANNELS_CONFIGURATION)
        self.db: StudyChannels = StudyChannels(self.bot)
        self.need_init = True
        if not first_init:
            self.ainit.start()

    @loop()
    async def ainit(self):
        """
        Loads the configuration for the module.
        """
        global study_join_voice_channel, study_channels, default_study_channel_name
        # noinspection PyTypeChecker
        async with AinitManager(bot=self.bot, loop=self.ainit, need_init=self.need_init,
                                bot_channels=bot_channels) as need_init:
            if need_init:
                study_channels, default_study_channel_name \
                    = await TmpChannelUtil.ainit_helper(self.bot, self.db,
                                                        self.config_db,
                                                        study_join_voice_channel,
                                                        ConfigurationNameEnum.STUDY_CATEGORY,
                                                        ConfigurationNameEnum.STUDY_JOIN_VOICE_CHANNEL,
                                                        ConfigurationNameEnum.DEFAULT_STUDY_NAME,
                                                        default_study_channel_name)

                key = ConfigurationNameEnum.DEFAULT_KEEP_TIME.value
                default_keep_time = await self.config_db.find_one({key: {"$exists": True}})
                if not default_keep_time:
                    await self.config_db.insert_one({key: event(hour=24, min=0)})

    def cog_unload(self):
        self.delete_old_channels.stop()

    @listener()
    async def on_ready(self):
        global first_init
        if first_init:
            first_init = False
            self.ainit.start()
            self.delete_old_channels.start()

    @listener()
    async def on_voice_state_update(self, member: Union[Member, User], before: VoiceState, after: VoiceState):
        if member.bot:
            return

        global study_join_voice_channel, study_channels, default_study_channel_name
        guild: Guild = self.bot.guilds[0]

        event_type: EventType = EventType.status(before, after)

        if event_type == EventType.LEFT or event_type == EventType.SWITCHED:
            voice_channel: VoiceChannel = before.channel
            if voice_channel in study_channels:
                if await TmpChannelUtil.check_delete_channel(voice_channel, self.db, logger,
                                                             reset_delete_at=(True, self.config_db)):
                    study_channels.remove(voice_channel)

        if event_type == EventType.JOINED or event_type == EventType.SWITCHED:
            await TmpChannelUtil.joined_voice_channel(self.db, study_channels, after.channel,
                                                      study_join_voice_channel.item, guild,
                                                      default_study_channel_name, member,
                                                      ConfigurationNameEnum.STUDY_CATEGORY, logger)

    @group(pass_context=True,
           name="studyChannel")
    @bot_chat(bot_channels)
    @has_guild_permissions(administrator=True)
    async def study_channel(self, ctx: Context):
        if not ctx.invoked_subcommand:
            raise BadArgument
        member: Union[Member, User] = ctx.author
        logger.info(f'User="{member.name}#{member.discriminator}({member.id})", Command="{ctx.message.content}"')

    @study_channel.command(pass_context=True,
                           name="category")
    async def study_channel_category(self, ctx: Context, category: int):
        """
        Saves the category of the tmp study channels:

        Args:
            ctx: The command context provided by the discord.py wrapper.

            category: The category id for the channels.
        """

        db = PrimitiveMongoData(CollectionEnum.CATEGORIES)
        key = ConfigurationNameEnum.STUDY_CATEGORY
        msg = "category"
        await TmpChannelUtil.update_category_and_voice_channel(category, ctx, db, key, msg)

    @study_channel.command(pass_context=True,
                           name="join")
    async def study_channel_join(self, ctx: Context, channel: int):
        """
        Saves the enter point of tmp study channels:

        Args:
            ctx: The command context provided by the discord.py wrapper.

            channel: The voice_channel id.
        """

        db = PrimitiveMongoData(CollectionEnum.CHANNELS)
        key = ConfigurationNameEnum.STUDY_JOIN_VOICE_CHANNEL
        msg = "voice Channel"
        await TmpChannelUtil.update_category_and_voice_channel(channel, ctx, db, key, msg)

    @loop(minutes=10)
    async def delete_old_channels(self):
        to_delete = set()
        for voice_channel in study_channels:
            if await TmpChannelUtil.check_delete_channel(voice_channel, self.db, logger):
                to_delete.add(voice_channel)
        for old in to_delete:
            study_channels.remove(old)


def setup(bot: Bot):
    bot.add_cog(StudyTmpChannels(bot))
