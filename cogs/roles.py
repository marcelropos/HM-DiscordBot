# noinspection PyUnresolvedReferences
import discord
# noinspection PyUnresolvedReferences
from discord.ext import commands
from settings import Embedgenerator, BugReport, ServerIds
from utils import *
from enum import Enum
import re


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
            raise commands.BadArgument("Kein valider Studiengang."
                                       f"`!help roles` f\u00fcr mehr Informationen")

        return course


class StudyGroupsConverter(discord.ext.commands.MemberConverter):

    async def convert(self, ctx, argument):
        argument = argument.upper()
        try:
            course = Course(argument[:2])
        except ValueError:
            raise commands.BadArgument("Kein valider Studiengang."
                                       f"`!help roles` f\u00fcr mehr Informationen")

        if course == Course.INFORMATIK:
            if argument[3] in ["A", "B"]:
                group = argument[3]
            else:
                raise commands.BadArgument("Keine valide Gruppe des Studienganges Informatik."
                                           f"`!help roles` f\u00fcr mehr Informationen")

        elif course == Course.WIRTSCHAFTSINFORMATIK:
            if argument[3] in ["A", "B", "C", "D"]:
                group = argument[3]
            else:
                raise commands.BadArgument("Keine valide Gruppe des Studienganges Wirtschaftsinformatik."
                                           f"`!help roles` f\u00fcr mehr Informationen")
        else:
            raise commands.BadArgument("data-Science hat keine Gruppen."
                                       f"`!help roles` f\u00fcr mehr Informationen")
        return StudyGroups(course, group)


