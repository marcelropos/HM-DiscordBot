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
        cmd: str = self.ctx.command.name
        if self.ctx.subcommand_passed:
            cmd += f" {self.ctx.subcommand_passed}"
        await self.ctx.send_help(cmd)
        return f"I have sent you a help message that describes how to correctly use the command.\n" \
               f"With {self.ctx.bot.command_prefix}help you can also see what other commands exist and how to use them."

    @property
    def logger(self) -> Callable[[str], Logger]:
        return get_mongo_child_logger
