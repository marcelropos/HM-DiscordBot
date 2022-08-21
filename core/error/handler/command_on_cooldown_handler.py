from datetime import timedelta, datetime
from logging import Logger
from typing import Callable

from discord.ext.commands import CommandOnCooldown

from core.error.handler.base_handler import BaseHandler
from core.logger import get_discord_child_logger


class CommandOnCooldownHandler(BaseHandler):
    error: CommandOnCooldown

    @staticmethod
    def handles_type():
        return CommandOnCooldown

    @property
    def cause(self) -> str:
        # The self.error.type.name works because it uses the enum Class in the background
        return f'The command limitation of `{self.error.cooldown.rate}` ' \
               f'per `{self.error.type.name}` within `{self.time(int(self.error.cooldown.per))}` was exceeded.'

    @property
    async def solution(self) -> str:
        return f"You can use this command again at " \
               f"{(datetime.now() + timedelta(seconds=self.error.retry_after)).strftime('%d.%m.%y %H:%M')}"

    @staticmethod
    def time(sec: int) -> str:
        delta = timedelta(seconds=sec)
        delta_str = str(delta)[-8:]
        hours, minutes, _ = [int(val) for val in delta_str.split(":", 3)]
        days = delta.days % 7
        return f"{days} days {hours} hours {minutes} minutes"

    @property
    def logger(self) -> Callable[[str], Logger]:
        return get_discord_child_logger
