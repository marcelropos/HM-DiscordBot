from logging import Logger
from typing import Callable

from core.error.error_collection import ManPageNotFound
from core.error.handler.base_handler import BaseHandler
from core.logger import get_discord_child_logger


class ManPageNotFoundHandler(BaseHandler):

    @staticmethod
    def handles_type():
        return ManPageNotFound

    @property
    def cause(self) -> str:
        return "The Manpage you requested could not be found"

    @property
    async def solution(self) -> str:
        return "With limited options of mine, you should probably do your own searching."

    @property
    def logger(self) -> Callable[[str], Logger]:
        return get_discord_child_logger
