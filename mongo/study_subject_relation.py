from dataclasses import dataclass
from typing import Optional, Any

from discord import Role, Guild
from discord.ext.commands import Bot, BadArgument

from core.global_enum import DBKeyWrapperEnum, CollectionEnum, SubjectsOrGroupsEnum
from mongo.mongo_collection import MongoDocument, MongoCollection
from mongo.subjects_or_groups import SubjectsOrGroups


@dataclass(frozen=True)
class StudySubjectRelation(MongoDocument):
    _id: int
    group: Role
    subject: Role
    default: bool

    @property
    def document(self) -> dict[str: Any]:
        return {
            DBKeyWrapperEnum.ID.value: self._id,
            DBKeyWrapperEnum.GROUP.value: self.group.id,
            DBKeyWrapperEnum.SUBJECT.value: self.subject.id,
            DBKeyWrapperEnum.DEFAULT.value: self.default
        }

    @property
    def name(self):
        return self.group.name


class StudySubjectRelations(MongoCollection):
    def __init__(self, bot: Bot):
        # noinspection PyTypeChecker
        super().__init__(CollectionEnum.GROUP_SUBJECT_RELATION.value)
        self.bot = bot

    def __contains__(self, item):
        raise NotImplementedError("Use await contains() instead!")

    async def contains(self, subject: StudySubjectRelation) -> bool:
        return True if await self.find_one(subject.document) else False

    async def _create_document(self, result) -> Optional[StudySubjectRelation]:
        if result:
            guild: Guild = self.bot.guilds[0]
            return StudySubjectRelation(result[DBKeyWrapperEnum.ID.value],
                                        guild.get_role(int(result[DBKeyWrapperEnum.GROUP.value])),
                                        guild.get_role(int(result[DBKeyWrapperEnum.SUBJECT.value])),
                                        result[DBKeyWrapperEnum.DEFAULT.value])

    async def insert_one(self, document: tuple[Role, Role, bool]) -> StudySubjectRelation:
        group, subject, default = document

        if not {_ for _ in await SubjectsOrGroups(self.bot, SubjectsOrGroupsEnum.GROUP).find({}) if
                _.role is group}:
            raise BadArgument

        if not {_ for _ in await SubjectsOrGroups(self.bot, SubjectsOrGroupsEnum.SUBJECT).find({}) if _.role is subject}:
            raise BadArgument

        document = {
            DBKeyWrapperEnum.GROUP.value: group.id,
            DBKeyWrapperEnum.SUBJECT.value: subject.id,
            DBKeyWrapperEnum.DEFAULT.value: default
        }
        await self.collection.insert_one(document)
        return await self.find_one(document)

    async def find_one(self, find_params: dict) -> Optional[StudySubjectRelation]:
        result = await self.collection.find_one(find_params)
        return await self._create_document(result)

    async def find(self, find_params: dict, sort: dict = None, limit: int = None) -> list[StudySubjectRelation]:
        cursor = self.collection.find(find_params)
        if sort:
            cursor = cursor.sort(sort)

        return [await self._create_document(entry) for entry in await cursor.to_list(limit)]

    async def update_one(self, find_params: dict, replace: dict) -> StudySubjectRelation:
        await self.collection.update_one(find_params, {"$set": replace})
        document = find_params.copy()
        document.update(replace)
        return await self.find_one(document)
