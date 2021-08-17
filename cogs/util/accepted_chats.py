from discord import TextChannel
from discord.ext.commands import Bot

from core.globalEnum import CollectionEnum, ConfigurationNameEnum
from mongo.primitiveMongoData import PrimitiveMongoData


async def assign_accepted_chats(bot: Bot, channels: set[TextChannel]):
    """
    Save accepted chats to a variable.

    Args:
        bot: The bot class.

        channels: A set in which the accepted chats should be stored.
    """
    channels.clear()
    db = PrimitiveMongoData(CollectionEnum.CHANNELS)
    key = ConfigurationNameEnum.BOT_COMMAND_CHAT.value
    channels.add(bot.get_channel((await db.find_one({key: {"$exists": True}}))[key]))
    key = ConfigurationNameEnum.DEBUG_CHAT.value
    channels.add(bot.get_channel((await db.find_one({key: {"$exists": True}}))[key]))
