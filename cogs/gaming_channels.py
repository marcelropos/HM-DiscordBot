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
from mongo.gaming_channels import GamingChannels
from mongo.primitive_mongo_data import PrimitiveMongoData

bot_channels: set[TextChannel] = set()
event = namedtuple("DeleteTime", ["hour", "min"])
gaming_join_voice_channel: Placeholder = Placeholder()
default_gaming_channel_name = "Gaming-{0:02d}"
gaming_channels: set[VoiceChannel] = set()
first_init = True

logger = get_discord_child_logger("GamingChannels")


class GamingTmpChannels(Cog):

    def __init__(self, bot: Bot):
        self.bot = bot
        self.config_db: PrimitiveMongoData = PrimitiveMongoData(CollectionEnum.TEMP_CHANNELS_CONFIGURATION)
        self.db: GamingChannels = GamingChannels(self.bot)
        self.need_init = True
        if not first_init:
            self.ainit.start()

    @loop()
    async def ainit(self):
        """
        Loads the configuration for the module.
        """
        global gaming_join_voice_channel, gaming_channels, default_gaming_channel_name
        # noinspection PyTypeChecker
        async with AinitManager(bot=self.bot, loop=self.ainit, need_init=self.need_init,
                                bot_channels=bot_channels) as need_init:
            if need_init:
                gaming_channels, default_gaming_channel_name \
                    = await TmpChannelUtil.ainit_helper(self.bot, self.db, self.config_db,
                                                        gaming_join_voice_channel,
                                                        ConfigurationNameEnum.GAMING_CATEGORY,
                                                        ConfigurationNameEnum.GAMING_JOIN_VOICE_CHANNEL,
                                                        ConfigurationNameEnum.DEFAULT_GAMING_NAME,
                                                        default_gaming_channel_name)

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

        global gaming_join_voice_channel, gaming_channels, default_gaming_channel_name
        guild: Guild = self.bot.guilds[0]

        event_type: EventType = EventType.status(before, after)

        if event_type == EventType.JOINED or event_type == EventType.SWITCHED:
            await TmpChannelUtil.joined_voice_channel(self.db, gaming_channels, after.channel,
                                                      gaming_join_voice_channel.item, guild,
                                                      default_gaming_channel_name, member,
                                                      ConfigurationNameEnum.GAMING_CATEGORY, logger)

        if event_type == EventType.LEFT or event_type == EventType.SWITCHED:
            voice_channel: VoiceChannel = before.channel
            if voice_channel in gaming_channels:
                if await TmpChannelUtil.check_delete_channel(voice_channel, self.db, logger):
                    gaming_channels.remove(voice_channel)

    @group(pass_context=True,
           name="gamingChannel")
    @bot_chat(bot_channels)
    @has_guild_permissions(administrator=True)
    async def gaming_channel(self, ctx: Context):
        if not ctx.invoked_subcommand:
            raise BadArgument
        member: Union[Member, User] = ctx.author
        logger.info(f'User="{member.name}#{member.discriminator}({member.id})", Command="{ctx.message.content}"')

    @gaming_channel.command(pass_context=True,
                            name="category")
    async def gaming_channel_category(self, ctx: Context, category: int):
        """
        Saves the category of the tmp study channels:

        Args:
            ctx: The command context provided by the discord.py wrapper.

            category: The category id for the channels.
        """

        db = PrimitiveMongoData(CollectionEnum.CATEGORIES)
        key = ConfigurationNameEnum.GAMING_CATEGORY
        msg = "category"
        await TmpChannelUtil.update_category_and_voice_channel(category, ctx, db, key, msg)

    @gaming_channel.command(pass_context=True,
                            name="join")
    async def gaming_channel_join(self, ctx: Context, channel: int):
        """
        Saves the enter point of tmp study channels:

        Args:
            ctx: The command context provided by the discord.py wrapper.

            channel: The voice_channel id.
        """

        db = PrimitiveMongoData(CollectionEnum.CHANNELS)
        key = ConfigurationNameEnum.GAMING_JOIN_VOICE_CHANNEL
        msg = "voice Channel"
        await TmpChannelUtil.update_category_and_voice_channel(channel, ctx, db, key, msg)

    @loop(minutes=10)
    async def delete_old_channels(self):
        to_delete = set()
        for voice_channel in gaming_channels:
            if await TmpChannelUtil.check_delete_channel(voice_channel, self.db, logger):
                to_delete.add(voice_channel)
        for old in to_delete:
            gaming_channels.remove(old)


def setup(bot: Bot):
    bot.add_cog(GamingTmpChannels(bot))
