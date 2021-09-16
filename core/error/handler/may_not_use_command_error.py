from collections import Callable

from logging import Logger
from core.error.error_collection import MayNotUseCommandError
from core.error.handler.base_handler import BaseHandler
from core.logger import get_discord_child_logger


class MayNotUseCommandHandler(BaseHandler):
    error: MayNotUseCommandError

    @staticmethod
    def handles_type():
        return MayNotUseCommandError

    @property
    def cause(self) -> str:
        return "You tried using a command that you don't have permission to use"

    @property
    async def solution(self) -> str:
        return "If you think you should be able to use this command please contact the admin"

    @property
    def logger(self) -> Callable[[str], Logger]:
        return get_discord_child_logger