from discord.ext.commands import BadBoolArgument

from core.error.handler.bad_argument_handler import BadArgumentHandler


class BadBoolArgumentHandler(BadArgumentHandler):
    error: BadBoolArgument

    @staticmethod
    def handles_type():
        return BadBoolArgument

    @property
    async def solution(self) -> str:
        return "Please use 'true' or 'false' if you need to supply a truth value."
