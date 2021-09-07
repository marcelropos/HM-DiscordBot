from datetime import datetime, timedelta
from typing import Union

from discord import Member, User, Embed
from discord.ext.commands import Bot, group, Cog, Context, BadArgument
from discord.ext.tasks import loop

from cogs.bot_status import listener
from cogs.util.ainit_ctx_mgr import AinitManager
from cogs.util.assign_variables import assign_role
from cogs.util.placeholder import Placeholder
from cogs.util.tmp_channel_util import TmpChannelUtil
from core.error.error_collection import WrongChatForCommand, MayNotUseCommandError
from core.global_enum import CollectionEnum, ConfigurationNameEnum, DBKeyWrapperEnum
from core.logger import get_discord_child_logger
from mongo.gaming_channels import GamingChannels, GamingChannel
from mongo.primitive_mongo_data import PrimitiveMongoData
from mongo.study_channels import StudyChannels, StudyChannel

moderator = Placeholder()
first_init = True

logger = get_discord_child_logger("Subjects")


class Tmpc(Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
        self.config_db: PrimitiveMongoData = PrimitiveMongoData(CollectionEnum.TEMP_CHANNELS_CONFIGURATION)
        self.study_db: StudyChannels = StudyChannels(self.bot)
        self.gaming_db: GamingChannels = GamingChannels(self.bot)
        self.need_init = True
        if not first_init:
            self.ainit.start()

    @listener()
    async def on_ready(self):
        global first_init
        if first_init:
            first_init = False
            self.ainit.start()

    @loop()
    async def ainit(self):
        """
        Loads the configuration for the module.
        """
        global moderator
        # noinspection PyTypeChecker
        async with AinitManager(self.bot, self.ainit, self.need_init) as need_init:
            if need_init:
                moderator.item = await assign_role(self.bot, ConfigurationNameEnum.MODERATOR_ROLE)

    @group(pass_context=True,
           name="tmpc")
    async def tmpc(self, ctx: Context):
        if not ctx.invoked_subcommand:
            raise BadArgument
        member: Union[Member, User] = ctx.author
        logger.info(f'User="{member.name}#{member.discriminator}({member.id})", Command="{ctx.message.content}"')

    @tmpc.command(pass_context=True)
    async def keep(self, ctx: Context):
        """
        Makes a Study Channel stay for a longer time.
        """
        document = await self.check_tmpc_channel(ctx)
        if type(document) == GamingChannel:
            raise MayNotUseCommandError
        if document.deleteAt:
            document.deleteAt = None
            embed = Embed(title="Turned off keep",
                          description=f"This channel will no longer stay after everyone leaves")
        else:
            key = ConfigurationNameEnum.DEFAULT_KEEP_TIME.value
            time_difference: tuple[int, int] = (await self.config_db.find_one({key: {"$exists": True}}))[key]
            document.deleteAt = datetime.now() + timedelta(hours=time_difference[0], minutes=time_difference[1])
            embed = Embed(title="Turned on keep",
                          description=f"This channel will stay after everyone leaves for "
                                      f"{time_difference[0]} hours and {time_difference[1]} minutes")

        await self.study_db.update_one({DBKeyWrapperEnum.CHAT.value: document.channel_id}, document.document)
        await ctx.reply(embed=embed)
        await TmpChannelUtil.check_delete_channel(document.voice, self.study_db, logger)

    async def check_tmpc_channel(self, ctx: Context) -> Union[GamingChannel, StudyChannel]:
        key = DBKeyWrapperEnum.CHAT.value
        document: Union[GamingChannel, StudyChannel] = await self.study_db.find_one({key: ctx.channel.id})
        if not document:
            document = await self.gaming_db.find_one({key: ctx.channel.id})

        if not document:
            raise WrongChatForCommand
        elif document.owner != ctx.author:
            raise MayNotUseCommandError
        return document


def setup(bot: Bot):
    bot.add_cog(Tmpc(bot))
