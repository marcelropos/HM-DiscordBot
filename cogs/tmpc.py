from datetime import datetime, timedelta
from typing import Union

from discord import Member, User, Embed, Guild
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

    @tmpc.command(pass_context=True)
    async def lock(self, ctx: Context):
        """
        Locks a Study or Gaming Channel.
        """
        document = await self.check_tmpc_channel(ctx)
        guild: Guild = ctx.guild

        key = ConfigurationNameEnum.STUDENTY.value
        verified = guild.get_role(
            (await PrimitiveMongoData(CollectionEnum.ROLES).find_one({key: {"$exists": True}}))[key])

        await document.voice.set_permissions(verified, view_channel=False)

        embed = Embed(title="Locked",
                      description=f"Locked this channel. Now only the students that you can see on the "
                                  f"right side can join and see the vc.\n"
                                  f"If you are not a moderator, moderators can join and see this channel.")
        await ctx.reply(embed=embed)

    @tmpc.command(pass_context=True)
    async def unlock(self, ctx: Context):
        """
        Unlocks a Study or Gaming Channel.
        """
        document = await self.check_tmpc_channel(ctx)
        guild: Guild = ctx.guild

        key = ConfigurationNameEnum.STUDENTY.value
        verified = guild.get_role(
            (await PrimitiveMongoData(CollectionEnum.ROLES).find_one({key: {"$exists": True}}))[key])

        await document.voice.set_permissions(verified, view_channel=True)

        embed = Embed(title="Unlocked",
                      description=f"Unlocked this channel. Now every Student can join the vc.")
        await ctx.reply(embed=embed)

    @tmpc.command(pass_context=True)
    async def token(self, ctx: Context, mode: str, user=None):
        """
        Manage token

        Args:
            ctx: The command context provided by the discord.py wrapper.

            mode: One of the following: show: show the current token; gen: generate a new token;
                    send <@user>: sends the token to a user.

            user: The user if you want to send the token directly to a user
        """
        document = await self.check_tmpc_channel(ctx)
        guild: Guild = ctx.guild

        if mode.lower() == "show":
            embed: Embed = Embed(title="Token",
                                 description=f"`!tmpc join {document.token}`")
        elif mode.lower() == "gen":
            new_token = TmpChannelUtil.create_token()
            new_document = {
                DBKeyWrapperEnum.OWNER.value: document.owner_id,
                DBKeyWrapperEnum.CHAT.value: document.channel_id,
                DBKeyWrapperEnum.VOICE.value: document.voice_id,
                DBKeyWrapperEnum.TOKEN.value: new_token,
            }
            if type(document) == StudyChannel:
                new_document.update({DBKeyWrapperEnum.DELETE_AT.value: document.deleteAt})
                await self.study_db.update_one(document.document, new_document)
            else:
                await self.gaming_db.update_one(document.document, new_document)
            embed: Embed = Embed(title="Token",
                                 description=f"`!tmpc join {new_token}`")
        elif mode.lower() == "send":
            if not ctx.message.mentions:
                raise BadArgument
            member: Union[Member, User] = ctx.message.mentions[0]
            embed: Embed = Embed(title="Token",
                                 description=f"`!tmpc join {document.token}`")
            await member.send(embed=embed)
            embed: Embed = Embed(title="Send token",
                                 description=f"Send token as a private message to {member.mention}")
        else:
            raise BadArgument

        await ctx.reply(embed=embed)

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
