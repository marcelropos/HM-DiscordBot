from logging import Logger
from typing import Callable

from core.error.error_collection import GroupOrSubjectNotFoundError
from core.error.handler.base_handler import BaseHandler
from core.logger import get_discord_child_logger


class GroupOrSubjectNotFoundHandler(BaseHandler):
    error: GroupOrSubjectNotFoundError

    @staticmethod
    def handles_type():
        return GroupOrSubjectNotFoundError

    @property
    def cause(self) -> str:
        return "Did not find the " + self.error.type.name + " specified: " + self.error.group

    @property
    async def solution(self) -> str:
        return f"Tag a Role that is a " + self.error.type.name

    @property
    def logger(self) -> Callable[[str], Logger]:
        return get_discord_child_logger
