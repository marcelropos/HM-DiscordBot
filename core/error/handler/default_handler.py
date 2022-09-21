from logging import Logger
from typing import Callable

from core.error.error_collection import HasNoHandlerException
from core.error.handler.base_handler import BaseHandler
from core.logger import get_discord_child_logger


class DefaultHandler(BaseHandler):
    error: HasNoHandlerException

    @staticmethod
    def handles_type():
        return HasNoHandlerException

    @property
    def cause(self) -> str:
        handler = get_discord_child_logger("DefaultHandler")
        handler.error(f"{self.error.args}\n{self.error.__cause__}\n{self.error.__context__}")
        return self.error.args[0]

    @property
    async def solution(self) -> str:
        return f"Attention {type(self.error).__name__} has no handler, please contact the admin about this."

    @property
    def logger(self) -> Callable[[str], Logger]:
        return get_discord_child_logger
