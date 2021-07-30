import os
import typing
from dataclasses import dataclass
from typing import Optional, Union

from discord.ext.commands import Bot

from Mongo.mongocollection import MongoCollection, MongoDocument
from discord import Member, TextChannel, VoiceChannel, User, Guild
import datetime

from Mongo.primitivemongodata import PrimitiveMongoData
from core.globalenum import CollectionEnum


@dataclass
class StudyChannel(MongoDocument):
    _id: int
    owner: Union[Member, User]
    chat: TextChannel
    voice: VoiceChannel
    token: int
    deleteAt: datetime

    @property
    def document(self) -> dict[str: typing.Any]:
        return {
            "_id": self._id,
            "owner": self.owner.id,
            "chat": self.chat.id,
            "voice": self.voice.id,
            "token": self.token,
            "deleteAt": self.deleteAt
        }


class StudyChannels(MongoCollection):
    def __init__(self, bot: Bot):
        super().__init__(os.environ["DB_NAME"], self.__class__.__name__)
        self.bot = bot

    async def _create_study_channel(self, result):
        _id, owner_id, chat_id, voice_id, token, delete_at = result
        guild: Guild = self.bot.guilds[0]
        chat: TextChannel = guild.get_channel(chat_id)
        voice: VoiceChannel = guild.get_channel(voice_id)
        owner: Union[Member, User] = await guild.fetch_member(owner_id)

        return StudyChannel(_id, owner, chat, voice, token, delete_at)

    async def insert_one(self, entry: tuple[
                             Union[Member, User],
                             TextChannel, VoiceChannel,
                             int,
                             Optional[datetime.datetime]]) -> StudyChannel:
        owner, chat, voice, token, delete_at = entry

        hours = await PrimitiveMongoData.find_configuration(CollectionEnum.ROLES_SETTINGS, "deleteAfter", "HOURS")

        document = {
            "owner": owner.id,
            "chat": chat.id,
            "voice": voice.id,
            "token": token,
            "deleteAt": delete_at if delete_at else datetime.datetime.now() + datetime.timedelta(hours=hours)
        }

        await self.collection.insert_one(document)
        return await self.find_one(document)

    async def find_one(self, find_params: dict) -> StudyChannel:
        result = await self.collection.find_one(find_params)
        return await self._create_study_channel(result)

    async def find(self, find_params: dict, sort: dict = None, limit: int = None) -> list[StudyChannel]:
        cursor = self.collection.find(find_params)
        if sort:
            cursor = cursor.sort(self)

        return [await self._create_study_channel(document) for document in await cursor.to_list(limit)]

    async def update_one(self, find_params: dict, replace: dict) -> StudyChannel:
        await self.collection.update_one(find_params, {"$set": replace})
        document = find_params.copy()
        document.update(replace)
        return await self.find_one(document)
