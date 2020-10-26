# noinspection PyUnresolvedReferences
import discord
# noinspection PyUnresolvedReferences
from discord.ext import commands
from utils import *
from enum import Enum
import re


class RoleNotFoundError(UserError):
    pass


class MultipleGroupsError(UserError):
    pass


class MultipleCoursesError(UserError):
    pass


class Course(Enum):
    INFORMATIK = "IF"
    WIRTSCHAFTSINFORMATIK = "IB"
    DATA_SCIENCE = "DC"


class StudyGroups:

    # noinspection PyMissingConstructor
    def __init__(self, course: Course, group: str):
        self.course = course
        self.group = group

    #  This will cause a bug in the second semester
    def __str__(self):
        return f"{self.course.value}1{str(self.group)}"  # IF1A


class StudyCourseConverter(discord.ext.commands.MemberConverter):

    async def convert(self, ctx, argument):
        argument = argument.upper()
        try:
            course = Course(argument[:2])
        except ValueError:
            raise commands.BadArgument("Kein valider Studiengang.")

        return course


class StudyGroupsConverter(discord.ext.commands.MemberConverter):

    async def convert(self, ctx, argument):
        argument = argument.upper()
        try:
            course = Course(argument[:2])
        except ValueError:
            raise commands.BadArgument("Kein valider Studiengang.")

        if course == Course.INFORMATIK:
            if argument[3] in ["A", "B"]:
                group = argument[3]
            else:
                raise commands.BadArgument("Keine valide Gruppe des Studienganges Informatik.")

        elif course == Course.WIRTSCHAFTSINFORMATIK:
            if argument[3] in ["A", "B", "C", "D"]:
                group = argument[3]
            else:
                raise commands.BadArgument("Keine valide Gruppe des Studienganges Wirtschaftsinformatik.")

        else:
            raise commands.BadArgument("data-Science hat keine Gruppen.")

        return StudyGroups(course, group)


# noinspection PyUnresolvedReferences
class Roles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_role(ServerRoles.HM)
    async def study(self, ctx, arg: StudyCourseConverter):
        got_roles = {role.name for role in ctx.author.roles}
        if len(got_roles.intersection(ServerRoles.ALL_COURSES)):
            raise MultipleCoursesError("Du kannst darfst nur einen Studiengang haben")

        if arg == Course.INFORMATIK:
            role = discord.utils.get(ctx.guild.roles, name=ServerRoles.INFORMATIK)

        elif arg == Course.WIRTSCHAFTSINFORMATIK:
            role = discord.utils.get(ctx.guild.roles, name=ServerRoles.WIRTSCHAFTSINFORMATIK)

        elif arg == Course.DATA_SCIENCE:
            role = discord.utils.get(ctx.guild.roles, name=ServerRoles.DATA_SCIENCE)

        else:
            print("Debug")
            return

        await ctx.author.add_roles(role)

    @commands.command()
    @commands.has_role(ServerRoles.HM)
    async def group(self, ctx, arg: StudyGroupsConverter):
        got_roles = {role.name for role in ctx.author.roles}
        if len(got_roles.intersection(ServerRoles.ALL_GROUPS)):
            raise MultipleGroupsError("Du darfst nicht mehr als einer Gruppe angehören.")

        if arg.course == Course.INFORMATIK:
            if not any((role.name == ServerRoles.INFORMATIK for role in ctx.author.roles)):
                raise RoleNotFoundError("Nicht im Studiengang Informatik. ```!help roles``` für mehr Informationen.")

        elif arg.course == Course.WIRTSCHAFTSINFORMATIK:
            if not any((role.name == ServerRoles.WIRTSCHAFTSINFORMATIK for role in ctx.author.roles)):
                raise RoleNotFoundError("Nicht im Studiengang Wirtschaftsinformatik. ```!help roles``` für mehr "
                                        "Informationen.")

        role = discord.utils.get(ctx.guild.roles, name=str(arg))
        await ctx.author.add_roles(role)

    @commands.command()
    @commands.has_role(ServerRoles.MODERATOR_ROLE_NAME)
    async def hm(self, ctx):
        msg = ctx.message.content
        matches = re.finditer(r"[0-9]+", msg)
        for match in matches:
            start, end = match.span()
            user_id = msg[start:end]
        # noinspection PyUnboundLocalVariable
        member = await ctx.guild.fetch_member(user_id)
        role = discord.utils.get(ctx.guild.roles, name=ServerRoles.HM)
        await member.add_roles(role)

    @commands.command(aliases=["nsfw-add"])
    @commands.has_role(ServerRoles.HM)
    async def nsfw_add(self, ctx):
        role = discord.utils.get(ctx.guild.roles, name=ServerRoles.NSFW)
        await ctx.author.add_roles(role)

    @commands.command(aliases=["nsfw-rem"])
    @commands.has_role(ServerRoles.HM)
    async def nsfw_rem(self, ctx):
        role = discord.utils.get(ctx.guild.roles, name=ServerRoles.NSFW)
        await ctx.author.remove_roles(role)

    @commands.command()
    @commands.has_role(ServerRoles.HM)
    async def coding(self, ctx):
        role = discord.utils.get(ctx.guild.roles, name=ServerRoles.CODEING)
        await ctx.author.add_roles(role)


def setup(bot):
    bot.add_cog(Roles(bot))
