from logging import Logger
from typing import Callable

from core.error.error_collection import NotOwnerError
from core.error.handler.base_handler import BaseHandler
from core.logger import get_discord_child_logger


class NotOwnerHandler(BaseHandler):
    error: NotOwnerError

    @staticmethod
    def handles_type():
        return NotOwnerError

    @property
    def cause(self) -> str:
        return f"You do not have the permission to execute this command."

    @property
    async def solution(self) -> str:
        user = f"Ask {self.error.owner} to execute this command.\n"
        mod = "A moderator may also allowed to use this command."
        return user + mod if self.error.is_mod else user

    @property
    def logger(self) -> Callable[[str], Logger]:
        return get_discord_child_logger
