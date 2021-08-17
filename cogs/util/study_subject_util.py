from discord import CategoryChannel, Role, PermissionOverwrite, TextChannel, Guild, Embed
from discord.ext.commands import Context

from core.globalEnum import CollectionEnum, ConfigurationNameEnum
from mongo.primitiveMongoData import PrimitiveMongoData
from mongo.subjectsorgroups import SubjectOrGroup, SubjectsOrGroups


class StudySubjectUtil:
    @staticmethod
    async def get_server_objects(category_key: ConfigurationNameEnum,
                                 guild: Guild,
                                 name: str,
                                 separator_key: ConfigurationNameEnum,
                                 db: SubjectsOrGroups) -> SubjectOrGroup:
        study_category: CategoryChannel = guild.get_channel(
            (await PrimitiveMongoData(CollectionEnum.CATEGORIES)
             .find_one({category_key.value: {"$exists": True}}))[category_key.value])

        study_separator: Role = guild.get_role(
            (await PrimitiveMongoData(CollectionEnum.ROLES)
             .find_one({separator_key.value: {"$exists": True}}))[separator_key.value])

        role: Role = await guild.create_role(name=name,
                                             reason="")

        overwrites = {role: PermissionOverwrite(read_messages=True)}
        channel: TextChannel = await guild.create_text_channel(name=name,
                                                               category=study_category,
                                                               overwrites=overwrites,
                                                               nsfw=False,
                                                               reason="")
        entry: SubjectOrGroup = await db.insert_one((channel, role))
        await entry.role.edit(position=study_separator.position - 1)

        return entry

    @staticmethod
    async def update_category_and_separator(value: int,
                                            ctx: Context,
                                            db: PrimitiveMongoData,
                                            key: ConfigurationNameEnum,
                                            msg: str):
        find = {key.value: {"$exists": True}}
        if await db.find_one(find):
            await db.update_one(find, {key.value: value})
        else:
            await db.insert_one({key.value: value})
        embed = Embed(title="Study Groups",
                      description=f"Set {msg} successfully!")
        await ctx.reply(embed=embed)