# noinspection PyUnresolvedReferences
class Roles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.guild_only()
    @commands.has_role(ServerIds.HM)
    async def study(self, ctx, arg: StudyCourseConverter):
        await accepted_channels(self.bot, ctx)
        got_roles = {role.name for role in ctx.author.roles}
        if len(got_roles.intersection(ServerRoles.ALL_COURSES)):
            raise MultipleCoursesError()

        if arg == Course.INFORMATIK:
            role = discord.utils.get(ctx.guild.roles, id=ServerIds.INFORMATIK)

        elif arg == Course.WIRTSCHAFTSINFORMATIK:
            role = discord.utils.get(ctx.guild.roles, id=ServerIds.WIRTSCHAFTSINFORMATIK)

        elif arg == Course.DATA_SCIENCE:
            role = discord.utils.get(ctx.guild.roles, id=ServerIds.DATA_SCIENCE)

        else:
            print("Debug")
            return

        await ctx.author.add_roles(role, reason="request by user")

    @commands.command()
    @commands.guild_only()
    @commands.has_role(ServerIds.HM)
    async def group(self, ctx, arg: StudyGroupsConverter):
        await accepted_channels(self.bot, ctx)
        got_roles = {role.name for role in ctx.author.roles}
        if len(got_roles.intersection(ServerRoles.ALL_GROUPS)):
            raise MultipleGroupsError()

        if arg.course == Course.INFORMATIK:
            if not any((role.name == ServerRoles.INFORMATIK for role in ctx.author.roles)):
                raise RoleNotFoundError()

        elif arg.course == Course.WIRTSCHAFTSINFORMATIK:
            if not any((role.name == ServerRoles.WIRTSCHAFTSINFORMATIK for role in ctx.author.roles)):
                raise RoleNotFoundError()

        role = discord.utils.get(ctx.guild.roles, name=str(arg))
        await ctx.author.add_roles(role, reason="request by user")

    @commands.command()
    @commands.guild_only()
    @commands.has_role(ServerIds.MODERATOR)
    async def hm(self, ctx):
        await accepted_channels(self.bot, ctx)
        msg = ctx.message.content
        matches = re.finditer(r"[0-9]+", msg)
        for match in matches:
            start, end = match.span()
            user_id = msg[start:end]
        # noinspection PyUnboundLocalVariable
        member = await ctx.guild.fetch_member(user_id)
        role = discord.utils.get(ctx.guild.roles, id=ServerIds.HM)
        await member.add_roles(role, reason=f"request by {str(ctx.author)}")
        # noinspection PyBroadException
        try:
            nohm = discord.utils.get(ctx.guild.roles, id=ServerIds.NOHM)
            await member.remove_roles(nohm, reason=f"request by {str(ctx.author)}")
        except Exception:
            pass

        # noinspection PyBroadException
        try:
            for x in ["help", "roles", "rules"]:
                embed = Embedgenerator(x)
                await member.send(embed=embed.generate())
            await member.send("Achte auch bitte darauf, dass du neue Nachrichten bei Mittteilungen liest. Diese sind "
                              "meist wichtig und interessant. Du findest diese ganz oben.")
        except Exception:
            pass

    @hm.error
    async def hm_errorhandler(self, ctx, error):
        if isinstance(error, MissingRole):
            await ctx.send(f"<@!{ctx.author.id}>\n"
                           f"Dieser Befehl ist Moderatoren vorbehalten.")
        else:
            error = BugReport(self.bot, ctx, e)
            error.user_details()
            await error.reply()
            raise e

    @commands.command(aliases=["nsfw-add"])
    @commands.guild_only()
    @commands.has_role(ServerIds.HM)
    async def nsfw_add(self, ctx):
        await accepted_channels(self.bot, ctx)
        role = discord.utils.get(ctx.guild.roles, id=ServerIds.NSFW)
        await ctx.author.add_roles(role, reason="request by user")

    @commands.command(aliases=["nsfw-rem"])
    @commands.guild_only()
    @commands.has_role(ServerIds.HM)
    async def nsfw_rem(self, ctx):
        await accepted_channels(self.bot, ctx)
        role = discord.utils.get(ctx.guild.roles, id=ServerIds.NSFW)
        await ctx.author.remove_roles(role, reason="request by user")

    @commands.command()
    @commands.guild_only()
    @commands.has_role(ServerIds.HM)
    async def coding(self, ctx):
        await accepted_channels(self.bot, ctx)
        role = discord.utils.get(ctx.guild.roles, id=ServerIds.CODEING)
        await ctx.author.add_roles(role, reason="request by user")

    @group.error
    @study.error
    @nsfw_add.error
    @nsfw_rem.error
    @coding.error
    async def roles_errorhanler(self, ctx, error):
        if isinstance(error, RoleNotFoundError):
            embed = Embedgenerator("roles")
            await ctx.send(content=f"<@!{ctx.author.id}>\n"
                                   f"Es ist erforderlich, dass du dich zuerst in einen Studiengang einschreibst.",
                           embed=embed.generate())

        elif isinstance(error, MultipleGroupsError) or isinstance(error, MultipleCoursesError):
            await ctx.send(f"<@!{ctx.author.id}>\n"
                           f"Es ist nicht gestattet in mehreren Gruppen oder Studieng\u00e4ngen eingeschrieben zu sein."
                           f"\n F\u00fcr eine \u00c4nderung stelle eine Anfrage in <#{ServerIds.HELP}>")

        elif isinstance(error, MissingRole):
            await ctx.send(f"<@!{ctx.author.id}>\n"
                           f"F\u00fcr diesen Befehl ist eine Verifikation erforderlich.\n"
                           f"Stelle hierzu eine Anfrage in <#{ServerIds.HELP}>.")

        elif isinstance(error, MissingRequiredArgument):
            await ctx.send(f"<@!{ctx.author.id}>\n"
                           f"Anscheinend war der Befehl nicht Volls\u00e4ndig.\n")

        elif isinstance(error, WrongChatError):
            await ctx.message.delete()
            await ctx.send(f"<@!{ctx.author.id}>\n"
                           f"Dieser Befehl darf in diesem Chat nicht verwendet werden.\n"
                           f"Nutzebitte den dafür vorgesehenen Chat <#{ServerIds.BOT_COMMANDS_CHANNEL}>.",
                           delete_after=60)
        
        elif isinstance(error, discord.ext.commands.errors.NoPrivateMessage):
            await ctx.send(f"Dieser Befehl kann nur im Chat <#{ServerIds.BOT_COMMANDS_CHANNEL}> gestellt werden.")

        elif isinstance(error, commands.BadArgument):
            await ctx.send(error)

        else:
            error = BugReport(self.bot, ctx, error)
            error.user_details()
            await error.reply()
            raise error


def setup(bot):
    bot.add_cog(Roles(bot))
