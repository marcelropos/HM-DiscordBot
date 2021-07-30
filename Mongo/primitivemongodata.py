import os
import typing

from Mongo.mongocollection import MongoCollection
from core.globalenum import CollectionEnum


class PrimitiveMongoData(MongoCollection):

    def __init__(self, collection):
        super().__init__(os.environ["DB_NAME"], collection)

    async def insert_one(self, document: dict) -> dict:
        return await self.find_one(document)

    async def find_one(self, find_params: dict) -> dict:
        return await self.collection.find_one(find_params)

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

    @staticmethod
    async def find_configuration(collection: CollectionEnum, key: str, attribute: str) -> typing.Any:
        result = await PrimitiveMongoData(collection.value).find_one({key: {'$exists': True}})
        if result:
            return result[attribute]
