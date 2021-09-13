from logging import Logger
from typing import Callable

from core.error.error_collection import YouAlreadyHaveThisSubjectError
from core.error.handler.base_handler import BaseHandler
from core.logger import get_discord_child_logger


class YouAlreadyHaveThisSubjectHandler(BaseHandler):
    error: YouAlreadyHaveThisSubjectError

    @staticmethod
    def handles_type():
        return YouAlreadyHaveThisSubjectError

    @property
    def cause(self) -> str:
        return "You are already assigned to this subject."

    @property
    async def solution(self) -> str:
        return "Did you maybe mean another subject? Or maybe you wanted to remove this subject?"

    @property
    def logger(self) -> Callable[[str], Logger]:
        return get_discord_child_logger
