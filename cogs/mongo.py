from discord.ext.commands import Cog, Bot
from discord.ext.commands import group, Context

from core.globalEnum import CollectionEnum
from mongo.primitiveMongoData import PrimitiveMongoData


class ModuleError(Exception):
    pass


class Mongo(Cog):

    def __init__(self, bot: Bot):
        self.bot: Bot = bot

    # Roles

    @group(pass_context=True)
    async def mongo(self, ctx: Context):
        if not ctx.invoked_subcommand:
            raise ModuleError

    @mongo.group(pass_context=True,
                 name="add")
    async def mongo_add(self, ctx: Context, collection: CollectionEnum, key: str, value: str):
        await PrimitiveMongoData(collection).insert_one({key: value})

    @mongo.group(pass_context=True,
                 name="find")
    async def mongo_find(self, ctx: Context, collection: CollectionEnum, key: str):
        found = await PrimitiveMongoData(collection).find_one({key: {"$exists": True}})

    @mongo.group(pass_context=True,
                 name="edit")
    async def mongo_edit(self, ctx: Context, collection: CollectionEnum, key: str, value: str):
        await PrimitiveMongoData(collection).update_one({key: {"$exists": True}}, {key: value})

    @mongo.group(pass_context=True,
                 name="remove",
                 aliases=["rem", "rm"])
    async def mongo_remove(self, ctx: Context, collection: CollectionEnum, key: str):
        await PrimitiveMongoData(collection).delete_one({key: {"$exists": True}})

    # Converter

    async def cog_before_invoke(self, ctx: Context):
        pass

    async def cog_after_invoke(self, ctx: Context):
        pass


def setup(bot: Bot):
    bot.add_cog(Mongo(bot))
