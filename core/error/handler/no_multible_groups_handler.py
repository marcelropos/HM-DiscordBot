from logging import Logger
from typing import Callable

from core.error.error_collection import NoMultipleGroupsError
from core.error.handler.base_handler import BaseHandler
from core.logger import get_discord_child_logger


class NoMultipleGroupsHandler(BaseHandler):
    error: NoMultipleGroupsError

    @staticmethod
    def handles_type():
        return NoMultipleGroupsError

    @property
    def cause(self) -> str:
        return f'You may only belong to one group, but you already assigned to {self.error.role.mention}.'

    @property
    async def solution(self) -> str:
        return f"Ask an Admin to reassign you."

    @property
    def logger(self) -> Callable[[str], Logger]:
        return get_discord_child_logger
