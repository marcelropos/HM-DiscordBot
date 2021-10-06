from datetime import datetime, timedelta
from typing import Union

from discord import Member, User, Embed, Guild, TextChannel, Message, NotFound, PermissionOverwrite
from discord.ext.commands import Bot, group, Cog, Context, BadArgument, BotMissingPermissions, cooldown, BucketType
from discord.ext.tasks import loop
from discord_components import DiscordComponents

from cogs.bot_status import listener
from cogs.util.ainit_ctx_mgr import AinitManager
from cogs.util.placeholder import Placeholder
from cogs.util.tmp_channel_util import TmpChannelUtil
from core.error.error_collection import WrongChatForCommandTmpc, CouldNotFindToken
from core.global_enum import CollectionEnum, ConfigurationNameEnum, DBKeyWrapperEnum
from core.logger import get_discord_child_logger
from core.predicates import bot_chat, has_role_plus
from mongo.gaming_channels import GamingChannels, GamingChannel
from mongo.primitive_mongo_data import PrimitiveMongoData
from mongo.study_channels import StudyChannels, StudyChannel

bot_channels: set[TextChannel] = set()
moderator = Placeholder()
first_init = True

logger = get_discord_child_logger("Subjects")


class Tmpc(Cog):
    """
    Manages the gaming/study tmp channels.
    """

    def __init__(self, bot: Bot):
        self.bot = bot
        self.config_db: PrimitiveMongoData = PrimitiveMongoData(CollectionEnum.TEMP_CHANNELS_CONFIGURATION)
        self.study_db: StudyChannels = StudyChannels(self.bot)
        self.gaming_db: GamingChannels = GamingChannels(self.bot)
        self.need_init = True
        if not first_init:
            self.ainit.start()
        logger.info(f"The cog is online.")

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
        global moderator, bot_channels
        # noinspection PyTypeChecker
        async with AinitManager(bot=self.bot,
                                loop=self.ainit,
                                need_init=self.need_init,
                                bot_channels=bot_channels,
                                moderator=moderator) as need_init:
            if need_init:
                DiscordComponents(self.bot)

    def cog_unload(self):
        logger.warning("Cog has been unloaded.")

    @group(pass_context=True,
           name="tmpc",
           help="Manages the gaming/study tmp channels.")
    async def tmpc(self, ctx: Context):
        if not ctx.invoked_subcommand:
            raise BadArgument
        member: Union[Member, User] = ctx.author
        logger.info(f'User="{member.name}#{member.discriminator}({member.id})", Command="{ctx.message.content}"')

    @tmpc.command(pass_context=True,
                  help="Keeps the channel after leaving.")
    async def keep(self, ctx: Context):
        """
        Makes a Study Channel stay for a longer time.
        """
        document = await self.check_tmpc_channel(ctx)
        if type(document) == GamingChannel:
            raise BotMissingPermissions(["Channel needs to be Study Channel"])

        key = ConfigurationNameEnum.DEFAULT_KEEP_TIME.value
        time_difference: tuple[int, int] = (await self.config_db.find_one({key: {"$exists": True}}))[key]
        document.deleteAt = datetime.now() + timedelta(hours=time_difference[0], minutes=time_difference[1])
        embed = Embed(title="Turned on keep",
                      description=f"This channel will stay after everyone leaves for "
                                  f"{time_difference[0]} hours and {time_difference[1]} minutes.\n"
                                  f"Please check the channel topic for the exact deletion time.")

        await self.study_db.update_one({DBKeyWrapperEnum.CHAT.value: document.channel_id}, document.document)
        await ctx.reply(embed=embed)
        await document.chat.edit(
            topic=f"Owner: {document.owner.display_name}\n"
                  f"- This channel will be deleted at {document.deleteAt.strftime('%d.%m.%y %H:%M')} "
                  f"{datetime.now().astimezone().tzinfo}")
        await TmpChannelUtil.check_delete_channel(document.voice, self.study_db, logger, self.bot)

    @tmpc.command(pass_context=True,
                  help="Deletes the channel after leaving.")
    async def release(self, ctx: Context):
        """
        Deletes the channel after leaving.
        """
        document = await self.check_tmpc_channel(ctx)
        if type(document) == GamingChannel:
            raise BotMissingPermissions(["Channel needs to be Study Channel"])

        document.deleteAt = None
        embed = Embed(title="Turned off keep",
                      description=f"This channel will no longer stay after everyone leaves")

        await self.study_db.update_one({DBKeyWrapperEnum.CHAT.value: document.channel_id}, document.document)
        await ctx.reply(embed=embed)
        await TmpChannelUtil.check_delete_channel(document.voice, self.study_db, logger, self.bot)

    @tmpc.command(pass_context=True,
                  brief="Hides the channel",
                  help="Not invited or not joined member will not see your tmp channel.")
    async def hide(self, ctx: Context):
        """
        Hides a Study or Gaming Channel.
        """
        document = await self.check_tmpc_channel(ctx)
        guild: Guild = ctx.guild

        overwrites = document.voice.overwrites
        overwrites = await self.un_view_helper(overwrites, document, guild, ConfigurationNameEnum.STUDENTY.value, False)
        overwrites = await self.un_view_helper(overwrites, document, guild, ConfigurationNameEnum.FRIEND.value, False)
        overwrites = await self.un_view_helper(overwrites, document, guild, ConfigurationNameEnum.TMP_STUDENTY.value,
                                               False)
        await document.voice.edit(overwrites=overwrites)

        embed = Embed(title="Hidden",
                      description=f"Hidden this channel. Now only the students that you can see on the "
                                  f"right side can see the vc.\n"
                                  f"If you are not a moderator, moderators can join and see this channel.")
        await ctx.reply(embed=embed)

    @tmpc.command(pass_context=True,
                  brief="Shows the channel",
                  help="All member will see your tmp channel again.")
    async def show(self, ctx: Context):
        """
        Shows (Unhides) a Study or Gaming Channel.
        """
        document = await self.check_tmpc_channel(ctx)
        guild: Guild = ctx.guild

        overwrites = document.voice.overwrites
        overwrites = await self.un_view_helper(overwrites, document, guild, ConfigurationNameEnum.STUDENTY.value, True)
        overwrites = await self.un_view_helper(overwrites, document, guild, ConfigurationNameEnum.FRIEND.value, True)
        overwrites = await self.un_view_helper(overwrites, document, guild, ConfigurationNameEnum.TMP_STUDENTY.value,
                                               True)
        await document.voice.edit(overwrites=overwrites)

        embed = Embed(title="Unhidden",
                      description=f"Made this channel visible. Now every Student can see the vc.")
        await ctx.reply(embed=embed)

    @staticmethod
    async def un_view_helper(overwrites, document, guild, key, view):
        result = await PrimitiveMongoData(CollectionEnum.ROLES).find_one({key: {"$exists": True}})
        if result:
            role = guild.get_role(result[key])
            if role:
                overwrites[role] = PermissionOverwrite(connect=document.voice.overwrites_for(role).connect,
                                                       view_channel=view)
        return overwrites

    @tmpc.command(pass_context=True,
                  brief="Locks the channel",
                  help="Not invited or not joined member will not be able to access your tmp channel.")
    async def lock(self, ctx: Context):
        """
        Locks a Study or Gaming Channel.
        """
        document = await self.check_tmpc_channel(ctx)
        guild: Guild = ctx.guild

        overwrites = document.voice.overwrites
        overwrites = await self.un_lock_helper(overwrites, document, guild, ConfigurationNameEnum.STUDENTY.value, False)
        overwrites = await self.un_lock_helper(overwrites, document, guild, ConfigurationNameEnum.FRIEND.value, False)
        overwrites = await self.un_lock_helper(overwrites, document, guild, ConfigurationNameEnum.TMP_STUDENTY.value,
                                               False)
        await document.voice.edit(overwrites=overwrites)

        embed = Embed(title="Locked",
                      description=f"Locked this channel. Now only the students that you can see on the "
                                  f"right side can join the vc.\n"
                                  f"If you are not a moderator, moderators can join this channel.")
        await ctx.reply(embed=embed)

    @tmpc.command(pass_context=True,
                  brief="Locks the channel",
                  help="Not invited or not joined member will be able to access your tmp channel again.")
    async def unlock(self, ctx: Context):
        """
        Unlocks a Study or Gaming Channel.
        """
        document = await self.check_tmpc_channel(ctx)
        guild: Guild = ctx.guild

        overwrites = document.voice.overwrites
        overwrites = await self.un_lock_helper(overwrites, document, guild, ConfigurationNameEnum.STUDENTY.value, True)
        overwrites = await self.un_lock_helper(overwrites, document, guild, ConfigurationNameEnum.FRIEND.value, True)
        overwrites = await self.un_lock_helper(overwrites, document, guild, ConfigurationNameEnum.TMP_STUDENTY.value,
                                               True)
        await document.voice.edit(overwrites=overwrites)

        embed = Embed(title="Unlocked",
                      description=f"Unlocked this channel. Now every Student can join the vc.")
        await ctx.reply(embed=embed)

    @staticmethod
    async def un_lock_helper(overwrites, document, guild, key, connect):
        result = await PrimitiveMongoData(CollectionEnum.ROLES).find_one({key: {"$exists": True}})
        if result:
            role = guild.get_role(result[key])
            if role:
                overwrites[role] = PermissionOverwrite(connect=connect,
                                                       view_channel=document.voice.overwrites_for(role).view_channel)
        return overwrites

    @tmpc.command(pass_context=True,
                  brief="Locks the channel",
                  help="Not invited or not joined member will be able to access your tmp channel again.",
                  aliases=["rn", "mv"])
    @cooldown(1, 60, BucketType.user)
    async def rename(self, ctx: Context, *, name: str):
        """
        Renames a study/gaming channel
        """
        document = await self.check_tmpc_channel(ctx, is_mod=True)

        if len(name) > 100:
            raise BadArgument("The given Name is to long.")

        await document.chat.edit(name=name)
        await document.voice.edit(name=name)

        embed = Embed(title="Channels renamed.",
                      description=f"The channels are renamed to {name}")
        await ctx.reply(embed=embed)

    @tmpc.command(pass_context=True,
                  brief="Manages the token for your tmp channel",
                  help="mode:\n"
                       "- show: show the current token.\n"
                       "- gen: generate a new token.\n"
                       "- send <@user>: sends the token to a user.\n"
                       "- place: place an embed in the channel so that user can easily join the Study Channel.\n"
                       "\tAttention the place Command only works for Study Channels.")
    async def token(self, ctx: Context, mode: str, user=None):
        """
        Manage token

        Args:
            ctx: The command context provided by the discord.py wrapper.

            mode: One of the following:
                    show: show the current token;
                    gen: generate a new token;
                    send <@user>: sends the token to a user;
                    place: place an embed in the channel so that user can easily join the Study Channel.
                        Attention the place Command only works for Study Channels.

            user: The user if you want to send the token directly to a user
        """
        if mode.lower() == "place":
            document: StudyChannel = await self.study_db.find_one({DBKeyWrapperEnum.OWNER.value: ctx.author.id})
            if not document:
                embed: Embed = Embed(title="Could not find Channel",
                                     description="I could not find any Study that you are the owner of")
                await ctx.reply(embed=embed)
                return
            embed: Embed = Embed(title="Study Channel Invite",
                                 description="")
            embed.add_field(name="Creator",
                            value=ctx.author.mention,
                            inline=False)
            embed.add_field(name="Token",
                            value="The reaction with 🔓 is equivalent to token input.",
                            inline=False)

            embed.add_field(name="Token",
                            value=f"`!tmpc join {document.token}`",
                            inline=False)
            message: Message = await ctx.send(embed=embed)
            await ctx.message.delete()
            await message.add_reaction(emoji="🔓")
            new_document = {
                DBKeyWrapperEnum.OWNER.value: document.owner_id,
                DBKeyWrapperEnum.CHAT.value: document.channel_id,
                DBKeyWrapperEnum.VOICE.value: document.voice_id,
                DBKeyWrapperEnum.TOKEN.value: document.token,
                DBKeyWrapperEnum.DELETE_AT.value: document.deleteAt,
                DBKeyWrapperEnum.MESSAGES.value: document.messages + [message]
            }
            new_document[DBKeyWrapperEnum.MESSAGES.value] = [(message.channel.id, message.id) for message in
                                                             new_document[DBKeyWrapperEnum.MESSAGES.value]]
            await self.study_db.update_one(document.document, new_document)
            return

        document = await self.check_tmpc_channel(ctx)

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
                new_document.update({DBKeyWrapperEnum.DELETE_AT.value: document.deleteAt,
                                     DBKeyWrapperEnum.MESSAGES.value: list()})
                for message in document.messages:
                    try:
                        await message.delete()
                    except NotFound:
                        pass
                await self.study_db.update_one({DBKeyWrapperEnum.ID.value: document._id}, new_document)
            else:
                await self.gaming_db.update_one(document.document, new_document)
            embed: Embed = Embed(title="Token",
                                 description=f"`!tmpc join {new_token}`")
        else:
            raise BadArgument

        await ctx.reply(embed=embed)

    @tmpc.command(pass_context=True,
                  brief="Join a tmp channel.",
                  help="By submitting the token, you can join a tmp channel if the token is valid.")
    @bot_chat(bot_channels)
    async def join(self, ctx: Context, token: int):
        """
        Join a Study or Gaming Channel

        Args:
            ctx: The command context provided by the discord.py wrapper.

            token: The token for the Channel
        """
        key = DBKeyWrapperEnum.TOKEN.value
        document = await self.study_db.find_one({key: token})
        if not document:
            document = await self.gaming_db.find_one({key: token})

        if not document:
            raise CouldNotFindToken

        await document.voice.set_permissions(ctx.author, view_channel=True, connect=True)
        await document.chat.set_permissions(ctx.author, view_channel=True)
        await ctx.message.delete()

        try:
            await ctx.author.move_to(document.voice, reason="Joined via Token")
        except Exception:
            pass

    @tmpc.command(pass_context=True,
                  brief="Kicks user from tmpc",
                  help="You can remove a user from the list of users that can still join/see the channels after"
                       " you used tmpc hide of tmpc lock.")
    @has_role_plus(moderator)
    async def kick(self, ctx: Context, member: Union[User, Member]):
        """
        Kicks a user from the tmpc channel

        Args:
           ctx: The command context provided by the discord.py wrapper.

           member: The member to kick
        """
        document = await self.check_tmpc_channel(ctx, is_mod=True)
        await document.voice.set_permissions(member, overwrite=None)
        await document.chat.set_permissions(member, overwrite=None)
        embed: Embed = Embed(title="Kick",
                             description=f"{member.mention} was kicked.")
        await ctx.reply(embed=embed)

    @tmpc.command(pass_context=True,
                  brief="Removes mod rights.",
                  help="Mods have special rights. Lock and hide commands are ineffective against moderators."
                       "This command removes these special rights.")
    @has_role_plus(moderator)
    async def nomod(self, ctx: Context):
        """
        Keeps out the Mods out of the Gaming or Study Channel

        Args:
           ctx: The command context provided by the discord.py wrapper.
        """
        global moderator

        document = await self.check_tmpc_channel(ctx, is_mod=True)
        await document.voice.set_permissions(moderator.item, overwrite=None)
        await document.chat.set_permissions(moderator.item, overwrite=None)
        embed: Embed = Embed(title="No Mod",
                             description=f"Mods can't see or join this channel anymore")
        await ctx.reply(embed=embed)

    async def check_tmpc_channel(self, ctx: Context, is_mod: bool = False) -> Union[GamingChannel, StudyChannel]:
        key = DBKeyWrapperEnum.CHAT.value
        document: Union[GamingChannel, StudyChannel] = await self.study_db.find_one({key: ctx.channel.id})
        if not document:
            document = await self.gaming_db.find_one({key: ctx.channel.id})

        if not document:
            raise WrongChatForCommandTmpc
        elif not is_mod and document.owner != ctx.author:
            raise BotMissingPermissions
        return document


def setup(bot: Bot):
    bot.add_cog(Tmpc(bot))
