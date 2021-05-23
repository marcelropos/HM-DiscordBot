from typing import Union

import discord
from discord import User, Message
from discord.ext import commands
from discord.ext.commands import Context, Bot
from discord.member import Member
from discord.role import Role

from settings_files._global import ServerIds, ServerRoles, Messages
from settings_files.all_errors import *
from utils.embed_generator import EmbedGenerator
from utils.logbot import LogBot
from utils.utils import accepted_channels, extract_id, has_not_roles, has_not_role


class Roles(commands.Cog):
    """Manage your roles"""

    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.command(description="Join your course and study group to get all the relevant chats and notifications.",
                      brief="Course of study & Study group",
                      aliases=["study"]
                      )
    @commands.guild_only()
    @commands.has_role(ServerIds.HM)
    @has_not_roles(ServerRoles.ALL_GROUPS)
    async def group(self, ctx: Context, group: str, member: str):
        # member is only defined for pretty-help module. And it will be replaced later.
        await accepted_channels(self.bot, ctx)

        message: Message = ctx.message
        assert isinstance(ctx, Context), f"Expected {type(Context)} but got {type(ctx)}"
        assert isinstance(group, str), f"Expected {type(str)} but got {type(group)}"
        assert isinstance(member, str), f"Expected {type(str)} but got {type(member)}"
        assert isinstance(message, Message), f"Expected {type(Message)} but got {type(message)}"

        try:
            member: Member = message.mentions.pop()
            assert isinstance(member, Member), f"Expected {type(Member)} but got {type(member)}"
        except Exception:
            raise MissingRequiredArgument

        got_roles = {role.name for role in member.roles}
        group = group.upper()

        if not len({group}.intersection(ServerRoles.ALL_GROUPS)):
            raise RoleNotFoundError(Messages.ROLE_NOT_FOUND.format(sorted(list(ServerRoles.ALL_GROUPS))))

        if len(got_roles.intersection(ServerRoles.ALL_GROUPS)):
            raise MultipleGroupsError(f"@{member.nick if member.nick else member.name} is already a member of "
                                      f"`{got_roles.intersection(ServerRoles.ALL_GROUPS).pop()}`")
        else:

            try:
                if int(group[2]) > 1:
                    for x in ctx.author.roles:
                        if ServerIds.MODERATOR == x.id:
                            break
                    else:
                        raise MissingRole(ServerIds.MODERATOR)
            except ValueError as error:
                raise IncorrectBotConfigurationException(error)

            verified = discord.utils.get(ctx.guild.roles, id=ServerIds.HM)
            if not isinstance(verified, Role):
                raise IncorrectBotConfigurationException("Need the correct id for the verified role.")

            role_name = group
            course = discord.utils.get(ctx.guild.roles, name=role_name)
            if not isinstance(course, Role):
                raise IncorrectServerConfigurationException(
                    Messages.ROLE_NOT_ASSIGNED_ON_SERVER.format(role_name))

            role_name = group[:3]
            course_group = discord.utils.get(ctx.guild.roles, name=role_name)
            if not isinstance(course, Role):
                raise IncorrectServerConfigurationException(
                    Messages.ROLE_NOT_ASSIGNED_ON_SERVER.format(role_name))

            await member.add_roles(verified, reason=f"request by {str(ctx.author)}")
            await member.add_roles(course, reason=f"request by {str(ctx.author)}")
            await member.add_roles(course_group, reason=f"request by {str(ctx.author)}")

    @commands.command(description="As a moderator you can verify a user.",
                      brief="Verify a user",
                      aliases=[]
                      )
    @commands.guild_only()
    @commands.has_role(ServerIds.MODERATOR)
    async def hm(self, ctx: Context, user: str):
        if not isinstance(ctx, Context):
            raise ValueError(Messages.Expected_BUT_GOT.format(type(Context), type(ctx)))
        if not isinstance(user, str):
            raise ValueError(Messages.Expected_BUT_GOT.format(type(str), type(user)))
        await accepted_channels(self.bot, ctx)

        user_id = extract_id(user)
        try:
            member = await ctx.guild.fetch_member(user_id)
        except HTTPException:
            raise IncorrectUserInputError("Can not fetch user, please try to tag the user.\n"
                                          "Please notify the staff if this error still occurs.")
        assert isinstance(member, Member)

        role = discord.utils.get(ctx.guild.roles, id=ServerIds.HM)
        if not isinstance(role, Role):
            raise IncorrectBotConfigurationException(f"Need the correct id for the verified role.")

        no_hm = discord.utils.get(ctx.guild.roles, id=ServerIds.NOHM)
        assert no_hm is None or isinstance(no_hm, Role)

        await member.add_roles(role, reason=f"request by {str(ctx.author)}")
        if no_hm:
            await member.remove_roles(no_hm, reason=f"request by {str(ctx.author)}")

    # ===================Not Safe For Work=================== #

    @commands.command(name="nsfw-add",
                      help="Add nsfw role")
    @commands.guild_only()
    @commands.has_role(ServerIds.HM)
    @has_not_role(ServerIds.NSFW)
    async def nsfw_add(self, ctx: Context):
        await accepted_channels(self.bot, ctx)
        role = discord.utils.get(ctx.guild.roles, id=ServerIds.NSFW)
        await ctx.author.add_roles(role, reason="request by user")

    @commands.command(name="nsfw-rem",
                      help="Remove nsfw role")
    @commands.guild_only()
    @commands.has_role(ServerIds.NSFW)
    async def nsfw_rem(self, ctx: Context):
        await accepted_channels(self.bot, ctx)
        role = discord.utils.get(ctx.guild.roles, id=ServerIds.NSFW)
        await ctx.author.remove_roles(role, reason="request by user")

    # ===================News=================== #

    @commands.command(name="news-add",
                      help="Add news role")
    @commands.guild_only()
    @commands.has_role(ServerIds.HM)
    @has_not_role(ServerIds.NEWS)
    async def news_add(self, ctx: Context):
        await accepted_channels(self.bot, ctx)
        role = discord.utils.get(ctx.guild.roles, id=ServerIds.NEWS)
        await ctx.author.add_roles(role, reason="request by user")

    @commands.command(name="news-rem",
                      help="Remove news role")
    @commands.guild_only()
    @commands.has_role(ServerIds.NEWS)
    async def news_rem(self, ctx: Context):
        await accepted_channels(self.bot, ctx)
        role = discord.utils.get(ctx.guild.roles, id=ServerIds.NEWS)
        await ctx.author.remove_roles(role, reason="request by user")

    # ===================Coding=================== #

    @commands.command(name="coding-add",
                      help="Add coding role")
    @commands.guild_only()
    @commands.has_role(ServerIds.HM)
    @has_not_role(ServerIds.CODEING)
    async def coding_add(self, ctx: Context):
        await accepted_channels(self.bot, ctx)
        role = discord.utils.get(ctx.guild.roles, id=ServerIds.CODEING)
        await ctx.author.add_roles(role, reason="request by user")

    @commands.command(name="coding-rem",
                      help="Remove coding role")
    @commands.guild_only()
    @commands.has_role(ServerIds.CODEING)
    async def coding_rem(self, ctx: Context):
        await accepted_channels(self.bot, ctx)
        role = discord.utils.get(ctx.guild.roles, id=ServerIds.CODEING)
        await ctx.author.remove_roles(role, reason="request by user")

    @staticmethod
    async def member_converter(ctx: Context, member_id: str) -> Union[Member, User]:
        if not isinstance(ctx, Context):
            raise ValueError(Messages.Expected_BUT_GOT.format(type(Context), type(ctx)))
        if member_id is not None and not isinstance(member_id, str):
            raise ValueError(Messages.Expected_BUT_GOT.format(type(str), type(member_id)))
        if member_id:
            user_id = extract_id(member_id)
            member = await ctx.guild.fetch_member(user_id)
        else:
            member = ctx.author
        assert isinstance(member, Member)
        return member

    @group.error
    @coding_add.error
    @coding_rem.error
    @nsfw_add.error
    @nsfw_rem.error
    @news_add.error
    @news_rem.error
    @hm.error
    async def roles_error_handler(self, ctx: Context, error):
        if isinstance(error, CommandInvokeError):
            error = error.original

        if isinstance(error, RoleNotFoundError):
            embed = EmbedGenerator("roles")
            await ctx.reply(content=f"<@!{ctx.author.id}>\n"
                                    f"{error}",
                            embed=embed.generate(),
                            delete_after=60)

        elif isinstance(error, MultipleGroupsError):
            await ctx.message.delete(delay=60)
            await ctx.reply(f"<@!{ctx.author.id}>\n"
                            f"{error}",
                            delete_after=60)

        elif isinstance(error, MissingRequiredArgument):
            await ctx.reply(f"<@!{ctx.author.id}>\n"
                            f"Apparently, the command was not complete.\n",
                            delete_after=60)
        # must be last check
        elif isinstance(error, CheckFailure):
            await ctx.message.delete(delay=60)
            await ctx.reply(f"You have a role that causes that you can't actually execute this command.\n"
                            f"Make a request for this in <#{ServerIds.HELP}>.\n"
                            f"Below you will find a list of commands that are currently available to you.",
                            delete_after=60)
            await ctx.send_help("Roles")

        elif isinstance(error, global_only_handled_errors()):
            pass

        else:
            LogBot.logger.warning("There are some unhandled exceptions.")


def setup(bot: Bot):
    bot.add_cog(Roles(bot))
