from logging import Logger
from typing import Callable

from core.error.error_collection import NoBotChatError
from core.error.handler.base_handler import BaseHandler
from core.logger import get_discord_child_logger


class BadArgumentHandler(BaseHandler):
    error: NoBotChatError

    @staticmethod
    def handles_type():
        return NoBotChatError

    @property
    def cause(self) -> str:
        return f'You may not use this command in this channel.'

    @property
    async def solution(self) -> str:
        channels = ""
        for channel in self.error.channels:
            channels += f"<#{channel.id}>\n"
        return f"This command may only be used in the following chats:\n" \
               f"{channels}" \
               f"If you do not have access to any of these chats, please ask for support."

    @property
    def logger(self) -> Callable[[str], Logger]:
        return get_discord_child_logger
