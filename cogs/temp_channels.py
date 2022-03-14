from collections import namedtuple
from typing import Union

from discord import VoiceState, Member, User, VoiceChannel, Guild, TextChannel, RawReactionActionEvent
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
from mongo.temp_channels import TempChannels

bot_channels: set[TextChannel] = set()
event = namedtuple("DeleteTime", ["hour", "min"])
study_join_voice_channel: Placeholder = Placeholder()
default_study_channel_name = "Study-{0:02d}"
temp_channels: set[VoiceChannel] = set()
first_init = True

logger = get_discord_child_logger("StudyChannels")


class StudyTmpChannels(Cog):
    """
    Configure study tmp settings.
    """

    def __init__(self, bot: Bot):
        self.bot = bot
        self.config_db: PrimitiveMongoData = PrimitiveMongoData(CollectionEnum.TEMP_CHANNELS_CONFIGURATION)
        self.db: TempChannels = TempChannels(self.bot)
        self.need_init = True
        if not first_init:
            self.ainit.start()
        logger.info(f"The cog is online.")

    @loop()
    async def ainit(self):
        """
        Loads the configuration for the module.
        """
        global study_join_voice_channel, temp_channels, default_study_channel_name, bot_channels
        # noinspection PyTypeChecker
        async with AinitManager(bot=self.bot, loop=self.ainit, need_init=self.need_init,
                                bot_channels=bot_channels) as need_init:
            if need_init:
                temp_channels, default_study_channel_name \
                    = await TmpChannelUtil.ainit_helper(self.bot, self.db,
                                                        self.config_db,
                                                        study_join_voice_channel,
                                                        ConfigurationNameEnum.STUDY_JOIN_VOICE_CHANNEL,
                                                        ConfigurationNameEnum.DEFAULT_STUDY_NAME,
                                                        default_study_channel_name)

                key = ConfigurationNameEnum.DEFAULT_KEEP_TIME.value
                default_keep_time = await self.config_db.find_one({key: {"$exists": True}})
                if not default_keep_time:
                    await self.config_db.insert_one({key: event(hour=24, min=0)})

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

        global study_join_voice_channel, temp_channels, default_study_channel_name
        guild: Guild = self.bot.guilds[0]

        event_type: EventType = EventType.status(before, after)

        if event_type == EventType.LEFT or event_type == EventType.SWITCHED:
            voice_channel: VoiceChannel = before.channel
            if voice_channel in temp_channels:
                if await TmpChannelUtil.check_delete_channel(voice_channel, self.db, logger,
                                                             reset_delete_at=(True, self.config_db)):
                    temp_channels.remove(voice_channel)

        if event_type == EventType.JOINED or event_type == EventType.SWITCHED:
            await TmpChannelUtil.joined_voice_channel(self.db, temp_channels, after.channel,
                                                      study_join_voice_channel.item, guild,
                                                      default_study_channel_name, member,
                                                      logger, self.bot)

    @group(pass_context=True,
           name="studyChannel",
           help="Configure study channel settings.")
    @bot_chat(bot_channels)
    @has_guild_permissions(administrator=True)
    async def study_channel(self, ctx: Context):
        if not ctx.invoked_subcommand:
            raise BadArgument
        member: Union[Member, User] = ctx.author
        logger.info(f'User="{member.name}#{member.discriminator}({member.id})", Command="{ctx.message.content}"')

    @study_channel.command(pass_context=True,
                           name="join",
                           brief="Sets a join channel.",
                           help="Joining the chosen channel will create a tmp channel.\n"
                                "The channel must be given as an int value.")
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
        channels = temp_channels.copy()
        for voice_channel in channels:
            if await TmpChannelUtil.check_delete_channel(voice_channel, self.db, logger):
                temp_channels.remove(voice_channel)


def setup(bot: Bot):
    bot.add_cog(StudyTmpChannels(bot))
