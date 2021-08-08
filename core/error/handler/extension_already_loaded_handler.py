from logging import Logger
from typing import Callable

from discord.ext.commands import ExtensionAlreadyLoaded

from core.error.handler.base_handler import BaseHandler
from core.logger import get_discord_child_logger


class ExtensionAlreadyLoadedHandler(BaseHandler):
    error: ExtensionAlreadyLoaded

    @staticmethod
    def handles_type():
        return ExtensionAlreadyLoaded

    @property
    def cause(self) -> str:
        return self.error.args[0]

    @property
    async def solution(self) -> str:
        return f"You can reload the cog if you want, or just be happy that the cog is already active."

    @property
    def logger(self) -> Callable[[str], Logger]:
        return get_discord_child_logger
