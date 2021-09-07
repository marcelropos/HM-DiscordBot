from logging import Logger
from typing import Callable

from core.error.error_collection import LinkingNotFoundError
from core.error.handler.base_handler import BaseHandler
from core.logger import get_discord_child_logger


class GroupOrSubjectNotFoundHandler(BaseHandler):
    error: LinkingNotFoundError

    @staticmethod
    def handles_type():
        return LinkingNotFoundError

    @property
    def cause(self) -> str:
        return "Did not find the linking specified."

    @property
    async def solution(self) -> str:
        return "You can find the known linking with `!link show`"

    @property
    def logger(self) -> Callable[[str], Logger]:
        return get_discord_child_logger
