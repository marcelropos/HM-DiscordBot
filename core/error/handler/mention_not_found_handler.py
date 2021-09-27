from logging import Logger
from typing import Callable

from core.error.error_collection import MentionNotFoundError
from core.error.handler.base_handler import BaseHandler
from core.logger import get_discord_child_logger


class MentionNotFoundHandler(BaseHandler):
    error: MentionNotFoundError

    @staticmethod
    def handles_type():
        return MentionNotFoundError

    @property
    def cause(self) -> str:
        return f"Cant find a {self.error.want} with the following name {self.error.mention}"

    @property
    async def solution(self) -> str:
        return "1. Use the following format? `@<user/role>`?\n" \
               "2. Check if a role is expected and you have passed a member.\n" \
               "3. Check if a member is expected and you have passed a role."

    @property
    def logger(self) -> Callable[[str], Logger]:
        return get_discord_child_logger
