from dataclasses import dataclass
from typing import Optional, Any

from discord import Role, Guild
from discord.ext.commands import Bot

from core.global_enum import DBKeyWrapperEnum, CollectionEnum
from mongo.mongo_collection import MongoDocument, MongoCollection


@dataclass(frozen=True)
class AlumniRole(MongoDocument):
    _id: int
    role: Role

    @property
    def document(self) -> dict[str: Any]:
        return {
            DBKeyWrapperEnum.ID.value: self._id,
            DBKeyWrapperEnum.ROLE.value: self.role.id
        }


class AlumniRoles(MongoCollection):
    def __init__(self, bot: Bot):
        # noinspection PyTypeChecker
        super().__init__(CollectionEnum.ALUMNI_ROLES.value)
        self.bot = bot

    def __contains__(self, item):
        raise NotImplementedError("Use await contains() instead!")

    async def contains(self, subject: AlumniRole) -> bool:
        return True if await self.find_one(subject.document) else False

    async def _create_document(self, result) -> Optional[AlumniRole]:
        if result:
            guild: Guild = self.bot.guilds[0]
            return AlumniRole(result[DBKeyWrapperEnum.ID.value],
                              guild.get_role(int(result[DBKeyWrapperEnum.ROLE.value])))

    async def insert_one(self, role: Role) -> AlumniRole:
        document = {
            DBKeyWrapperEnum.ROLE.value: role.id
        }
        await self.collection.insert_one(document)
        return await self.find_one(document)

    async def find_one(self, find_params: dict) -> Optional[AlumniRole]:
        result = await self.collection.find_one(find_params)
        return await self._create_document(result)

    async def find(self, find_params: dict, sort: dict = None, limit: int = None) -> list[AlumniRole]:
        cursor = self.collection.find(find_params)
        if sort:
            cursor = cursor.sort(sort)

        return [await self._create_document(entry) for entry in await cursor.to_list(limit)]

    async def update_one(self, find_params: dict, replace: dict) -> AlumniRole:
        await self.collection.update_one(find_params, {"$set": replace})
        document = find_params.copy()
        document.update(replace)
        return await self.find_one(document)
