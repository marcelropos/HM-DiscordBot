# noinspection PyUnresolvedReferences
import discord
# noinspection PyUnresolvedReferences
from discord.ext import commands
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
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.guild_only()
    @commands.has_role(ServerIds.HM)
    async def group(self, ctx, group: str, member=None):
        await accepted_channels(self.bot, ctx)
        if member:
            user_id = extract_id(member)
            member = await ctx.guild.fetch_member(user_id)
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
                        raise MissingRole(f"Höhere Semster können nur von Mods vergeben werden")

                try:
                    role = discord.utils.get(ctx.guild.roles, name=group)
                    await member.add_roles(role, reason=f"request by {str(ctx.author)}")

                    role = discord.utils.get(ctx.guild.roles, name=group[:3])
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
            raise MultipleGroupsError(f"@{name} ist bereits Mitglied der gruppe von "
                                      f"`{got_roles.intersection(ServerRoles.ALL_GROUPS).pop()}`")

    @commands.command()
    @commands.guild_only()
    @commands.has_role(ServerIds.MODERATOR)
    async def hm(self, ctx):
        await accepted_channels(self.bot, ctx)
        msg = ctx.message.content
        user_id = extract_id(msg)
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
            await member.send("Achte auch bitte darauf, dass du neue Nachrichten bei Mittteilungen liest. Diese sind "
                              "meist wichtig und interessant. Du findest diese ganz oben.")
        except Exception:
            pass

    @hm.error
    async def hm_errorhandler(self, ctx, error):
        if isinstance(error, discord.ext.commands.errors.MissingRole):
            await ctx.send(f"<@!{ctx.author.id}>\n"
                           f"Dieser Befehl ist Moderatoren vorbehalten.")
        else:
            error = BugReport(self.bot, ctx, error)
            error.user_details()
            await error.reply()
            raise error

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
    @nsfw_add.error
    @nsfw_rem.error
    @coding.error
    async def roles_errorhanler(self, ctx, error):
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
