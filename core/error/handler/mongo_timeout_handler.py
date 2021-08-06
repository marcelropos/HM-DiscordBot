from logging import Logger
from typing import Callable

from pymongo.errors import ServerSelectionTimeoutError

from core.error.handler.base_handler import BaseHandler
from core.logger import get_mongo_child_logger


class MongoTimeoutHandler(BaseHandler):

    @staticmethod
    def handles_type():
        return ServerSelectionTimeoutError

    @property
    def cause(self) -> str:
        return "Could not connect to the database."

    @property
    async def solution(self) -> str:
        return "Report this error to the server admin immediately!"

    @property
    def logger(self) -> Callable[[str], Logger]:
        return get_mongo_child_logger
