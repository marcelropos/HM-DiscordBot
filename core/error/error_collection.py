from core.globalEnum import CollectionEnum, SubjectsOrGroupsEnum


class ManPageNotFound(Exception):
    pass


class CouldNotEditEntryError(Exception):
    def __init__(self, collection: CollectionEnum, key: str, value: str = "<value>"):
        self.collection = collection
        self.key = key
        self.value = value


class GroupOrSubjectNotFoundError(Exception):
    def __init__(self, group: str, _type: SubjectsOrGroupsEnum):
        self.group = group
        self._type = _type
