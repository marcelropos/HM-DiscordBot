from abc import ABC, abstractmethod
from logging import Logger
from typing import Callable, Optional, final

from discord import Message, NotFound
from discord.ext.commands import Context

from core.error.error_reply import error_reply


class BaseHandler(ABC):
    __handler = set()

    def __init__(self, error: Exception, ctx: Context):
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
    async def solution(self) -> str:
        pass

    @property
    @abstractmethod
    def logger(self) -> Callable[[str], Logger]:
        pass

    # noinspection PyMethodMayBeStatic
    @property
    def content(self) -> Optional[str]:
        return None

    # noinspection PyMethodMayBeStatic,PyTypeChecker
    @property
    def delete_after(self) -> Optional[int]:
        return 60

    @final
    async def handle(self):
        try:
            await error_reply(ctx=self.ctx,
                              logger=self.logger("error"),
                              cause=self.cause,
                              solution=await self.solution,
                              content=self.content,
                              delete_after=self.delete_after)
            msg: Message = self.ctx.message

            await msg.delete(delay=self.delete_after)
        except NotFound:
            pass

    @staticmethod
    def handlers(error: Exception, ctx: Context):
        for handler in BaseHandler.__handler:
            if error.__class__ == handler.handles_type():
                return handler(error, ctx)
        from core.error.handler.default_handler import DefaultHandler
        return DefaultHandler(error, ctx)

    def __init_subclass__(cls, **kwargs):
        cls.__handler.add(cls)
