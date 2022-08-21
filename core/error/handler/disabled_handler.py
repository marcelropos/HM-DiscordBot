from logging import Logger
from typing import Callable

from discord.ext.commands import DisabledCommand

from core.error.handler.base_handler import BaseHandler
from core.logger import get_discord_child_logger


class DefaultHandler(BaseHandler):
    error: DisabledCommand

    @staticmethod
    def handles_type():
        return DisabledCommand

    @property
    def cause(self) -> str:
        return self.error.args[0]

    @property
    async def solution(self) -> str:
        return f"Ask to enable this command."

    @property
    def logger(self) -> Callable[[str], Logger]:
        return get_discord_child_logger
