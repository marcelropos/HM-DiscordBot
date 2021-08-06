from abc import ABC, abstractmethod
from logging import Logger
from typing import Callable
from typing import final, Union

from discord.ext.commands import Context

from core.error.error_reply import error_reply


class BaseHandler(ABC):
    __handler = set()

    def __init__(self, error, ctx: Context):
        self.error = error
        self.ctx = ctx

    @staticmethod
    @abstractmethod
    def handles_type():
        pass

    @property
    @abstractmethod
    def cause(self) -> str:
        pass

    @property
    @abstractmethod
    def solution(self) -> str:
        pass

    @property
    @abstractmethod
    def logger(self) -> Callable[[str], Logger]:
        pass

    # noinspection PyMethodMayBeStatic
    @property
    def content(self) -> Union[str, None]:
        return None

    # noinspection PyMethodMayBeStatic,PyTypeChecker
    @property
    def delete_after(self) -> Union[int, None]:
        return None

    @final
    async def handle(self):
        await error_reply(ctx=self.ctx,
                          logger=self.logger("error"),
                          cause=self.cause,
                          solution=self.solution,
                          content=self.content,
                          delete_after=self.delete_after)

    @staticmethod
    def handlers(error: Exception, ctx: Context):
        for handler in BaseHandler.__handler:
            if error.__class__ == handler.handles_type():
                return handler(error, ctx)

    def __init_subclass__(cls, **kwargs):
        cls.__handler.add(cls)
