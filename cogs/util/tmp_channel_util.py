from typing import Union

import pyotp
from discord import Guild, CategoryChannel, PermissionOverwrite, Member, User, TextChannel, VoiceChannel, Embed
from discord.ext.commands import Context

from core.global_enum import ConfigurationNameEnum, CollectionEnum
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

        overwrites = {member: PermissionOverwrite(view_channel=True),
                      verified: PermissionOverwrite(view_channel=True),
                      moderator: PermissionOverwrite(view_channel=True),
                      guild.default_role: PermissionOverwrite(view_channel=False)}

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
