from asyncio import Lock
from datetime import datetime, timedelta
from typing import Union, Optional

import pyotp
from discord import Guild, CategoryChannel, PermissionOverwrite, Member, User, TextChannel, VoiceChannel, Embed, \
    NotFound
from discord.ext.commands import Bot

from cogs.util.assign_variables import assign_chat, assign_accepted_chats
from core.discord_limits import CATEGORY_CHANNEL_LIMIT, GLOBAL_CHANNEL_LIMIT
from core.error.error_collection import BrokenConfigurationError, HitDiscordLimitsError
from core.error.error_reply import send_error
from core.global_enum import ConfigurationNameEnum, CollectionEnum, DBKeyWrapperEnum
from core.logger import get_discord_child_logger
from mongo.join_temp_channels import JoinTempChannel, JoinTempChannels
from mongo.primitive_mongo_data import PrimitiveMongoData
from mongo.temp_channels import TempChannels, TempChannel

logger = get_discord_child_logger("TempChannels")


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
    def logger():
        global logger
        return logger

    @staticmethod
    async def get_server_objects(guild: Guild,
                                 name_format: str,
                                 member: Union[Member, User],
                                 db: TempChannels,
                                 join_channel: JoinTempChannel, bot: Bot) -> TempChannel:
        """
        Creates a new tmp_channel voice and text channel, saves it and places it correctly.

        Args:
            guild: The server on which the bot is.

            name_format: The format string for the name of the channels

            member: The User creating this channel

            db: The database connection to be used.

            join_channel: The Join Channel which triggered the action

            bot: The bot instance.

        Returns:
            A TempChannel which contains the created pair.

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
            channels = {channel.name for channel in guild.channels}
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

        entry: TempChannel = await db.insert_one(
            (member, text_channel, voice_channel, TmpChannelUtil.create_token(), join_channel.persistent, None)
        )

        # noinspection PyBroadException
        try:
            await member.move_to(voice_channel, reason="Create Tmp Channel")
        except Exception:
            pass

        await TmpChannelUtil.make_welcome_embed(entry, bot)
        return entry

    # noinspection PyArgumentEqualDefault
    @staticmethod
    async def make_welcome_embed(document: TempChannel, bot: Bot):
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
        embed.add_field(name="Join this channel:",
                        value=f"With `!tmpc join {document.token}` members can join this channel even when locked.\n"
                              f"This command must be used in a bot command chat or via dm to {bot.user.mention}.",
                        inline=False)
        embed.add_field(name="Invite member",
                        value="With `!tmpc invite <@members>` "
                              "you can add up to ten members to the channel.\n"
                              "This command must be used in a bot command chat.",
                        inline=True)
        embed.add_field(name="Leave channel",
                        value="With `!tmpc leave` you can leave the channel.\n"
                              "The owner will not be able to invite you after that. ",
                        inline=True)
        embed.add_field(name="Restrictions:",
                        value="As long as nothing is specified, all commands must be written to this chat.",
                        inline=False)
        await document.chat.send(content=document.owner.mention, embed=embed)

    @staticmethod
    def create_token() -> int:
        secret = pyotp.random_base32()
        totp = pyotp.TOTP(secret)
        return int(totp.now())

    @staticmethod
    async def check_delete_channel(voice_channel: Optional[VoiceChannel], db: TempChannels,
                                   reset_delete_at: tuple[bool, PrimitiveMongoData] = (False, None)) -> bool:

        try:
            if len({member for member in voice_channel.members if not member.bot}) != 0:
                return True

            document: TempChannel = await db.find_one({DBKeyWrapperEnum.VOICE.value: voice_channel.id})
        except AttributeError:
            return True

        if not document:
            return True

        async with Locker():

            if document.voice is None or document.chat is None:
                return await TmpChannelUtil.delete_channel(db, document)

            if not document.deleteAt or (not reset_delete_at[0] and datetime.now() > document.deleteAt):
                return await TmpChannelUtil.delete_channel(db, document)

            if reset_delete_at[0] and document.deleteAt:
                await TmpChannelUtil.update_channel_deadline(db, document, reset_delete_at)

        return False

    @staticmethod
    async def update_channel_deadline(db, document, reset_delete_at):
        key = ConfigurationNameEnum.DEFAULT_KEEP_TIME.value
        time_difference: tuple[int, int] = (await reset_delete_at[1].find_one({key: {"$exists": True}}))[key]
        new_deadline = datetime.now() + timedelta(hours=time_difference[0], minutes=time_difference[1])
        document.deleteAt = new_deadline
        await db.update_one({DBKeyWrapperEnum.CHAT.value: document.channel_id}, document.document)
        diff: timedelta = document.deleteAt - datetime.now()
        if diff.seconds / 60 > 10 or datetime.now() > document.deleteAt:
            await document.chat.edit(
                topic=f"Owner: {document.owner.display_name}\n"
                      f"- This channel will be deleted at {document.deleteAt.strftime('%d.%m.%y %H:%M')} "
                      f"{datetime.now().astimezone().tzinfo}")

    @staticmethod
    async def delete_channel(db, document) -> bool:
        try:
            await document.voice.delete(reason="No longer used")
        except (NotFound, AttributeError):
            pass
        try:
            await document.chat.delete(reason="No longer used")
        except (NotFound, AttributeError):
            pass
        for message in document.messages:
            try:
                await message.delete()
            except (NotFound, AttributeError):
                pass
        await db.delete_one({DBKeyWrapperEnum.ID.value: document.id})
        try:
            logger.info(f"Deleted Tmp Study Channel {document.voice.name}")
        except AttributeError:
            logger.info("Delete a channel that no longer exists on the server.")
        return True

    @staticmethod
    async def joined_voice_channel(db: TempChannels, channels: set[VoiceChannel],
                                   voice_channel: VoiceChannel, guild: Guild,
                                   member: Union[Member, User],
                                   bot: Bot, join_db: JoinTempChannels):
        async with Locker():
            # noinspection PyBroadException
            try:
                join_channel: Optional[JoinTempChannel] = await join_db.find_one(
                    {DBKeyWrapperEnum.VOICE.value: voice_channel.id})
                if join_channel:
                    logger.info(
                        f'User="{member.name}#{member.discriminator}({member.id})" joinChannel="{voice_channel.name}"')
                    temp_channel: list[TempChannel] = await db.find({DBKeyWrapperEnum.OWNER.value: member.id})
                    my_channel: set[TempChannel] = {channel for channel in temp_channel
                                                    if channel.voice.category.id == member.voice.channel.category.id}
                    if my_channel:
                        channel: TempChannel = my_channel.pop()
                        await member.move_to(channel.voice, reason="Member has already a temp channel in this category")
                        return

                    channels.add((await TmpChannelUtil.get_server_objects(guild,
                                                                          join_channel.default_channel_name, member, db,
                                                                          join_channel, bot)).voice)
                    logger.info(f"Created Tmp Channel with the name '{voice_channel.name}'")

                if voice_channel in channels:
                    document: Optional[TempChannel] = await db.find_one(
                        {DBKeyWrapperEnum.VOICE.value: voice_channel.id})

                    if not document:
                        await TmpChannelUtil.database_illegal_state(bot, voice_channel)
                        return

                    logger.info(
                        f'User="{member.name}#{member.discriminator}({member.id})" tempChannel="{voice_channel.name}"')
                    reason = "Joined TempChannel"
                    if not document.chat.overwrites_for(member).view_channel:
                        await document.chat.set_permissions(member, view_channel=True, reason=reason)
                    if not (document.voice.overwrites_for(member).view_channel and document.voice.overwrites_for(
                            member).connect):
                        await document.voice.set_permissions(member, view_channel=True, connect=True, reason=reason)
            except HitDiscordLimitsError as e:
                bot_chats = set()
                await assign_accepted_chats(bot, bot_chats)
                for chat in bot_chats:
                    chat: TextChannel
                    if member in chat.members:
                        await send_error(chat, "CreateTempChannel", e.cause, e.solution, member)
            except Exception as e:
                logger.exception("Unhandled exception during channel creation occurred!")
                bot_chats = set()
                await assign_accepted_chats(bot, bot_chats)
                for chat in bot_chats:
                    chat: TextChannel
                    if member in chat.members:
                        await send_error(chat, "CreateTempChannel", str(e), "Notify the administrator", member)

    @staticmethod
    async def ainit_helper(db: TempChannels) -> set:

        deleted_channels: list[TempChannel] = [document for document in await db.find({}) if
                                               not document.voice or not document.chat]
        for deleted in deleted_channels:
            await db.delete_one({DBKeyWrapperEnum.ID.value: deleted.id})

        return {document.voice for document in await db.find({})}

    @staticmethod
    async def database_illegal_state(bot: Bot, wrong_voice_channel: VoiceChannel):
        bot_channel = await assign_chat(bot, ConfigurationNameEnum.DEBUG_CHAT)
        embed = Embed(title=f"Error occurred for {wrong_voice_channel.mention}")
        embed.add_field(name="Cause", value="The database is in an illegal state", inline=False)
        embed.add_field(name="Solution",
                        value="This should never happen.",
                        inline=False)
        await bot_channel.send(embed=embed)
        logger.error(f"The Database is in an Illegal State while checking voice channel {wrong_voice_channel.id}")
