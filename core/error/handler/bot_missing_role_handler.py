from discord.ext.commands import BotMissingRole

from core.error.handler.bot_missing_permissions_handler import BotMissingPermissionsHandler


class BotMissingRoleHandler(BotMissingPermissionsHandler):
    error: BotMissingRole

    @staticmethod
    def handles_type():
        return BotMissingRole

    @property
    async def solution(self) -> str:
        return (await super().solution).replace("permission", "role")
