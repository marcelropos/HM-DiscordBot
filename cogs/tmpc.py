from datetime import datetime, timedelta
from typing import Union

from discord import Member, User, Embed, Guild, TextChannel, Message, NotFound, PermissionOverwrite
from discord.abc import GuildChannel
from discord.ext.commands import Bot, group, Cog, Context, BadArgument, cooldown, BucketType, \
    max_concurrency
from discord.ext.tasks import loop
from discord_components import DiscordComponents, Interaction, SelectOption, Select

from cogs.bot_status import listener
from cogs.util.ainit_ctx_mgr import AinitManager
from cogs.util.placeholder import Placeholder
from cogs.util.tmp_channel_util import TmpChannelUtil
from core.error.error_collection import WrongChatForCommandTmpc, CouldNotFindToken, NotOwnerError, \
    NameDuplicationError, LeaveOwnChannelError, TempChannelMayNotPersistError, YouOwnNoChannelsError
from core.error.error_reply import send_error
from core.global_enum import CollectionEnum, ConfigurationNameEnum, DBKeyWrapperEnum
from core.logger import get_discord_child_logger
from core.predicates import bot_chat, has_role_plus
from mongo.primitive_mongo_data import PrimitiveMongoData
from mongo.temp_channels import TempChannels, TempChannel

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
        self.channel_db: TempChannels = TempChannels(self.bot)
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
    @max_concurrency(1, BucketType.channel, wait=True)
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
        document = await self.check_tmpc_channel(ctx.author, ctx.channel.id)

        if not document.persist:
            raise TempChannelMayNotPersistError()

        key = ConfigurationNameEnum.DEFAULT_KEEP_TIME.value
        time_difference: tuple[int, int] = (await self.config_db.find_one({key: {"$exists": True}}))[key]
        document.deleteAt = datetime.now() + timedelta(hours=time_difference[0], minutes=time_difference[1])
        embed = Embed(title="Turned on keep",
                      description=f"This channel will stay for {time_difference[0]} hours and {time_difference[1]} "
                                  f"minutes, after everyone has left.\n"
                                  f"Please check the channel topic for the exact deletion time.")

        await self.channel_db.update_one({DBKeyWrapperEnum.CHAT.value: document.channel_id}, document.document)
        await ctx.reply(embed=embed)
        await document.chat.edit(
            topic=f"Owner: {document.owner.display_name}\n"
                  f"- This channel will be deleted at {document.deleteAt.strftime('%d.%m.%y %H:%M')} "
                  f"{datetime.now().astimezone().tzinfo}")
        await TmpChannelUtil.check_delete_channel(document.voice, self.channel_db, logger)

    @tmpc.command(pass_context=True,
                  help="Deletes the channel after leaving.")
    async def release(self, ctx: Context):
        """
        Deletes the channel after leaving.
        """
        document = await self.check_tmpc_channel(ctx.author, ctx.channel.id)

        if not document.persist:
            raise TempChannelMayNotPersistError()

        document.deleteAt = None
        embed = Embed(title="Turned off keep",
                      description=f"This channel will no longer stay after everyone leaves")

        await self.channel_db.update_one({DBKeyWrapperEnum.CHAT.value: document.channel_id}, document.document)
        await ctx.reply(embed=embed)
        await TmpChannelUtil.check_delete_channel(document.voice, self.channel_db, logger)

    @tmpc.command(pass_context=True,
                  brief="Hides the channel",
                  help="Not invited or not joined member will not see your tmp channel.")
    async def hide(self, ctx: Context):
        """
        Hides a Study or Gaming Channel.
        """
        document = await self.check_tmpc_channel(ctx.author, ctx.channel.id)
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
        document = await self.check_tmpc_channel(ctx.author, ctx.channel.id)
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
        document = await self.check_tmpc_channel(ctx.author, ctx.channel.id)
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
        document = await self.check_tmpc_channel(ctx.author, ctx.channel.id)
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
                  brief="Renames the Channel",
                  help="Renames the channel",
                  aliases=["rn", "mv"])
    @cooldown(1, 60, BucketType.channel)
    async def rename(self, ctx: Context, *, name: str):
        """
        Renames a study/gaming channel
        """
        document = await self.check_tmpc_channel(ctx.author, ctx.channel.id, is_mod=True)
        names = {channel.name.lower() for channel in ctx.guild.channels}

        if len(name) > 100:
            raise BadArgument("The given Name is to long.")
        if name.lower() in names:
            raise NameDuplicationError(name)

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
                       "- place: place an embed in the channel so that user can easily join the Study Channel.\n"
                       "\tAttention the place Command only works for Study Channels.")
    async def token(self, ctx: Context, mode: str):
        """
        Manage token

        Args:
            ctx: The command context provided by the discord.py wrapper.

            mode: One of the following:
                    show: show the current token;
                    gen: generate a new token;
                    place: place an embed in the channel so that user can easily join the Study Channel.
                        Attention the place Command only works for Study Channels.
        """
        if mode.lower() == "place":
            document: TempChannel = await self.get_temp_channel(ctx)

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
            replace = {DBKeyWrapperEnum.MESSAGES.value: document.messages + [message]}
            replace[DBKeyWrapperEnum.MESSAGES.value] = [(message.channel.id, message.id) for message in
                                                        replace[DBKeyWrapperEnum.MESSAGES.value]]
            await self.channel_db.update_one(document.document, replace)
            return

        if mode.lower() == "show":
            document = await self.check_tmpc_channel(ctx.author, ctx.channel.id, everyone=True)
            embed: Embed = Embed(title="Token",
                                 description=f"`!tmpc join {document.token}`")
        elif mode.lower() == "gen":
            document = await self.check_tmpc_channel(ctx.author, ctx.channel.id)
            new_token = TmpChannelUtil.create_token()
            new_document = {DBKeyWrapperEnum.TOKEN.value: new_token}

            new_document.update({DBKeyWrapperEnum.MESSAGES.value: list()})
            for message in document.messages:
                try:
                    await message.delete()
                except NotFound:
                    pass
            await self.channel_db.update_one({DBKeyWrapperEnum.ID.value: document.id}, new_document)

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
        document = await self.channel_db.find_one({key: token})

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
    @cooldown(1, 60, BucketType.channel)
    async def kick(self, ctx: Context, member: User):
        """
        Kicks a user from the tmpc channel

        Args:
           ctx: The command context provided by the discord.py wrapper.

           member: The member to kick
        """
        document = await self.check_tmpc_channel(ctx.author, ctx.channel.id, is_mod=True)

        msg: Message = ctx.message
        voice_overwrites: dict = document.voice.overwrites
        chat_overwrites: dict = document.chat.overwrites
        changed = False
        kicked = ""
        for mention in msg.mentions:
            mention: Member
            if mention in document.chat.members:
                # noinspection PyBroadException
                try:
                    voice_overwrites.pop(mention)
                    chat_overwrites.pop(mention)
                    changed = True
                    kicked += mention.mention + "\n"
                except KeyError:
                    pass

        if changed:
            await document.voice.edit(overwrite=voice_overwrites)
            await document.chat.edit(overwrite=chat_overwrites)
            for mention in msg.mentions:
                mention: Member
                if mention in document.voice.members:
                    # noinspection PyUnresolvedReferences
                    await member.move_to(None)

            embed: Embed = Embed(title="Kick")
            embed.add_field(name="Kicked", value=kicked)
            for member in document.chat.members:
                member: Member
                if moderator.item in member.roles:
                    break
            else:
                category: GuildChannel = document.voice.category
                voice_overwrites = document.voice.overwrites
                voice_overwrites[moderator.item] = category.overwrites[moderator.item]
                chat_overwrites = document.chat.overwrites
                chat_overwrites[moderator.item] = category.overwrites[moderator.item]
                await document.voice.edit(overwrite=voice_overwrites)
                await document.chat.edit(overwrite=chat_overwrites)
                embed.add_field(name="Moderator permissions",
                                value="Since this chat cannot be moderated without a moderator, "
                                      "the moderator rights will be restored.")

            await ctx.reply(embed=embed)

    @tmpc.command(pass_context=True,
                  aliases=["remove", "rem", "rm"],
                  brief="Deletes the tmpc even if someone is still in the channel",
                  help="You can force delete this tmpc even if people are still in the voice channel.")
    async def delete(self, ctx: Context):
        """
        Deletes the tmpc even if the voice channel is not empty

        Args:
           ctx: The command context provided by the discord.py wrapper.
        """
        document = await self.check_tmpc_channel(ctx.author, ctx.channel.id)
        try:
            await document.voice.delete(reason="Force deleted by owner")
        except (NotFound, AttributeError):
            pass
        try:
            await document.chat.delete(reason="Force deleted by owner")
        except (NotFound, AttributeError):
            pass

        for message in document.messages:
            try:
                await message.delete()
            except (NotFound, AttributeError):
                pass
        await self.channel_db.delete_one({DBKeyWrapperEnum.ID.value: document.id})

        logger.info(f"Deleted Tmp Channel {document.voice.name} on user command")

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

        document = await self.check_tmpc_channel(ctx.author, ctx.channel.id, is_mod=True)
        await document.voice.set_permissions(moderator.item, overwrite=None)
        await document.chat.set_permissions(moderator.item, overwrite=None)
        embed: Embed = Embed(title="No Mod",
                             description=f"Mods can't see or join this channel anymore")
        await ctx.reply(embed=embed)

    @tmpc.command(pass_context=True,
                  brief="Invite a user to your temp channel",
                  help="The first argument must be <true|false>\n"
                       "True: StudyChannel mode\n"
                       "False: TempChannel mode\n"
                       "Member must be invited by mentions.\n"
                       "Limitations:\n"
                       "- This command can be used 3/hour/user\n"
                       "- The invite command is limited to 10 user at once")
    @cooldown(3, 3600, BucketType.user)
    async def invite(self, ctx: Context):

        document = await self.get_temp_channel(ctx)

        voice_overwrites = document.voice.overwrites
        chat_overwrites = document.chat.overwrites
        msg: Message = ctx.message
        if len(msg.mentions) > 10:
            await ctx.reply("Warning hit limit")

        changed = False
        for mention in msg.mentions[:10]:
            if mention not in chat_overwrites:
                changed = True
                voice_overwrites[mention] = PermissionOverwrite(connect=True,
                                                                view_channel=True)
                chat_overwrites[mention] = PermissionOverwrite(view_channel=True)
            else:
                if document.chat.overwrites_for(mention).view_channel:
                    await send_error(ctx.message.channel, "Invitation",
                                     f"{mention.mention} can already see your channels",
                                     f"No Action required", ctx.author)
                else:  # could only be false or none
                    await send_error(ctx.message.channel, "Invitation",
                                     f"{mention.mention} used the left command on this channel",
                                     f"If {mention.mention} wants to join again {mention.mention} must use one of "
                                     f"the other common join methods", ctx.author, None)
        if changed:
            await document.voice.edit(overwrites=voice_overwrites)
            await document.chat.edit(overwrites=chat_overwrites)

    @tmpc.command(pass_context=True,
                  brief="Removes personal rights.",
                  help="Limitations:"
                       "- This command can be used 4/hour/user\n")
    @cooldown(1, 3600, BucketType.channel)
    async def leave(self, ctx: Context):
        document = await self.check_tmpc_channel(ctx.author, ctx.channel.id, everyone=True)
        if ctx.author.id == document.owner.id:
            raise LeaveOwnChannelError()

        voice_overwrites: dict = document.voice.overwrites
        chat_overwrites: dict = document.chat.overwrites
        changed = False
        if moderator.item in ctx.author.roles:
            try:
                voice_overwrites.pop(ctx.author)
                chat_overwrites.pop(ctx.author)
                changed = True
            except KeyError:
                pass
        else:
            changed = True
            try:
                voice_overwrites.pop(ctx.author)
            except KeyError:
                pass
            chat_overwrites[ctx.author] = PermissionOverwrite(view_channel=False)

        if changed:
            await document.voice.edit(overwrites=voice_overwrites)
            await document.chat.edit(overwrites=chat_overwrites)

    async def check_tmpc_channel(self, member: Member, _id: int, is_mod: bool = False, everyone: bool = False) \
            -> TempChannel:
        key = DBKeyWrapperEnum.CHAT.value
        document: TempChannel = await self.channel_db.find_one({key: _id})
        if not document:
            document = await self.channel_db.find_one({key: _id})

        if not document:
            raise WrongChatForCommandTmpc

        if everyone or member == document.owner or \
                (is_mod and moderator.item in member.roles):
            return document
        raise NotOwnerError(is_mod=is_mod, owner=document.owner.mention)

    async def get_temp_channel(self, ctx: Context) -> TempChannel:

        channels: list[TempChannel] = await self.channel_db.find({DBKeyWrapperEnum.OWNER.value: ctx.author.id})
        if not channels:
            raise YouOwnNoChannelsError()
        elif len(channels) == 1:
            return channels.pop()

        pool = {channel.chat.name: channel for channel in channels}

        options = Select(
            placeholder="Select your group",
            options=[SelectOption(label=channel.chat.name, value=channel.chat.name) for channel in channels])

        await ctx.reply(content="Please select **one** of the following groups.",
                        components=[options])

        res: Interaction = await self.bot.wait_for("select_option",
                                                   check=lambda x: self.check(x, [channel.chat.name for channel in
                                                                                  channels], ctx.author),
                                                   timeout=120)
        await res.respond(content=f"I received your input.")
        return pool[res.values[0]]

    @staticmethod
    def check(x, options: list[str], author: Member) -> bool:
        return x.values[0] in options and x.user.id == author.id


def setup(bot: Bot):
    bot.add_cog(Tmpc(bot))
