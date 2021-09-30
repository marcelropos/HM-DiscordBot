from logging import Logger
from typing import Callable

from discord.ext.commands import MissingPermissions

from core.error.handler.base_handler import BaseHandler
from core.logger import get_discord_child_logger


class MissingPermissionsHandler(BaseHandler):
    error: MissingPermissions

    @staticmethod
    def handles_type():
        return MissingPermissions

    @property
    def cause(self) -> str:
        return self.error.args[0]

    @property
    async def solution(self) -> str:
        return f"```md\n" \
               f"* Ask yourself if you are allowed to execute this command at all:\n\n" \
               f"\tIf yes:\n" \
               f"\t\tAsk a moderator if they can give you this \n" \
               f"\t\tpermission. Otherwise ask for an admin. \n\n" \
               f"\tIf no:\n" \
               f"\t\tWhy do you use this command?! Just stop it!\n\n" \
               f"* If you can give yourself the permission, then you can solve your problem yourself.\n" \
               f"```"

    @property
    def logger(self) -> Callable[[str], Logger]:
        return get_discord_child_logger
