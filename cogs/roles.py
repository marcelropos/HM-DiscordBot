import discord
from discord.ext import commands
from discord.ext.commands import Context, Bot
from discord.role import Role
from discord.member import Member
from utils.embed_generator import BugReport
from settings_files._global import ServerIds, ServerRoles, Messages
from utils.embed_generator import EmbedGenerator
from utils.utils import accepted_channels, extract_id
from settings_files.all_errors import *


class MissingRole(MissingRole):
    def __init__(self, missing_role):
        self.missing_role = missing_role
        CheckFailure().__init__(missing_role)


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
    async def group(self, ctx: Context, group: str, member=None):
        await accepted_channels(self.bot, ctx)
        if member:
            user_id = extract_id(member)
            member: Member = await ctx.guild.fetch_member(user_id)
        else:
            member = ctx.author
        got_roles = {role.name for role in member.roles}
        group = group.upper()
        if not len(got_roles.intersection(ServerRoles.ALL_GROUPS)):

            try:
                if int(group[2]) > 1:
                    is_mod = False
                    for x in ctx.author.roles:
                        if ServerIds.MODERATOR == x.id:
                            is_mod = True
                    if not is_mod:
                        raise MissingRole(f"Higher semesters can only be assigned by mods.")

                try:
                    role: Role = discord.utils.get(ctx.guild.roles, name=group)
                    await member.add_roles(role, reason=f"request by {str(ctx.author)}")

                    role: Role = discord.utils.get(ctx.guild.roles, name=group[:3])
                    await member.add_roles(role, reason=f"request by {str(ctx.author)}")
                except AttributeError:
                    raise RoleNotFoundError(Messages.ROLE_NOT_FOUND.format(sorted(list(ServerRoles.ALL_GROUPS))))

            except IndexError:
                raise RoleNotFoundError(Messages.ROLE_NOT_FOUND.format(sorted(list(ServerRoles.ALL_GROUPS))))
            except ValueError:
                raise RoleNotFoundError(Messages.ROLE_NOT_FOUND.format(sorted(list(ServerRoles.ALL_GROUPS))))
        else:
            if member.nick:
                name = member.nick
            else:
                name = member.name
            raise MultipleGroupsError(f"@{name} is already a member of "
                                      f"`{got_roles.intersection(ServerRoles.ALL_GROUPS).pop()}`")

    @commands.command(description="As a moderator you can verify a user.",
                      brief="Verify a user",
                      aliases=[]
                      )
    @commands.guild_only()
    @commands.has_role(ServerIds.MODERATOR)
    async def hm(self, ctx: Context, user):
        await accepted_channels(self.bot, ctx)
        user_id = extract_id(user)
        # noinspection PyUnboundLocalVariable
        member = await ctx.guild.fetch_member(user_id)
        role = discord.utils.get(ctx.guild.roles, id=ServerIds.HM)
        await member.add_roles(role, reason=f"request by {str(ctx.author)}")
        # noinspection PyBroadException
        try:
            no_hm = discord.utils.get(ctx.guild.roles, id=ServerIds.NOHM)
            await member.remove_roles(no_hm, reason=f"request by {str(ctx.author)}")
        except Exception:
            pass

        # noinspection PyBroadException
        try:
            for x in ["help", "roles", "rules"]:
                embed = EmbedGenerator(x)
                await member.send(embed=embed.generate())
            await member.send("Also, please make sure that you read new messages at messages. "
                              "These are usually important and interesting. You can find them at the top.")
        except Exception:
            pass

    @hm.error
    async def hm_errorhandler(self, ctx: Context, error):
        if isinstance(error, discord.ext.commands.errors.MissingRole):
            await ctx.send(f"<@!{ctx.author.id}>\n"
                           f"This command is reserved for moderators.")
        else:
            error = BugReport(self.bot, ctx, error)
            error.user_details()
            await error.reply()
            raise error

    # ===================Not Safe For Work=================== #

    @commands.group(
        brief="Not Safe For Work - role",
        help="Add or remove role NSFW",
        pass_context=True
    )
    @commands.guild_only()
    @commands.has_role(ServerIds.HM)
    async def nsfw(self, ctx: Context):
        if ctx.invoked_subcommand is None:
            await ctx.send('Invalid sub mode passed...')

    @nsfw.command(pass_context=True,
                  help="Add role")
    async def add(self, ctx: Context):
        await accepted_channels(self.bot, ctx)
        role = discord.utils.get(ctx.guild.roles, id=ServerIds.NSFW)
        await ctx.author.add_roles(role, reason="request by user")

    @nsfw.command(pass_context=True,
                  help="Remove role")
    async def rem(self, ctx: Context):
        await accepted_channels(self.bot, ctx)
        role = discord.utils.get(ctx.guild.roles, id=ServerIds.NSFW)
        await ctx.author.remove_roles(role, reason="request by user")

    # ===================News=================== #

    @commands.group(
        brief="Newsletter - role",
        help="Add or remove role newsletter.",
        pass_context=True
    )
    @commands.guild_only()
    @commands.has_role(ServerIds.HM)
    async def news(self, ctx: Context):
        if ctx.invoked_subcommand is None:
            await ctx.send('Invalid sub mode passed...')

    @news.command(pass_context=True,
                  help="Add role")
    async def add(self, ctx: Context):
        await accepted_channels(self.bot, ctx)
        role = discord.utils.get(ctx.guild.roles, id=ServerIds.NEWS)
        await ctx.author.add_roles(role, reason="request by user")

    @news.command(pass_context=True,
                  help="Remove role")
    async def rem(self, ctx: Context):
        await accepted_channels(self.bot, ctx)
        role = discord.utils.get(ctx.guild.roles, id=ServerIds.NEWS)
        await ctx.author.remove_roles(role, reason="request by user")

    # ===================Coding=================== #

    @commands.group(
        brief="coding - role",
        help="Add or remove role coding.",
        pass_context=True
    )
    @commands.guild_only()
    @commands.has_role(ServerIds.HM)
    async def coding(self, ctx: commands):
        if ctx.invoked_subcommand is None:
            await ctx.send('Invalid sub mode passed...')

    @coding.command(pass_context=True,
                    help="Add role")
    async def add(self, ctx: Context):
        await accepted_channels(self.bot, ctx)
        role = discord.utils.get(ctx.guild.roles, id=ServerIds.CODEING)
        await ctx.author.add_roles(role, reason="request by user")

    @coding.command(pass_context=True,
                    help="Remove role")
    async def rem(self, ctx: Context):
        await accepted_channels(self.bot, ctx)
        role = discord.utils.get(ctx.guild.roles, id=ServerIds.CODEING)
        await ctx.author.remove_roles(role, reason="request by user")

    @group.error
    @coding.error
    async def roles_error_handler(self, ctx: Context, error):
        if isinstance(error, RoleNotFoundError):
            embed = EmbedGenerator("roles")
            await ctx.send(content=f"<@!{ctx.author.id}>\n"
                                   f"{error}",
                           embed=embed.generate(),
                           delete_after=60)

        elif isinstance(error, MultipleGroupsError) or isinstance(error, MultipleCoursesError):
            await ctx.send(f"<@!{ctx.author.id}>\n"
                           f"{error}")

        elif isinstance(error, discord.ext.commands.errors.MissingRole):
            await ctx.send(f"<@!{ctx.author.id}>\n"
                           f"`{error}`\n"
                           f"Make a request for this in <#{ServerIds.HELP}>.")

        elif isinstance(error, MissingRequiredArgument):
            await ctx.send(f"<@!{ctx.author.id}>\n"
                           f"Apparently, the command was not complete.\n")

        elif isinstance(error, WrongChatError):
            await ctx.message.delete()
            await ctx.send(f"<@!{ctx.author.id}>\n"
                           f"This command may not be used in this chat.\n"
                           f"Please use the chat provided for this purpose. <#{ServerIds.BOT_COMMANDS_CHANNEL}>.",
                           delete_after=60)

        elif isinstance(error, discord.ext.commands.errors.NoPrivateMessage):
            await ctx.send(f"This command can be placed only in the chat CHAT <#{ServerIds.BOT_COMMANDS_CHANNEL}>.")

        elif isinstance(error, commands.BadArgument):
            await ctx.send(str(error))

        else:
            error = BugReport(self.bot, ctx, error)
            error.user_details()
            await error.reply()
            raise error


def setup(bot: Bot):
    bot.add_cog(Roles(bot))
