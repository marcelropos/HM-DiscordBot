from logging import Logger
from typing import Callable

from core.error.error_collection import HitDiscordLimitsError
from core.error.handler.base_handler import BaseHandler
from core.logger import get_discord_child_logger


class HitDiscordLimitsHandler(BaseHandler):
    error: HitDiscordLimitsError

    @staticmethod
    def handles_type():
        return HitDiscordLimitsError

    @property
    def cause(self) -> str:
        return self.error.cause

    @property
    async def solution(self) -> str:
        return self.error.solution

    @property
    def logger(self) -> Callable[[str], Logger]:
        return get_discord_child_logger
