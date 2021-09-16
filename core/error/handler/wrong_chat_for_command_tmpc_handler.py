from logging import Logger
from typing import Callable

from core.error.error_collection import WrongChatForCommandTmpc
from core.error.handler.base_handler import BaseHandler
from core.logger import get_discord_child_logger


class WrongChatForCommandTmpcHandler(BaseHandler):
    error: WrongChatForCommandTmpc

    @staticmethod
    def handles_type():
        return WrongChatForCommandTmpc

    @property
    def cause(self) -> str:
        return "Can't use this tmpc command outside of the tmpc chat"

    @property
    async def solution(self) -> str:
        return f"You can only use this command inside the text chat created with the study or gaming voice chat"

    @property
    def logger(self) -> Callable[[str], Logger]:
        return get_discord_child_logger
