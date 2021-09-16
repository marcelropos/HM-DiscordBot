import datetime
import typing
from dataclasses import dataclass
from typing import Optional, Union

from discord import Member, TextChannel, VoiceChannel, User, Guild
from discord.ext.commands import Bot

from core.global_enum import DBKeyWrapperEnum, CollectionEnum
from mongo.mongo_collection import MongoCollection, MongoDocument


@dataclass
class GamingChannel(MongoDocument):
    _id: int
    owner: Union[Member, User]
    chat: TextChannel
    voice: VoiceChannel
    token: int

    @property
    def owner_id(self) -> int:
        return self.owner.id

    @property
    def voice_id(self) -> int:
        return self.voice.id

    @property
    def channel_id(self) -> int:
        return self.chat.id

    @property
    def document(self) -> dict[str: typing.Any]:
        return {
            DBKeyWrapperEnum.ID.value: self._id,
            DBKeyWrapperEnum.OWNER.value: self.owner.id,
            DBKeyWrapperEnum.CHAT.value: self.chat.id if self.chat else None,
            DBKeyWrapperEnum.VOICE.value: self.voice.id if self.voice else None,
            DBKeyWrapperEnum.TOKEN.value: self.token,
        }


class GamingChannels(MongoCollection):
    def __init__(self, bot: Bot):
        super().__init__(CollectionEnum.GAMING_CHANNELS.value)
        self.bot = bot

    async def _create_gaming_channel(self, result):
        if result:
            guild: Guild = self.bot.guilds[0]
            return GamingChannel(result[DBKeyWrapperEnum.ID.value],
                                 await guild.fetch_member(result[DBKeyWrapperEnum.OWNER.value]),
                                 guild.get_channel(result[DBKeyWrapperEnum.CHAT.value]),
                                 guild.get_channel(result[DBKeyWrapperEnum.VOICE.value]),
                                 result[DBKeyWrapperEnum.TOKEN.value])

    async def insert_one(self, entry: tuple[Union[Member, User],
                                            TextChannel, VoiceChannel,
                                            int,
                                            Optional[datetime.datetime]]) -> GamingChannel:
        owner, chat, voice, token, delete_at = entry

        document = {
            DBKeyWrapperEnum.OWNER.value: owner.id,
            DBKeyWrapperEnum.CHAT.value: chat.id,
            DBKeyWrapperEnum.VOICE.value: voice.id,
            DBKeyWrapperEnum.TOKEN.value: token,
        }

        await self.collection.insert_one(document)
        return await self.find_one(document)

    async def find_one(self, find_params: dict) -> GamingChannel:
        result = await self.collection.find_one(find_params)
        return await self._create_gaming_channel(result)

    async def find(self, find_params: dict, sort: dict = None, limit: int = None) -> list[GamingChannel]:
        cursor = self.collection.find(find_params)
        if sort:
            cursor = cursor.sort(self)

        return [await self._create_gaming_channel(entry) for entry in await cursor.to_list(limit)]

    async def update_one(self, find_params: dict, replace: dict) -> GamingChannel:
        await self.collection.update_one(find_params, {"$set": replace})
        document = find_params.copy()
        document.update(replace)
        return await self.find_one(document)
