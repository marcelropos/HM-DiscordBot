from logging import Logger
from typing import Callable

from core.error.error_collection import IsAlreadyAJoinChannelError
from core.error.handler.base_handler import BaseHandler
from core.logger import get_discord_child_logger


class DefaultHandler(BaseHandler):
    error: IsAlreadyAJoinChannelError

    @staticmethod
    def handles_type():
        return IsAlreadyAJoinChannelError

    @property
    def cause(self) -> str:
        return f"{self.error.channel.mention} is already a join channel."

    @property
    async def solution(self) -> str:
        return f"Edit {self.error.channel.mention} instead."

    @property
    def logger(self) -> Callable[[str], Logger]:
        return get_discord_child_logger
