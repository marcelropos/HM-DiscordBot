from logging import Logger
from typing import Callable

from core.error.error_collection import CouldNotEditEntryError
from core.error.handler.base_handler import BaseHandler
from core.global_enum import CollectionEnum
from core.logger import get_mongo_child_logger


class CouldNotEditEntryErrorHandler(BaseHandler):
    error: CouldNotEditEntryError

    @staticmethod
    def handles_type():
        return CouldNotEditEntryError

    @property
    def cause(self) -> str:
        return f'The `{self.error.collection.value}` collection does not contain the `{self.error.key}` key'

    @property
    async def solution(self) -> str:
        # noinspection PyTypeChecker
        return f"```md\n" \
               f"* Use: `!mongo add {self.error.collection.value} {self.error.key} {self.error.value}`\n" \
               f"* Try another collection\n" \
               f"* Give up and do not use this command again\n" \
               f"```\n" \
               f"You can choose between the following collections:\n" \
               f"`{sorted([e.value for e in CollectionEnum if e != self.error.collection])}`"

    @property
    def logger(self) -> Callable[[str], Logger]:
        return get_mongo_child_logger
