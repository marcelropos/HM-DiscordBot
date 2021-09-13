from logging import Logger
from typing import Callable

from core.error.error_collection import CantAssignToSubject
from core.error.handler.base_handler import BaseHandler
from core.logger import get_discord_child_logger


class CantAssignToSubjectHandler(BaseHandler):
    error: CantAssignToSubject

    @staticmethod
    def handles_type():
        return CantAssignToSubject

    @property
    def cause(self) -> str:
        return "Didn't find wanted Subject"

    @property
    async def solution(self) -> str:
        return "If you think this subject should exist or you should be able to assign yourself to it " \
               "please contact an admin."

    @property
    def logger(self) -> Callable[[str], Logger]:
        return get_discord_child_logger
