from discord.ext.commands import BotMissingRole

from core.error.handler.missing_permissions_handler import MissingPermissionsHandler


class MissingRoleHandler(MissingPermissionsHandler):
    error: BotMissingRole

    @staticmethod
    def handles_type():
        return BotMissingRole
