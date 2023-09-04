from logging import Logger
from typing import Callable

from core.error.error_collection import LeaveOwnChannelError
from core.error.handler.base_handler import BaseHandler
from core.logger import get_discord_child_logger


class LeaveOwnChannelHandler(BaseHandler):
    @staticmethod
    def handles_type():
        return LeaveOwnChannelError

    @property
    def cause(self) -> str:
        return "You try to leave you own channel."

    @property
    async def solution(self) -> str:
        return "Delete the channel if you don't want it anymore"

    @property
    def logger(self) -> Callable[[str], Logger]:
        return get_discord_child_logger
