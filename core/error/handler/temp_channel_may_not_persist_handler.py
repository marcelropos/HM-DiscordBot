from typing import Callable

from core.error.error_collection import TempChannelMayNotPersistError
from core.error.handler.base_handler import BaseHandler
from core.logger import Logger, get_discord_child_logger


class TempChannelMayNotPersistHandler(BaseHandler):
    error: TempChannelMayNotPersistError

    @staticmethod
    def handles_type():
        return TempChannelMayNotPersistError

    @property
    def cause(self) -> str:
        return "Your temp channel has no persistent flag"

    @property
    async def solution(self) -> str:
        return "There is nothing you can do about this.\n" \
               "Perhaps ask a moderator where you can create a channel with that flag."

    @property
    def logger(self) -> Callable[[str], Logger]:
        return get_discord_child_logger
