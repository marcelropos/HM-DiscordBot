from logging import Logger
from typing import Callable

from discord.ext.commands import NoPrivateMessage

from core.error.handler.base_handler import BaseHandler
from core.global_enum import CollectionEnum, ConfigurationNameEnum
from core.logger import get_discord_child_logger
from mongo.primitive_mongo_data import PrimitiveMongoData


class NoPrivateMessageHandler(BaseHandler):
    error: NoPrivateMessage

    @staticmethod
    def handles_type():
        return NoPrivateMessage

    @property
    def cause(self) -> str:
        return self.error.args[0]

    @property
    async def solution(self) -> str:
        key = ConfigurationNameEnum.BOT_COMMAND_CHAT.value
        channel = await PrimitiveMongoData(CollectionEnum.CHANNELS).find_one(
            {key: {"$exists": True}})
        return f"Use the <#{channel[key]}> Chat for your command."

    @property
    def logger(self) -> Callable[[str], Logger]:
        return get_discord_child_logger
