from core.global_enum import CollectionEnum
from mongo.mongo_collection import MongoCollection


class PrimitiveMongoData(MongoCollection):

    def __init__(self, collection: CollectionEnum, database: str = None):
        # noinspection PyTypeChecker
        super().__init__(collection.value, database)

    async def insert_one(self, document: dict) -> dict:
        await self.collection.insert_one(document)
        return await self.find_one(document)

    async def find_one(self, find_params: dict) -> dict:
        result = await self.collection.find_one(find_params)
        return result if result else dict()

    async def find(self, find_params: dict, sort: dict = None, limit: int = None) -> list[dict]:
        if sort:
            cursor = self.collection.find(find_params).sort(self)
        else:
            cursor = self.collection.find(find_params)

        result = [d for d in await cursor.to_list(limit)]
        return result

    async def update_one(self, find_params: dict, replace: dict):
        await self.collection.update_one(find_params, {"$set": replace})
        document = find_params.copy()
        document.update(replace)
        return await self.find_one(document)

    async def replace_one(self, old: dict, new: dict) -> dict:
        await self.collection.replace_one(old, new)
        return await self.find_one(new)
