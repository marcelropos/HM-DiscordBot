import logging
from datetime import datetime, timedelta
from typing import Union

import pyotp
from discord import Guild, CategoryChannel, PermissionOverwrite, Member, User, TextChannel, VoiceChannel, Embed, \
    NotFound
from discord.ext.commands import Context, Bot

from cogs.util.assign_variables import assign_category, assign_chat
from cogs.util.placeholder import Placeholder
from core.error.error_collection import BrokenConfigurationError
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

        if not verified:
            raise BrokenConfigurationError(CollectionEnum.ROLES.value, ConfigurationNameEnum.STUDENTY.value)

        key = ConfigurationNameEnum.FRIEND.value
        friend = guild.get_role(
            (await PrimitiveMongoData(CollectionEnum.ROLES).find_one({key: {"$exists": True}}))[key])

        if not friend:
            raise BrokenConfigurationError(CollectionEnum.ROLES.value, ConfigurationNameEnum.FRIEND.value)

        overwrites = channel_category.overwrites
        overwrites[member] = PermissionOverwrite(view_channel=True)

        text_channel: TextChannel = await guild.create_text_channel(name=name,
                                                                    category=channel_category,
                                                                    overwrites=overwrites,
                                                                    nsfw=False,
                                                                    reason="")

        overwrites = channel_category.overwrites
        overwrites[member] = PermissionOverwrite(view_channel=True, connect=True)
        overwrites[verified] = PermissionOverwrite(view_channel=True, connect=True)
        overwrites[friend] = PermissionOverwrite(view_channel=True, connect=True)

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

        await TmpChannelUtil.make_welcome_embed(entry)
        return entry

    @staticmethod
    async def make_welcome_embed(document: Union[GamingChannel, StudyChannel]):
        embed = Embed(title="Your tmpc channel",
                      description="Here you can find all commands that you can use to manage your channel:")
        if type(document) is StudyChannel:
            embed.add_field(name="Make Channel persistent:",
                            value="With"
                                  "```!tmpc keep```"
                                  "you can make your channel stay even after everyone has left the VC for a certain "
                                  "amount of time. To turn it off just do the same command.",
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
        embed.add_field(name="Send token to user:",
                        value="With"
                              "```!tmpc token send {@user}```"
                              "you can send the token directly to a member.",
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
        embed.add_field(name="Mod only command:",
                        value="With"
                              "```!tmpc nomod```"
                              "a moderator set that other moderators are not treated in a special way for the "
                              "visibility of the channel.",
                        inline=True)
        embed.add_field(name="Restrictions:",
                        value="All commands except `tmpc token place` and `tmpc join {token}` need to be written in "
                              "this channel.",
                        inline=True)
        embed.add_field(name="Join this channel:",
                        value=f"With `!tmpc join {document.token}` members can join this channel even when locked.",
                        inline=False)
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
