from typing import Callable

from core.error.error_collection import YouOwnNoChannelsError
from core.error.handler.base_handler import BaseHandler
from core.logger import Logger, get_discord_child_logger


class YouOwnNoChannelsHandler(BaseHandler):
    error: YouOwnNoChannelsError

    @staticmethod
    def handles_type():
        return YouOwnNoChannelsError

    @property
    def cause(self) -> str:
        return "No temp channel in the database belongs to you."

    @property
    async def solution(self) -> str:
        return "Create a temp channel to use this command."

    @property
    def logger(self) -> Callable[[str], Logger]:
        return get_discord_child_logger
