import datetime
import typing
from dataclasses import dataclass
from typing import Optional, Union

from discord import Member, TextChannel, VoiceChannel, User, Guild, Message, NotFound
from discord.ext.commands import Bot

from core.global_enum import CollectionEnum, DBKeyWrapperEnum
from mongo.gaming_channels import GamingChannel
from mongo.mongo_collection import MongoCollection


@dataclass
class StudyChannel(GamingChannel):
    deleteAt: datetime
    messages: list[Message]

    @property
    def message_ids(self) -> list[int]:
        return [message.id for message in self.messages]

    @property
    def document(self) -> dict[str: typing.Any]:
        document = super(StudyChannel, self).document
        document.update(
            {DBKeyWrapperEnum.DELETE_AT.value: self.deleteAt,
             DBKeyWrapperEnum.MESSAGES.value: [(message.channel, message) for message in self.messages]})
        return document


class StudyChannels(MongoCollection):
    def __init__(self, bot: Bot):
        super().__init__(CollectionEnum.STUDY_CHANNELS.value)
        self.bot = bot

    async def _create_study_channel(self, result):
        if result:
            guild: Guild = self.bot.guilds[0]
            messages = []
            for channel, message in result[DBKeyWrapperEnum.MESSAGES.value]:
                try:
                    messages.append(await guild.get_channel(channel).fetch_message(message))
                except (NotFound, AttributeError):
                    pass
            return StudyChannel(result[DBKeyWrapperEnum.ID.value],
                                await guild.fetch_member(result[DBKeyWrapperEnum.OWNER.value]),
                                guild.get_channel(result[DBKeyWrapperEnum.CHAT.value]),
                                guild.get_channel(result[DBKeyWrapperEnum.VOICE.value]),
                                result[DBKeyWrapperEnum.TOKEN.value],
                                result[DBKeyWrapperEnum.DELETE_AT.value],
                                messages)

    async def insert_one(self, entry: tuple[Union[Member, User],
                                            TextChannel, VoiceChannel,
                                            int,
                                            Optional[datetime.datetime]]) -> StudyChannel:
        owner, chat, voice, token, delete_at = entry

        document = {
            DBKeyWrapperEnum.OWNER.value: owner.id,
            DBKeyWrapperEnum.CHAT.value: chat.id,
            DBKeyWrapperEnum.VOICE.value: voice.id,
            DBKeyWrapperEnum.TOKEN.value: token,
            DBKeyWrapperEnum.DELETE_AT.value: delete_at,
            DBKeyWrapperEnum.MESSAGES.value: list()
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
        replace[DBKeyWrapperEnum.MESSAGES.value] = [(message[0].id, message[0].id) for message in
                                                    replace[DBKeyWrapperEnum.MESSAGES.value]]
        await self.collection.update_one(find_params, {"$set": replace})
        document = find_params.copy()
        document.update(replace)
        return await self.find_one(document)
