from logging import Logger
from typing import Callable

from core.error.error_collection import DatabaseIllegalState
from core.error.handler.base_handler import BaseHandler
from core.logger import get_mongo_child_logger


class DatabaseIllegalStateHandler(BaseHandler):
    error: DatabaseIllegalState

    @staticmethod
    def handles_type():
        return DatabaseIllegalState

    @property
    def cause(self) -> str:
        return "The database is in an illegal State"

    @property
    async def solution(self) -> str:
        return "Please contact an admin as fast as possible since this should never happen."

    @property
    def logger(self) -> Callable[[str], Logger]:
        return get_mongo_child_logger
