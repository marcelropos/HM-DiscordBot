import logging
from asyncio import Lock
from datetime import datetime, timedelta
from typing import Union

import pyotp
from discord import Guild, CategoryChannel, PermissionOverwrite, Member, User, TextChannel, VoiceChannel, Embed, \
    NotFound
from discord.ext.commands import Context, Bot

from cogs.util.assign_variables import assign_category, assign_chat, assign_accepted_chats
from cogs.util.placeholder import Placeholder
from core.discord_limits import CATEGORY_CHANNEL_LIMIT, GLOBAL_CHANNEL_LIMIT
from core.error.error_collection import BrokenConfigurationError, HitDiscordLimitsError
from core.error.error_reply import send_error
from core.global_enum import ConfigurationNameEnum, CollectionEnum, DBKeyWrapperEnum
from mongo.temp_channels import TempChannels, TempChannel
from mongo.primitive_mongo_data import PrimitiveMongoData


class Locker:
    lock = Lock()

    @classmethod
    async def __aenter__(cls):
        await cls.lock.acquire()

    @classmethod
    async def __aexit__(cls, exc_type, exc_val, exc_tb):
        cls.lock.release()


class TmpChannelUtil:

    @staticmethod
    async def get_server_objects(guild: Guild,
                                 name_format: str,
                                 member: Union[Member, User],
                                 db: TempChannels) -> TempChannel:
        """
        Creates a new tmp_channel voice and text channel, saves it and places it correctly.

        Args:
            category_key: The category under which the chat should appear.

            guild: The server on which the bot is.

            name_format: The format string for the name of the channels

            member: The User creating this channel

            db: The database connection to be used.

        Returns:
            A TempChannel or StudyChannel which contains the created pair.

        Raises:
            Forbidden,ServerSelectionTimeoutError
        """
        if len(guild.channels) + 2 > GLOBAL_CHANNEL_LIMIT:
            raise HitDiscordLimitsError("Hit server channel limit", "you can do nothing about this")

        channel_category: CategoryChannel = member.voice.channel.category

        if len(channel_category.channels) + 2 > CATEGORY_CHANNEL_LIMIT:
            raise HitDiscordLimitsError("To many temporary channels",
                                        "Try to create a channel later or report it to a moderator")

        if name_format.format(0) != name_format:
            i = 1
            channels = {channel.name for channel in channel_category.voice_channels}
            while name_format.format(i) in channels:
                i += 1
            name = name_format.format(i)
        else:
            name = name_format

        key = ConfigurationNameEnum.STUDENTY.value
        verified = guild.get_role(
            (await PrimitiveMongoData(CollectionEnum.ROLES).find_one({key: {"$exists": True}}))[key])

        if not verified:
            raise BrokenConfigurationError(CollectionEnum.ROLES.value, ConfigurationNameEnum.STUDENTY.value)

        key = ConfigurationNameEnum.FRIEND.value
        friend = guild.get_role(
            (await PrimitiveMongoData(CollectionEnum.ROLES).find_one({key: {"$exists": True}}))[key])

        if not friend:
            raise BrokenConfigurationError(CollectionEnum.ROLES.value, ConfigurationNameEnum.FRIEND.value)

        key = ConfigurationNameEnum.MODERATOR_ROLE.value
        moderator = guild.get_role(
            (await PrimitiveMongoData(CollectionEnum.ROLES).find_one({key: {"$exists": True}}))[key])

        if not moderator:
            raise BrokenConfigurationError(CollectionEnum.ROLES.value, ConfigurationNameEnum.MODERATOR_ROLE.value)

        overwrites = channel_category.overwrites
        overwrites[member] = PermissionOverwrite(view_channel=True)
        if moderator in member.roles:
            try:
                overwrites.pop(moderator)
            except KeyError:
                pass
        text_channel: TextChannel = await guild.create_text_channel(name=name,
                                                                    category=channel_category,
                                                                    overwrites=overwrites,
                                                                    nsfw=False,
                                                                    topic=f"Owner: {member.display_name}",
                                                                    reason="")

        overwrites = channel_category.overwrites
        overwrites[member] = PermissionOverwrite(view_channel=True, connect=True)
        overwrites[verified] = PermissionOverwrite(view_channel=True, connect=True)
        overwrites[friend] = PermissionOverwrite(view_channel=True, connect=True)
        if moderator in member.roles:
            try:
                overwrites.pop(moderator)
            except KeyError:
                pass

        # noinspection PyBroadException
        try:
            key = ConfigurationNameEnum.TMP_STUDENTY.value
            tmp_verified = guild.get_role(
                (await PrimitiveMongoData(CollectionEnum.ROLES).find_one({key: {"$exists": True}}))[key])

            if tmp_verified:
                overwrites[tmp_verified] = PermissionOverwrite(view_channel=True, connect=True)
        except Exception:
            pass

        voice_channel: VoiceChannel = await guild.create_voice_channel(name=name,
                                                                       category=channel_category,
                                                                       overwrites=overwrites,
                                                                       nsfw=False,
                                                                       reason="")

        # TODO: check for persistence
        entry: TempChannel = await db.insert_one(
            (member, text_channel, voice_channel, TmpChannelUtil.create_token(), True, None)
        )

        # noinspection PyBroadException
        try:
            await member.move_to(voice_channel, reason="Create Tmp Channel")
        except Exception:
            pass

        await TmpChannelUtil.make_welcome_embed(entry)
        return entry

    # noinspection PyArgumentEqualDefault
    @staticmethod
    async def make_welcome_embed(document: TempChannel):
        embed = Embed(title="Your tmpc channel",
                      description="Here you can find all commands that you can use to manage your channel:")
        if document.persist:
            embed.add_field(name="Make Channel persistent:",
                            value="With"
                                  "```!tmpc keep```"
                                  "and"
                                  "```!tmpc release```"
                                  "you can make your channel persistent or not even after everyone has left the VC for "
                                  "a certain amount of time.",
                            inline=True)
        embed.add_field(name="Hide/Show channel:",
                        value="With"
                              "```!tmpc hide```"
                              "and"
                              "```!tmpc show```"
                              "you can hide or show your channel to non invited member.",
                        inline=True)
        embed.add_field(name="(Un)Lock channel:",
                        value="With"
                              "```!tmpc lock```"
                              "and"
                              "```!tmpc unlock```"
                              "you can lock or unlock so that non invited member can't join the VC but will still be "
                              "able to see you.",
                        inline=True)
        embed.add_field(name="Show token:",
                        value="With"
                              "```!tmpc token show```"
                              "the bot will post the join token of the channel.",
                        inline=True)
        embed.add_field(name="Place token in channel:",
                        value="By using"
                              "```!tmpc token place```"
                              "in a channel of your choice you can place a handy dandy embed with which members can "
                              "easily join this channel.",
                        inline=True)
        embed.add_field(name="Generate new token:",
                        value="With"
                              "```!tmpc token gen```"
                              "you can generate a new token for this channel in case the token got leaked.",
                        inline=True)
        embed.add_field(name="Kick user:",
                        value="With"
                              "```!tmpc kick <@user>```"
                              "you can remove a user from the list of users that can still join/see the channels after"
                              "you used tmpc hide of tmpc lock.",
                        inline=True)
        embed.add_field(name="Mod only command:",
                        value="With"
                              "```!tmpc nomod```"
                              "a moderator can toggle, that other moderators are not treated in a special way for the "
                              "visibility of the channel.",
                        inline=True)
        embed.add_field(name="Rename channel:",
                        value="With"
                              "```!tmpc rename <name>```"
                              "you can rename this channel.",
                        inline=True)
        embed.add_field(name="Delete channel:",
                        value="With"
                              "```!tmpc delete```"
                              "you can force delete this channel even if someone is currently in the voice chat.",
                        inline=True)
        embed.add_field(name="Restrictions:",
                        value="All commands except `tmpc token place` and `tmpc join <token>` need to be written in "
                              "this channel.",
                        inline=False)
        embed.add_field(name="Join this channel:",
                        value=f"With `!tmpc join {document.token}` members can join this channel even when locked.",
                        inline=False)
        embed.add_field(name="Invite member",
                        value="With `!tmpc invite <true|false> <@members>` "
                              "you can add up to ten members to the channel.",
                        inline=True)
        embed.add_field(name="Leave channel",
                        value="With `!tmpc leave` you can leave the channel.\n"
                              "The owner will not be able to invite you after that. ",
                        inline=True)
        await document.chat.send(content=document.owner.mention, embed=embed)

    @staticmethod
    async def update_category_and_voice_channel(value: int,
                                                ctx: Context,
                                                db: PrimitiveMongoData,
                                                key: ConfigurationNameEnum,
                                                msg: str):
        """
        Updates a db entry.
        """
        find = {key.value: {"$exists": True}}
        if await db.find_one(find):
            await db.update_one(find, {key.value: value})
        else:
            await db.insert_one({key.value: value})
        embed = Embed(title="Tmp channels",
                      description=f"Set {msg} successfully!")
        await ctx.reply(embed=embed)

    @staticmethod
    def create_token() -> int:
        secret = pyotp.random_base32()
        totp = pyotp.TOTP(secret)
        return int(totp.now())

    @staticmethod
    async def check_delete_channel(voice_channel: VoiceChannel, db: TempChannels,
                                   logger: logging.Logger,
                                   reset_delete_at: tuple[bool, PrimitiveMongoData] = (False, None)) -> bool:
        if len({member for member in voice_channel.members if not member.bot}) == 0:
            document: list[TempChannel] = await db.find(
                {DBKeyWrapperEnum.VOICE.value: voice_channel.id})

            if not document:
                return True

            document: TempChannel = document[0]

            if document.voice is None and document.chat is None:
                return True

            if type(document) == TempChannel or not document.deleteAt or (
                    not reset_delete_at[0] and datetime.now() > document.deleteAt):
                try:
                    await document.voice.delete(reason="No longer used")
                except NotFound:
                    pass
                try:
                    await document.chat.delete(reason="No longer used")
                except NotFound:
                    pass

                for message in document.messages:
                    try:
                        await message.delete()
                    except NotFound:
                        pass

                await db.delete_one({DBKeyWrapperEnum.ID.value: document.id})

                logger.info(f"Deleted Tmp Study Channel {voice_channel.name}")
                return True
            elif reset_delete_at[0] and document.deleteAt:

                key = ConfigurationNameEnum.DEFAULT_KEEP_TIME.value
                time_difference: tuple[int, int] = (await reset_delete_at[1].find_one({key: {"$exists": True}}))[
                    key]

                new_deadline = datetime.now() + timedelta(hours=time_difference[0], minutes=time_difference[1])

                document.deleteAt = new_deadline
                await db.update_one({DBKeyWrapperEnum.CHAT.value: document.channel_id}, document.document)

                diff: timedelta = document.deleteAt - datetime.now()
                if diff.seconds / 60 > 10 or datetime.now() > document.deleteAt:
                    await document.chat.edit(
                        topic=f"Owner: {document.owner.display_name}\n"
                              f"- This channel will be deleted at {document.deleteAt.strftime('%d.%m.%y %H:%M')} "
                              f"{datetime.now().astimezone().tzinfo}")
        return False

    @staticmethod
    async def joined_voice_channel(db: TempChannels, channels: set[VoiceChannel],
                                   voice_channel: VoiceChannel, join_voice_channel: VoiceChannel, guild: Guild,
                                   default_channel_name: str, member: Union[Member, User],
                                   logger: logging.Logger, bot: Bot):
        async with Locker():
            try:
                if voice_channel is join_voice_channel:  # TODO: make this to a set
                    temp_channel: list[TempChannel] = await db.find({DBKeyWrapperEnum.OWNER.value: member.id})
                    my_channel: set[TempChannel] = {channel for channel in temp_channel
                                                    if channel.voice.category.id == member.voice.channel.category.id}
                    if my_channel:
                        channel: TempChannel = my_channel.pop()
                        await member.move_to(channel.voice, reason="Member has already a temp channel in this category")
                        return

                    channels.add((await TmpChannelUtil.get_server_objects(guild,
                                                                          default_channel_name, member, db)).voice)
                    logger.info(f"Created Tmp Channel with the name '{voice_channel.name}'")

                if voice_channel in channels:
                    document: list[TempChannel] = await db.find(
                        {DBKeyWrapperEnum.VOICE.value: voice_channel.id})

                    if not document:
                        await TmpChannelUtil.database_illegal_state(bot, voice_channel, logger)
                        return

                    document: TempChannel = document[0]
                    await document.chat.set_permissions(member, view_channel=True)
                    await document.voice.set_permissions(member, view_channel=True, connect=True)
            except HitDiscordLimitsError as e:
                bot_chats = set()
                await assign_accepted_chats(bot, bot_chats)
                for chat in bot_chats:
                    chat: TextChannel
                    if member in chat.members:
                        await send_error(chat, "CreateTempChannel", e.cause, e.solution, member)

    @staticmethod
    async def ainit_helper(bot: Bot, db: TempChannels,
                           config_db: PrimitiveMongoData, join_voice_channel: Placeholder,
                           category: ConfigurationNameEnum, join_channel: ConfigurationNameEnum,
                           default_name_key: ConfigurationNameEnum,
                           default_channel_name: str) -> tuple[set[VoiceChannel], str]:
        await assign_category(bot, category)
        join_voice_channel.item = await assign_chat(bot, join_channel)

        default_channel_name_tmp = await config_db.find_one({default_name_key.value: {"$exists": True}})
        if default_channel_name_tmp:
            default_channel_name = default_channel_name_tmp[default_name_key.value]
        else:
            await config_db.insert_one({default_name_key.value: default_channel_name})

        deleted_channels: list[TempChannel] = [document for document in await db.find({}) if
                                               not document.voice or not document.chat]
        for deleted in deleted_channels:
            await db.delete_one({DBKeyWrapperEnum.ID.value: deleted._id})

        return {document.voice for document in await db.find({})}, default_channel_name

    @staticmethod
    async def database_illegal_state(bot: Bot, wrong_voice_channel: VoiceChannel, logger: logging.Logger):
        bot_channel = await assign_chat(bot, ConfigurationNameEnum.DEBUG_CHAT)
        embed = Embed(title=f"Error occurred for {wrong_voice_channel.mention}")
        embed.add_field(name="Cause", value="The database is in an illegal state", inline=False)
        embed.add_field(name="Solution",
                        value="This should never happen.",
                        inline=False)
        await bot_channel.send(embed=embed)
        logger.error(f"The Database is in an Illegal State while checking voice channel {wrong_voice_channel.id}")
