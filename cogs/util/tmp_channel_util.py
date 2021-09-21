import logging
from datetime import datetime, timedelta
from typing import Union

import pyotp
from discord import Guild, CategoryChannel, PermissionOverwrite, Member, User, TextChannel, VoiceChannel, Embed, \
    NotFound
from discord.ext.commands import Context, Bot

from cogs.util.assign_variables import assign_category, assign_chat
from cogs.util.placeholder import Placeholder
from core.global_enum import ConfigurationNameEnum, CollectionEnum, DBKeyWrapperEnum
from mongo.gaming_channels import GamingChannels, GamingChannel
from mongo.primitive_mongo_data import PrimitiveMongoData
from mongo.study_channels import StudyChannels, StudyChannel


class TmpChannelUtil:
    @staticmethod
    async def get_server_objects(category_key: ConfigurationNameEnum,
                                 guild: Guild,
                                 name_format: str,
                                 member: Union[Member, User],
                                 db: Union[GamingChannels, StudyChannels]) -> Union[GamingChannel, StudyChannel]:
        """
        Creates a new tmp_channel voice and text channel, saves it and places it correctly.

        Args:
            category_key: The category under which the chat should appear.

            guild: The server on which the bot is.

            name_format: The format string for the name of the channels

            member: The User creating this channel

            db: The database connection to be used.

        Returns:
            A GamingChannel or StudyChannel which contains the created pair.

        Raises:
            Forbidden,ServerSelectionTimeoutError
        """
        channel_category: CategoryChannel = guild.get_channel(
            (await PrimitiveMongoData(CollectionEnum.CATEGORIES).find_one({category_key.value: {"$exists": True}}))[
                category_key.value])

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
        key = ConfigurationNameEnum.MODERATOR_ROLE.value
        moderator = guild.get_role(
            (await PrimitiveMongoData(CollectionEnum.ROLES).find_one({key: {"$exists": True}}))[key])

        overwrites = {member: PermissionOverwrite(view_channel=True),
                      moderator: PermissionOverwrite(view_channel=True),
                      guild.default_role: PermissionOverwrite(view_channel=False)}

        text_channel: TextChannel = await guild.create_text_channel(name=name,
                                                                    category=channel_category,
                                                                    overwrites=overwrites,
                                                                    nsfw=False,
                                                                    reason="")

        overwrites = {member: PermissionOverwrite(view_channel=True, connect=True),
                      verified: PermissionOverwrite(view_channel=True, connect=True),
                      moderator: PermissionOverwrite(view_channel=True, connect=True),
                      guild.default_role: PermissionOverwrite(view_channel=False, connect=False)}

        voice_channel: VoiceChannel = await guild.create_voice_channel(name=name,
                                                                       category=channel_category,
                                                                       overwrites=overwrites,
                                                                       nsfw=False,
                                                                       reason="")

        entry: Union[GamingChannel, StudyChannel] = await db.insert_one(
            (member, text_channel, voice_channel, TmpChannelUtil.create_token(), None))

        try:
            await member.move_to(voice_channel, reason="Create Tmp Channel")
        except Exception:
            pass

        return entry

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
    async def check_delete_channel(voice_channel: VoiceChannel, db: Union[GamingChannels, StudyChannels],
                                   logger: logging.Logger, bot: Bot,
                                   reset_delete_at: tuple[bool, PrimitiveMongoData] = (False, None)) -> bool:
        if len({member for member in voice_channel.members if not member.bot}) == 0:
            document: list[Union[StudyChannel, GamingChannel]] = await db.find(
                {DBKeyWrapperEnum.VOICE.value: voice_channel.id})

            if not document:
                await TmpChannelUtil.database_illegal_state(bot, voice_channel, logger)
                return False

            document: Union[StudyChannel, GamingChannel] = document[0]

            if type(document) == GamingChannel or not document.deleteAt or (
                    not reset_delete_at[0] and datetime.now() > document.deleteAt):
                try:
                    await document.voice.delete(reason="No longer used")
                except NotFound:
                    pass
                try:
                    await document.chat.delete(reason="No longer used")
                except NotFound:
                    pass

                if type(document) == StudyChannel:
                    for message in document.messages:
                        try:
                            await message.delete()
                        except NotFound:
                            pass

                await db.delete_one({DBKeyWrapperEnum.ID.value: document._id})

                logger.info(f"Deleted Tmp Study Channel {voice_channel.name}")
                return True
            elif reset_delete_at[0] and document.deleteAt:
                key = ConfigurationNameEnum.DEFAULT_KEEP_TIME.value
                time_difference: tuple[int, int] = (await reset_delete_at[1].find_one({key: {"$exists": True}}))[key]
                document.deleteAt = datetime.now() + timedelta(hours=time_difference[0], minutes=time_difference[1])
                await db.update_one({DBKeyWrapperEnum.CHAT.value: document.channel_id}, document.document)
                embed = Embed(title="Channel Deletion",
                              description=f"This channel will be deleted "
                                          f"<t:{int(document.deleteAt.timestamp())}:R> at "
                                          f"<t:{int(document.deleteAt.timestamp())}:F>")
                await document.chat.send(embed=embed)
        return False

    @staticmethod
    async def joined_voice_channel(db: Union[GamingChannels, StudyChannels], channels: set[VoiceChannel],
                                   voice_channel: VoiceChannel, join_voice_channel: VoiceChannel, guild: Guild,
                                   default_channel_name: str, member: Union[Member, User],
                                   category: ConfigurationNameEnum, logger: logging.Logger, bot: Bot):
        if voice_channel is join_voice_channel:
            if await db.find_one({DBKeyWrapperEnum.OWNER.value: member.id}):
                return

            channels.add((await TmpChannelUtil.get_server_objects(category, guild,
                                                                  default_channel_name, member, db)).voice)
            logger.info(f"Created Tmp Channel with the name '{voice_channel.name}'")

        if voice_channel in channels:
            document: list[Union[GamingChannel, StudyChannel]] = await db.find(
                {DBKeyWrapperEnum.VOICE.value: voice_channel.id})

            if not document:
                await TmpChannelUtil.database_illegal_state(bot, voice_channel, logger)
                return

            document: Union[GamingChannel, StudyChannel] = document[0]
            await document.chat.set_permissions(member, view_channel=True)
            await document.voice.set_permissions(member, view_channel=True)

    @staticmethod
    async def ainit_helper(bot: Bot, db: Union[GamingChannels, StudyChannels],
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

        deleted_channels: list[Union[GamingChannel, StudyChannel]] = [document for document in await db.find({}) if
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
