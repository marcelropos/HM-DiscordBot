import datetime
import typing
from dataclasses import dataclass
from typing import Optional, Union

from discord import Member, TextChannel, VoiceChannel, User, Guild
from discord.ext.commands import Bot

from core.globalEnum import CollectionEnum, ConfigurationNameEnum, ConfigurationAttributeEnum, DBKeyWrapperEnum
from mongo.mongoCollection import MongoCollection, MongoDocument
from mongo.primitiveMongoData import PrimitiveMongoData


@dataclass
class StudyChannel(MongoDocument):
    _id: int
    owner: Union[Member, User]
    chat: TextChannel
    voice: VoiceChannel
    token: int
    deleteAt: datetime

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
    def voice_member(self) -> set[Union[Member, User]]:
        return {member for member in self.voice.members if not member.bot}

    @property
    def document(self) -> dict[str: typing.Any]:
        return {
            DBKeyWrapperEnum.ID.value: self._id,
            DBKeyWrapperEnum.OWNER.value: self.owner.id,
            DBKeyWrapperEnum.CHAT.value: self.chat.id,
            DBKeyWrapperEnum.VOICE.value: self.voice.id,
            DBKeyWrapperEnum.TOKEN.value: self.token,
            DBKeyWrapperEnum.DELETE_AT.value: self.deleteAt
        }


class StudyChannels(MongoCollection):
    def __init__(self, bot: Bot):
        super().__init__(self.__class__.__name__)
        self.bot = bot

    async def _create_study_channel(self, result):
        _id, owner_id, chat_id, voice_id, token, delete_at = result
        guild: Guild = self.bot.guilds[0]
        chat: TextChannel = guild.get_channel(chat_id)
        voice: VoiceChannel = guild.get_channel(voice_id)
        owner: Union[Member, User] = await guild.fetch_member(owner_id)

        return StudyChannel(_id, owner, chat, voice, token, delete_at)

    async def insert_one(self, entry: tuple[Union[Member, User],
                                            TextChannel, VoiceChannel,
                                            int,
                                            Optional[datetime.datetime]]) -> StudyChannel:
        owner, chat, voice, token, delete_at = entry

        hours = await PrimitiveMongoData.find_configuration(CollectionEnum.ROLES_SETTINGS,
                                                            ConfigurationNameEnum.DELETE_AFTER,
                                                            ConfigurationAttributeEnum.HOURS)

        document = {
            DBKeyWrapperEnum.OWNER.value: owner.id,
            DBKeyWrapperEnum.CHAT.value: chat.id,
            DBKeyWrapperEnum.VOICE.value: voice.id,
            DBKeyWrapperEnum.TOKEN.value: token,
            DBKeyWrapperEnum.DELETE_AT.value:
                delete_at if delete_at else datetime.datetime.now() + datetime.timedelta(hours=hours)
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
