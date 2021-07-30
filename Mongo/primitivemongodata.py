import os

from Mongo.mongocollection import MongoCollection


class PrimitiveMongoData(MongoCollection):

    def __init__(self, collection):
        super().__init__(os.environ["DB_NAME"], collection)

    async def insert_one(self, document: dict) -> dict:
        return await self.collection.insert_one(document)

    async def find_one(self, find_params: dict) -> dict:
        return await self.collection.find_one(find_params)

    async def find(self, find_params: dict, sort: dict = None, limit: int = None) -> list[dict]:
        if sort:
            cursor = self.collection.find(find_params).sort(self)
        else:
            cursor = self.collection.find(find_params)

        result = [d for d in await cursor.to_list(limit)]
        return result

    async def update_one(self, find_params: dict, replace: dict) -> dict:
        return await self.collection.update_one(find_params, {"$set": replace})

    async def replace_one(self, old: dict, new: dict):
        return await self.collection.replace_one(old, new)
