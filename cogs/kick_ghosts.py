from datetime import datetime
from typing import Union

from discord import Member, User, Role, Embed, Guild, TextChannel, Forbidden
from discord.ext.commands import Cog, Bot, group, bot_has_guild_permissions, Context, BadArgument, command
# noinspection PyPackageRequirements
from pymongo.errors import ServerSelectionTimeoutError

from cogs.botStatus import listener
from core.error.error_reply import startup_error_reply
from core.globalEnum import CollectionEnum, ConfigurationNameEnum
from core.logger import get_discord_child_logger
from mongo.primitiveMongoData import PrimitiveMongoData

logger = get_discord_child_logger("KickGhosts")


class KickGhosts(Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
        self.db: PrimitiveMongoData = PrimitiveMongoData(CollectionEnum.KICK_GHOSTS)
        self.startup = True

        # The actual values will be set at the on_ready method.
        self.config: dict[ConfigurationNameEnum: Union[bool, int]] = {
            ConfigurationNameEnum.ENABLED: False,
            ConfigurationNameEnum.DEADLINE: 30,
            ConfigurationNameEnum.WARNING: 7,
        }

    @listener()
    async def on_ready(self):
        if self.startup:
            self.startup = False
            try:
                for c in self.config:
                    key = c.value
                    default = self.config[c]

                    enabled = await self.db.find_one({key: {"$exists": True}})
                    if enabled:
                        self.config[c] = enabled[key]
                    else:
                        await self.db.insert_one({key: default})

            except ServerSelectionTimeoutError:
                title = "Error on Startup"
                cause = "Could not connect to database."
                solution = f"```\n" \
                           f"1. Establish the connection to the database.\n" \
                           f"2. Reload `{self.__class__.__name__}`.\n" \
                           f"```"
                await startup_error_reply(bot=self.bot, title=title, cause=cause, solution=solution)
                logger.error(cause)

    # kick_ghosts group

    @group(pass_context=True,
           name="kickGhosts")
    @bot_has_guild_permissions(administrator=True)
    async def kick_ghosts(self, ctx: Context):
        self.check_subcommand(ctx)

    @kick_ghosts.group(pass_context=True)
    async def enabled(self, ctx: Context, mode: bool):
        key = ConfigurationNameEnum.ENABLED
        self.config[key] = mode
        await self.db.update_one({key.value: {"$exists": True}}, {key.value: mode})

        embed = Embed(title="Kick Ghosts",
                      description="The mode has been updated.")
        await ctx.reply(embed=embed)

    @kick_ghosts.group(pass_context=True)
    async def deadline(self, ctx: Context, days: int):
        key = ConfigurationNameEnum.DEADLINE
        self.config[key] = days
        await self.db.update_one({key.value: {"$exists": True}}, {key.value: days})

        embed = Embed(title="Kick Ghosts",
                      description="The deadline has been updated.")
        await ctx.reply(embed=embed)

    @kick_ghosts.group(pass_context=True)
    async def warning(self, ctx: Context, days: int):
        key = ConfigurationNameEnum.WARNING
        self.config[key] = days
        await self.db.update_one({key.value: {"$exists": True}}, {key.value: days})

        embed = Embed(title="Kick Ghosts",
                      description="The warning has been updated.")
        await ctx.reply(embed=embed)

    # safe_roles group

    @group(pass_context=True,
           name="safeRoles")
    @bot_has_guild_permissions(administrator=True)
    async def safe_roles(self, ctx: Context):
        self.check_subcommand(ctx)

    @safe_roles.group(pass_context=True)
    async def add(self, ctx: Context):
        key = ConfigurationNameEnum.SAFE_ROLES_LIST.value
        found = await self.db.find_one({key: {"$exists": True}})
        safe_roles = set()
        safe_roles.update(ctx.message.raw_role_mentions)
        if found:
            safe_roles.update(found[key])
            await self.db.update_one({key: {"$exists": True}}, {key: list(safe_roles)})
        else:
            await self.db.insert_one({key: list(safe_roles)})

        embed = Embed(title="Safe Roles",
                      description="The role is now added to the safe list.")
        await ctx.reply(embed=embed)

    @safe_roles.group(pass_context=True,
                      aliases=["rem", "rm"])
    async def remove(self, ctx: Context):
        key = ConfigurationNameEnum.SAFE_ROLES_LIST.value
        found = await self.db.find({key: {"$exists": True}})
        safe_roles: set[int] = set(found[key])
        safe_roles.difference(ctx.message.raw_role_mentions)
        await self.db.update_one({key: {"$exists": True}}, {key: safe_roles})

        embed = Embed(title="Safe Roles",
                      description="The role is now removed from the safe list.")
        await ctx.reply(embed=embed)

    @safe_roles.group(pass_context=True,
                      aliases=["view"])
    async def show(self, ctx: Context):
        key = ConfigurationNameEnum.SAFE_ROLES_LIST.value
        found = await self.db.find_one({key: {"$exists": True}})
        if found:
            safe_roles_ids: set[int] = set(found[key])
            safe_roles: list[Role] = [role for role in ctx.guild.roles if role.id in safe_roles_ids]
            safe_roles_names = ""
            for safe_role in safe_roles:
                safe_roles_names += f"<@&{safe_role.id}> "

            embed = Embed(title="Safe Roles:",
                          description=f"At the moment there are the following Roles selected as 'Safe Roles'\n"
                                      f"{safe_roles_names}")
        else:
            embed = Embed(title="Safe Roles",
                          description="No safe roles found.")
        await ctx.reply(embed=embed)

    # Loop

    @command()
    async def kick_not_verified(self):
        """
        Kick not verified Ghosts.
        """
        if not self.config[ConfigurationNameEnum.ENABLED]:
            return

        deadline, debug_chat, guild, help_chat, safe_roles, safe_roles_names, warning = await self.assign_variables()

        not_verified: set[Union[Member, User]] = {member for member in guild.members if
                                                  not set(member.roles).intersection(safe_roles)}

        kick_member: set[Union[Member, User]] = {member for member in not_verified if
                                                 self.days_on_server(member) > deadline}

        warn_member: set[Union[Member, User]] = {member for member in not_verified if
                                                 self.days_on_server(member) > deadline - warning - 1
                                                 and member not in kick_member}

        for member in warn_member:
            left = deadline - self.days_on_server(member)
            embed = Embed(title="WARNING YOU WILL BE KICKED SOON")
            embed.add_field(name="Cause",
                            value="To stay on the server, you need at least one of the following roles:\n"
                                  f"{safe_roles_names}",
                            inline=False)
            embed.add_field(name="Solution",
                            value=f"Receive one of these roles within the next **{left}** days.",
                            inline=False)
            await help_chat.send(embed=embed)  # , content=f"<@{member.id}>")

        for member in kick_member:
            try:
                await member.kick(reason="Too long without verification")
            except Forbidden:
                logger.error(f'Tried to kick User="{member.name}#{member.discriminator}({member.id})" '
                             f'but failed due missing permissions.')
                embed = Embed(title="Kick Ghosts",
                              description=f"Tried to kick <@{member.id}> but failed due missing permissions.")
                await debug_chat.send(embed=embed)

    # Helper methods

    async def assign_variables(self) -> (int, TextChannel, Guild, TextChannel, set[Role], str, int):
        """
        Assign variables for the kick_not_verified method.

        Return:
            A far too fat tuple
        """
        guild: Guild = self.bot.guilds[0]

        key = ConfigurationNameEnum.SAFE_ROLES_LIST.value
        found = await self.db.find_one({key: {"$exists": True}})
        safe_roles: set[Role] = {guild.get_role(safe_role_id) for safe_role_id in found[key]}

        deadline = self.config[ConfigurationNameEnum.DEADLINE]
        warning = self.config[ConfigurationNameEnum.WARNING]

        key = ConfigurationNameEnum.HELP_CHAT.value
        found = await PrimitiveMongoData(CollectionEnum.CHANNELS).find_one({key: {"$exists": True}})
        help_chat: TextChannel = guild.get_channel(found[key])

        key = ConfigurationNameEnum.DEBUG_CHAT.value
        found = await PrimitiveMongoData(CollectionEnum.CHANNELS).find_one({key: {"$exists": True}})
        debug_chat: TextChannel = guild.get_channel(found[key])

        safe_roles_names = ""
        for safe_role in safe_roles:
            safe_roles_names += f"<@&{safe_role.id}> "
        return deadline, debug_chat, guild, help_chat, safe_roles, safe_roles_names, warning

    @staticmethod
    def days_on_server(member: Member):
        """
        Calculates how long a member is on the guild.
        """
        return (datetime.now() - member.joined_at).days

    @staticmethod
    def check_subcommand(ctx):
        """
        Check if any subcommand has been invoked and logs that. Otherwise BadArgument is thrown.
        """
        if not ctx.invoked_subcommand:
            raise BadArgument
        member: Union[Member, User] = ctx.author
        logger.info(f'User="{member.name}#{member.discriminator}({member.id})", Command="{ctx.message.content}"')


def setup(bot: Bot):
    bot.add_cog(KickGhosts(bot))
