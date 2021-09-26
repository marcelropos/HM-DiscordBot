from datetime import datetime
from distutils.util import strtobool
from typing import Union

from discord import Embed, Guild, Member, Role, TextChannel, User
from discord.ext.commands import Cog, Bot, BadArgument, has_guild_permissions
from discord.ext.commands import group, Context

from core.error.error_collection import CouldNotEditEntryError
from core.global_enum import CollectionEnum
from core.logger import get_discord_child_logger
# noinspection PyUnresolvedReferences
from mongo.primitive_mongo_data import PrimitiveMongoData

logger = get_discord_child_logger("mongo")
collection_enum = []


class Mongo(Cog):
    """
    Accesses and modifies primitive data collections.
    """

    def __init__(self, bot: Bot):
        global collection_enum
        self.bot: Bot = bot
        collection_enum = [e.value for e in CollectionEnum]

    @group(pass_context=True,
           brief="Accesses and modifies primitive data collections.",
           help=f"You can modify data from the following collection with one of the subcommands.\n"
                f"{collection_enum}")
    @has_guild_permissions(administrator=True)
    async def mongo(self, ctx: Context):
        if not ctx.invoked_subcommand:
            raise BadArgument
        member: Union[Member, User] = ctx.author
        logger.info(f'User="{member.name}#{member.discriminator}({member.id})", Command="{ctx.message.content}"')

    @mongo.command(pass_context=True,
                   name="add",
                   help="Adds a key value pair to the collection.")
    async def mongo_add(self, ctx: Context, collection: CollectionEnum, key: str, *, value: str):
        """
        Adds a key value pair to the collection.

        Args:
            ctx: The command context provided by the discord.py wrapper.

            collection:  The collection (you can say a database table) which shall now contain the key value pair.

            key: The key of the pair.

            value: The value the pair.

        Replies:
            The user will receive a reply which contains representation of the data record.
        """
        converted_value = self.converter(value)
        respond = await PrimitiveMongoData(collection).insert_one({key: converted_value})

        embed = Embed(title=f"Database.{collection.value}",
                      description=f"The following data record is now saved in the database.\n"
                                  f"```\n{respond}\n```")
        await ctx.reply(embed=embed, delete_after=600)

    @mongo.command(pass_context=True,
                   name="find",
                   help="Finds a record in a specific collection.")
    async def mongo_find(self, ctx: Context, collection: CollectionEnum, key: str):
        """
        Finds a record in a specific collection.

        Args:
            ctx: The command context provided by the discord.py wrapper.

            collection: The collection (you can say a database table) which shall contain the key value pair.

            key: The key which is used to search for the record.

        Replies:
            The simple readable representation of the record or a not found message.

        """
        found = await PrimitiveMongoData(collection).find_one({key: {"$exists": True}})
        if found:

            embed = Embed(title=f"Database.{collection.value}",
                          description=f'```\n"{key}" : {self.display_value(ctx, found[key])}\n```')
        else:
            embed = Embed(title=f"Database.{collection.value}",
                          description=f"It seems that there is no such entry in this collection.\n"
                                      f"Did you choose the wrong collection?")
        await ctx.reply(embed=embed, delete_after=600)

    @mongo.command(pass_context=True,
                   name="edit",
                   brief="Edits a existing record.",
                   help="Edits a existing record.\n Throws: CouldNotEditEntryError if no entry was found to edit.")
    async def mongo_edit(self, ctx: Context, collection: CollectionEnum, key: str, *, value: str):
        """
        Edits a existing record.

        Args:
            ctx: The command context provided by the discord.py wrapper.

            collection: The collection (you can say a database table) which shall contain the key value pair.

            key: The key which es used to find the record.

            value: The replacing value.

        Replies:
            A diff which contains the old and new pair.
        """
        converted_value = self.converter(value)
        found = await PrimitiveMongoData(collection).find_one({key: {"$exists": True}})
        if found:
            await PrimitiveMongoData(collection).update_one({key: {"$exists": True}}, {key: converted_value})

            embed = Embed(title=f"Database.{collection.value}",
                          description='```diff\n'
                                      f'- "{key}" : {self.display_value(ctx, found[key])}\n'
                                      f'+ "{key}" : {self.display_value(ctx, value)}\n'
                                      f'```')
            await ctx.reply(embed=embed, delete_after=600)

        else:
            raise CouldNotEditEntryError(collection, key, value)

    @mongo.command(pass_context=True,
                   name="remove",
                   aliases=["rem", "rm"],
                   help="Removes any records which has a specific key.")
    async def mongo_remove(self, ctx: Context, collection: CollectionEnum, key: str):
        """
        Removes any records which has a specific key.

        Args:
            ctx: The command context provided by the discord.py wrapper.

            collection: The collection (you can say a database table) which shall not longer contain the key value pair.

            key: The key which shall wiped out.

        Replies:
            A message that (obviously) informs you that the records have been wiped.
        """
        await PrimitiveMongoData(collection).delete_many({key: {"$exists": True}})

        embed = Embed(title=f"Database.{collection.value}",
                      description="I do not know if such an entry was existing, if it was, it is now gone.")
        await ctx.reply(embed=embed, delete_after=600)

    def display_value(self, ctx: Context, value: Union[str, bool, datetime]) -> str:
        """
        Converts data into a simple understandable string form.

        Args:
            ctx: The command context provided by the discord.py wrapper.

            value: The value to be printed properly.

        Returns:
            The proper string.
        """
        converted_value = self.converter(value)
        if isinstance(value, str) and value.isnumeric():
            value = int(value)

        if isinstance(value, (bool, datetime)):
            value_str = str(converted_value)
        elif isinstance(value, int):
            converted_value: int
            guild: Guild = ctx.guild
            member: Member = guild.get_member(converted_value)
            role: Role = guild.get_role(converted_value)
            channel: TextChannel = guild.get_channel(converted_value)

            if member:
                value_str = f"@{member.name}#{member.discriminator}({member.id})"
            elif role:
                value_str = f"@{role.name}({role.id})"
            elif channel:
                value_str = f"#{channel.name}({channel.id})"
            else:
                value_str = converted_value
        else:
            value_str = f'"{value}"'
        return value_str

    @staticmethod
    def converter(data: Union[str, bool, int, datetime]) -> Union[str, bool, int, datetime]:
        """
        Converts text input data to storable objects and creates output text from objects.

        Text to object:
            1. Text that represents a integer value is converted to an integer.
            2. Text that represents a boolean value is converted to a boolean. (0 & 1 won't be convert to bool)
            3. Text representing a date & time is converted to a date object.

        Object to text:
            A date object is converted as a simple readable text.

        Everything else is equivalent to the input.

        Args:
            data: The string to be converted

        Returns:
            The representing Object

        """
        if isinstance(data, str):
            if data.isnumeric():
                result = int(data)
            else:
                try:
                    result = bool(strtobool(data))
                except ValueError:
                    try:
                        result = datetime.strptime(data, '%d.%m.%y %H:%M')
                    except ValueError:
                        result = data

        elif isinstance(data, datetime):
            result = data.strftime('%d.%m.%y %H:%M')
        else:
            result = data
        return result


def setup(bot: Bot):
    bot.add_cog(Mongo(bot))
