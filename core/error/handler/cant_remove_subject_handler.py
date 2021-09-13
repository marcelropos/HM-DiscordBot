from logging import Logger
from typing import Callable

from core.error.error_collection import CantRemoveSubject
from core.error.handler.base_handler import BaseHandler
from core.logger import get_discord_child_logger


class CantRemoveSubjectHandler(BaseHandler):
    error: CantRemoveSubject

    @staticmethod
    def handles_type():
        return CantRemoveSubject

    @property
    def cause(self) -> str:
        return "Can't opt-out of this subject"

    @property
    async def solution(self) -> str:
        return "Maybe you are not assigned to this subject or the role you tried to opt-out of is not a subject."

    @property
    def logger(self) -> Callable[[str], Logger]:
        return get_discord_child_logger
