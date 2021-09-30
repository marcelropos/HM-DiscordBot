from discord.ext.commands import BotMissingAnyRole

from core.error.handler.bot_missing_role_handler import MissingRoleHandler


class BotMissingAnyRoleHandler(MissingRoleHandler):
    error: BotMissingAnyRole

    @staticmethod
    def handles_type():
        return BotMissingAnyRole
