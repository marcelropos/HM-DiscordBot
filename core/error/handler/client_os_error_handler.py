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
        code = self.error.args[0]
        if code == 104:
            return "ConnectionResetError: Connection reset by peer."
        return f"ClientOSError"

    @property
    async def solution(self) -> str:
        code = self.error.args[0]
        if code == 104:
            return "Please wait a few minutes any try your command again."
        return "Please wait a few minutes any try your command again."

    @property
    def logger(self) -> Callable[[str], Logger]:
        return get_discord_child_logger
