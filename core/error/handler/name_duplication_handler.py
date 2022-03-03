from logging import Logger
from typing import Callable

from core.error.error_collection import NameDuplicationError
from core.error.handler.base_handler import BaseHandler
from core.logger import get_discord_child_logger


class NameDuplicationHandler(BaseHandler):
    error: NameDuplicationError

    @staticmethod
    def handles_type():
        return NameDuplicationError

    @property
    def cause(self) -> str:
        return f"This Guild has already a channel named `{self.error.name}`"

    @property
    async def solution(self) -> str:
        return "Try another name."

    @property
    def logger(self) -> Callable[[str], Logger]:
        return get_discord_child_logger
