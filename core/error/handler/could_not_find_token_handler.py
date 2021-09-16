from logging import Logger
from typing import Callable

from core.error.error_collection import CouldNotFindToken
from core.error.handler.base_handler import BaseHandler
from core.logger import get_discord_child_logger


class CouldNotFindTokenHandler(BaseHandler):
    error: CouldNotFindToken

    @staticmethod
    def handles_type():
        return CouldNotFindToken

    @property
    def cause(self) -> str:
        return "Could not find Token"

    @property
    async def solution(self) -> str:
        return f"Check if you gave the correct Token. If this problem persist contact the admin"

    @property
    def logger(self) -> Callable[[str], Logger]:
        return get_discord_child_logger
