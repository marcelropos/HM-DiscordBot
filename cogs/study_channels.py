from collections import namedtuple
from typing import Union

from discord import VoiceState, Member, User, VoiceChannel, Guild, TextChannel
from discord.ext.commands import Cog, Bot, has_guild_permissions, group, Context, BadArgument
from discord.ext.tasks import loop

from cogs.bot_status import listener
from cogs.util.ainit_ctx_mgr import AinitManager
from cogs.util.assign_variables import assign_chat, assign_category
from cogs.util.placeholder import Placeholder
from cogs.util.tmp_channel_util import TmpChannelUtil
from cogs.util.voice_state_change import EventType
from core.error.error_collection import DatabaseIllegalState
from core.global_enum import CollectionEnum, ConfigurationNameEnum, DBKeyWrapperEnum
from core.logger import get_discord_child_logger
from core.predicates import bot_chat
from mongo.primitive_mongo_data import PrimitiveMongoData
from mongo.study_channels import StudyChannels, StudyChannel

bot_channels: set[TextChannel] = set()
event = namedtuple("DeleteTime", ["hour", "min"])
study_join_voice_channel: Placeholder = Placeholder()
default_study_channel_name = "Study-{0:02d}"
study_channels: set[VoiceChannel] = set()
first_init = True

logger = get_discord_child_logger("GamingChannels")


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
                await assign_category(self.bot, ConfigurationNameEnum.STUDY_CATEGORY)
                study_join_voice_channel.item = await assign_chat(self.bot,
                                                                  ConfigurationNameEnum.STUDY_JOIN_VOICE_CHANNEL)

                key = ConfigurationNameEnum.DEFAULT_KEEP_TIME.value
                default_keep_time = await self.config_db.find_one({key: {"$exists": True}})
                if not default_keep_time:
                    await self.config_db.insert_one({key: event(hour=24, min=0)})

                key = ConfigurationNameEnum.DEFAULT_STUDY_NAME.value
                default_study_channel_name_tmp = await self.config_db.find_one({key: {"$exists": True}})
                if default_study_channel_name_tmp:
                    default_study_channel_name = default_study_channel_name_tmp[key]
                else:
                    await self.config_db.insert_one({key: default_study_channel_name})

                deleted_channels: list[StudyChannel] = [document for document in await self.db.find({}) if
                                                        not document.voice or not document.chat]
                for deleted in deleted_channels:
                    await self.db.delete_one({DBKeyWrapperEnum.ID.value: deleted._id})

                guild: Guild = self.bot.guilds[0]
                study_channels = {document.voice for document in await self.db.find({})}

    @listener()
    async def on_ready(self):
        global first_init
        if first_init:
            first_init = False
            self.ainit.start()

    @listener()
    async def on_voice_state_update(self, member: Union[Member, User], before: VoiceState, after: VoiceState):
        if member.bot:
            return

        global study_join_voice_channel, study_channels, default_study_channel_name
        guild: Guild = self.bot.guilds[0]

        event_type: EventType = EventType.status(before, after)

        if event_type == EventType.JOINED or event_type == EventType.SWITCHED:
            voice_channel: VoiceChannel = after.channel
            if voice_channel is study_join_voice_channel.item:
                study_channels.add((await TmpChannelUtil.get_server_objects(ConfigurationNameEnum.STUDY_CATEGORY,
                                                                            guild, default_study_channel_name,
                                                                            member, self.db)).voice)
                logger.info(f"Created Tmp Study Channel with the name '{voice_channel.name}'")

            if voice_channel in study_channels:
                pass  # TODO permissions

        if event_type == EventType.LEFT or event_type == EventType.SWITCHED:
            voice_channel: VoiceChannel = before.channel
            if voice_channel in study_channels and len(
                    {member for member in voice_channel.members if not member.bot}) == 0:
                document: list[StudyChannel] = await self.db.find({DBKeyWrapperEnum.VOICE.value: voice_channel.id})

                if not document:
                    raise DatabaseIllegalState

                document: StudyChannel = document[0]

                # TODO check if it should be deleted at a later date

                await document.voice.delete(reason="No longer used")
                await document.chat.delete(reason="No longer used")

                await self.db.delete_one(document.document)

                study_channels.remove(voice_channel)

                logger.info(f"Deleted Tmp Study Channel {voice_channel.name}")

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


def setup(bot: Bot):
    bot.add_cog(StudyTmpChannels(bot))