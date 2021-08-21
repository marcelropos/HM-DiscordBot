from logging import Logger
from typing import Callable

from core.error.error_collection import FailedToGrantRoleError
from core.error.handler.base_handler import BaseHandler
from core.logger import get_discord_child_logger


class NoMultipleGroupsHandler(BaseHandler):
    error: FailedToGrantRoleError

    @staticmethod
    def handles_type():
        return FailedToGrantRoleError

    @property
    def cause(self) -> str:
        return f'<@{self.error.member.id}> is already assigned to role <@&{self.error.role.id}>.'

    @property
    async def solution(self) -> str:
        return f"Ask an Admin to reassign <@{self.error.member.id}>."

    @property
    def logger(self) -> Callable[[str], Logger]:
        return get_discord_child_logger
