from logging import Logger
from typing import Callable

from bson.errors import InvalidDocument

from core.error.handler.base_handler import BaseHandler
from core.logger import get_mongo_child_logger


class InvalidDocumentHandler(BaseHandler):
    error: InvalidDocument

    @staticmethod
    def handles_type():
        return InvalidDocument

    @property
    def cause(self) -> str:
        return self.error.args[0]

    @property
    async def solution(self) -> str:
        return "Use a string"

    @property
    def logger(self) -> Callable[[str], Logger]:
        return get_mongo_child_logger
