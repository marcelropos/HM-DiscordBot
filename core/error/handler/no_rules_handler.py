from logging import Logger
from typing import Callable

from core.error.error_collection import NoRulesError
from core.error.handler.base_handler import BaseHandler
from core.logger import get_discord_child_logger


class NoRulesHandler(BaseHandler):

    @staticmethod
    def handles_type():
        return NoRulesError

    @property
    def cause(self) -> str:
        return f"Rules not available."

    @property
    async def solution(self) -> str:
        return f"This error should only happen shortly after startup, " \
               f"if you try again after a minute you should have no problems.\n" \
               f"If the error occurs even then, please report it immediately to the admin."

    @property
    def logger(self) -> Callable[[str], Logger]:
        return get_discord_child_logger
