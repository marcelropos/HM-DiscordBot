import time

from discord.ext.commands import Bot, Cog

from core.logger import get_discord_child_logger

listener = Cog.listener


class BotStatus(Cog):
    """Cogs for bot status callbacks

    This class contains listener for callbacks that are directly related to the Bot.
    """

    def __init__(self, bot: Bot):
        """
        Args:
            bot: the bot Object
        """
        self.bot = bot

    @listener()
    async def on_ready(self):
        if len(self.bot.guilds) > 1:
            self.bot_is_in_multiple_guild()
            await self.close_bot()
        elif len(self.bot.guilds) == 0:
            self.bot_is_in_no_guild()
            await self.close_bot()

    @listener()
    async def on_guild_join(self):
        self.bot_is_in_multiple_guild()
        await self.close_bot()

    @listener()
    async def on_guild_remove(self):
        self.bot_is_in_no_guild()
        await self.close_bot()

    async def close_bot(self):
        """Closes the bot"""
        await self.bot.close()
        time.sleep(1)  # this sleep is there to avoid a Exception in asyncio

    def bot_is_in_multiple_guild(self):
        """Logs that the Bot is in multiple Guilds"""
        get_discord_child_logger(self.__class__.__name__).error(
            "Bot is on multiple servers, the bot can only run on one server at a time."
            + "The Bot is on following servers: "
            + str([guild.name for guild in self.bot.guilds]))

    def bot_is_in_no_guild(self):
        """Logs that the Bot has no Guild"""
        get_discord_child_logger(self.__class__.__name__).error("Bot is on no server, the bot must run on a server.")


def setup(bot: Bot):
    """Setup this Cog for this file

    Args:
        bot: the bot Object
    """
    bot.add_cog(BotStatus(bot))
