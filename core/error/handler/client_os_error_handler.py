from logging import Logger
from typing import Callable

from aiohttp import ClientOSError

from core.error.handler.base_handler import BaseHandler
from core.logger import get_discord_child_logger


class DefaultHandler(BaseHandler):
    error: ClientOSError

    @staticmethod
    def handles_type():
        return ClientOSError

    @property
    def cause(self) -> str:
        return self.error.args[0]

    @property
    async def solution(self) -> str:
        return f"Read cause and fix it!"

    @property
    def logger(self) -> Callable[[str], Logger]:
        return get_discord_child_logger
