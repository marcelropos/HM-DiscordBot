from logging import Logger
from typing import Callable, Optional

from core.error.error_collection import MissingInteractionError
from core.error.handler.base_handler import BaseHandler
from core.logger import get_discord_child_logger


class MissingInteractionHandler(BaseHandler):
    error: MissingInteractionError

    @staticmethod
    def handles_type():
        return MissingInteractionError

    @property
    def cause(self) -> str:
        return f'Timeout during interaction'

    @property
    async def solution(self) -> str:
        return "Just repeat the command"

    @property
    def delete_after(self) -> Optional[int]:
        return None

    @property
    def logger(self) -> Callable[[str], Logger]:
        return get_discord_child_logger
