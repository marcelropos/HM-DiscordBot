import os
from dataclasses import dataclass
from typing import Optional, Union

from discord.ext.commands import Bot

from Mongo.mongocollection import MongoCollection, MongoDocument
from discord import Member, TextChannel, VoiceChannel, User, Guild
import datetime


@dataclass
class GamingChannel(MongoDocument):
    _id: int
    owner: Union[Member, User]
    chat: TextChannel
    voice: VoiceChannel
    token: int

    @property
    def document(self):
        return {
            "_id": self._id,
            "owner": self.owner.id,
            "chat": self.chat.id,
            "voice": self.voice.id,
            "token": self.token,
        }


# noinspection DuplicatedCode
class GamingChannels(MongoCollection):
    def __init__(self, bot: Bot):
        super().__init__(os.environ["DB_NAME"], self.__class__.__name__)
        self.bot = bot

    async def _create_study_channel(self, result):
        _id, owner_id, chat_id, voice_id, token = result
        guild: Guild = self.bot.guilds[0]

        chat: TextChannel = guild.get_channel(chat_id)
        voice: VoiceChannel = guild.get_channel(voice_id)
        owner: Union[Member, User] = await guild.fetch_member(owner_id)

        return GamingChannel(_id, owner, chat, voice, token)

    async def insert_one(self,
                         entry: tuple[
                             Union[Member, User],
                             TextChannel, VoiceChannel,
                             int,
                             Optional[datetime.datetime]]) -> GamingChannel:
        owner, chat, voice, token, delete_at = entry

        document = {
            "owner": owner.id,
            "chat": chat.id,
            "voice": voice.id,
            "token": token,
        }

        await self.collection.insert_one(document)
        return await self.find_one(document)

    async def find_one(self, find_params: dict) -> GamingChannel:
        result = await self.collection.find_one(find_params)
        return await self._create_study_channel(result)

    async def find(self, find_params: dict, sort: dict = None, limit: int = None) -> list[GamingChannel]:

        if sort:
            cursor = self.collection.find(find_params).sort(self)
        else:
            cursor = self.collection.find(find_params)

        return [await self._create_study_channel(entry) for entry in await cursor.to_list(limit)]

    async def update_one(self, find_params: dict, replace: dict) -> GamingChannel:
        result = await self.collection.update_one(find_params, {"$set": replace})
        return await self._create_study_channel(result)
