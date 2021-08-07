from logging import Logger
from typing import Callable

from discord.ext.commands import BadArgument

from core.error.handler.base_handler import BaseHandler
from core.logger import get_mongo_child_logger


class BadArgumentHandler(BaseHandler):
    error: BadArgument

    @staticmethod
    def handles_type():
        return BadArgument

    @property
    def cause(self) -> str:
        return f'At least one argument does not satisfy the conditions.'

    @property
    async def solution(self) -> str:
        # TODO: reply with the proper help message and supply the proper chat for more help
        cmd: str = self.ctx.command
        if self.ctx.subcommand_passed:
            cmd += f" {self.ctx.subcommand_passed}"
        return f"Type `{self.ctx.bot.command_prefix}help {cmd}` and read how to use this command correctly.\n" \
               f"If you still don't understand how this command works, post a request in the help chat."

    @property
    def logger(self) -> Callable[[str], Logger]:
        return get_mongo_child_logger
