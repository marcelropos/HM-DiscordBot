import typing
from dataclasses import dataclass
from typing import Optional

from discord import VoiceChannel, Guild
from discord.ext.commands import Bot

from core.global_enum import DBKeyWrapperEnum, CollectionEnum
from mongo.mongo_collection import MongoDocument, MongoCollection


@dataclass
class JoinTempChannel(MongoDocument):
    voice: VoiceChannel
    default_channel_name: str
    persistent: bool

    def document(self) -> dict[str: typing.Any]:
        return {
            DBKeyWrapperEnum.VOICE.value: self.voice.id,
            DBKeyWrapperEnum.DEFAULT_CHANNEL_NAME.value: self.default_channel_name,
            DBKeyWrapperEnum.PERSIST.value: self.persistent
        }


class JoinTempChannels(MongoCollection):
    def __init__(self, bot: Bot):
        super().__init__(CollectionEnum.JOIN_TEMP_CHANNELS.value)
        self.bot = bot

    async def _create_temp_channel(self, result) -> JoinTempChannel:
        if result:
            guild: Guild = self.bot.guilds[0]
            return JoinTempChannel(
                guild.get_channel(result[DBKeyWrapperEnum.VOICE.value]),
                result[DBKeyWrapperEnum.DEFAULT_CHANNEL_NAME.value],
                result[DBKeyWrapperEnum.PERSIST.value]
            )

    async def insert_one(self, entry: tuple[VoiceChannel, str, bool]) -> JoinTempChannel:
        voice, name, persist, = entry

        document = {
            DBKeyWrapperEnum.VOICE.value: voice.id,
            DBKeyWrapperEnum.DEFAULT_CHANNEL_NAME.value: name,
            DBKeyWrapperEnum.PERSIST.value: persist,
        }

        await self.collection.insert_one(document)
        return await self.find_one(document)

    async def find_one(self, find_params: dict) -> Optional[JoinTempChannel]:
        result = await self.collection.find_one(find_params)
        return await self._create_temp_channel(result)

    async def find(self, find_params: dict, sort: dict = None, limit: int = None) -> list[JoinTempChannel]:
        cursor = self.collection.find(find_params)
        if sort:
            cursor = cursor.sort(self)

        return [await self._create_temp_channel(entry) for entry in await cursor.to_list(limit)]

    async def update_one(self, find_params: dict, replace: dict) -> JoinTempChannel:
        await self.collection.update_one(find_params, {"$set": replace})
        document = find_params.copy()
        document.update(replace)
        return await self.find_one(document)