from logging import Logger
from typing import Callable

from core.error.error_collection import YouNeedAStudyGroupError
from core.error.handler.base_handler import BaseHandler
from core.logger import get_discord_child_logger


class BotMissingPermissionsHandler(BaseHandler):
    error: YouNeedAStudyGroupError

    @staticmethod
    def handles_type():
        return YouNeedAStudyGroupError

    @property
    def cause(self) -> str:
        return "You didn't take a study course."

    @property
    async def solution(self) -> str:
        return 'Execute the `!study` command first.'

    @property
    def logger(self) -> Callable[[str], Logger]:
        return get_discord_child_logger
