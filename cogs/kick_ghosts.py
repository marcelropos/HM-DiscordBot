import asyncio
from collections import namedtuple
from datetime import datetime, timedelta
from typing import Union

from discord import Member, User, Role, Embed, Guild, TextChannel, Forbidden
from discord.ext.commands import Cog, Bot, group, bot_has_guild_permissions, Context, BadArgument
from discord.ext.tasks import loop
from pymongo.errors import ServerSelectionTimeoutError

from cogs.bot_status import listener
from core.error.error_collection import BrokenConfigurationError
from core.error.error_reply import startup_error_reply
from core.global_enum import CollectionEnum, ConfigurationNameEnum
from core.logger import get_discord_child_logger
from mongo.primitive_mongo_data import PrimitiveMongoData

logger = get_discord_child_logger("KickGhosts")
event = namedtuple("KickTime", ["hour", "min"])


class KickGhosts(Cog):
    """
    Manage not verified member by kicking them after an amount of time.
    """

    def __init__(self, bot: Bot):
        self.bot = bot
        self.db: PrimitiveMongoData = PrimitiveMongoData(CollectionEnum.KICK_GHOSTS)
        self.startup = True

        # The actual values will be set at the on_ready method.
        self.config: dict[ConfigurationNameEnum: Union[bool, int, event]] = {
            ConfigurationNameEnum.ENABLED: False,
            ConfigurationNameEnum.DEADLINE: 30,
            ConfigurationNameEnum.WARNING: 7,
            ConfigurationNameEnum.TIME: event(hour=8, min=0)
        }

    def cog_unload(self):
        self.kick_not_verified.stop()

    @listener()
    async def on_ready(self):
        """
        Load configuration data or use a default if it is not available.
        """
        if self.startup:
            self.startup = False
            try:
                for c in self.config:
                    key = c.value

                    enabled = await self.db.find_one({key: {"$exists": True}})
                    if enabled:
                        self.config[c] = enabled[key]
                    else:
                        await self.db.insert_one({key: self.config[c]})
                self.config[ConfigurationNameEnum.TIME] = event(*self.config[ConfigurationNameEnum.TIME])
                self.kick_not_verified.start()

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
           name="kick",
           help="Manages the conditions when unverified members should be kicked or warned.")
    @bot_has_guild_permissions(administrator=True)
    async def kick_ghosts(self, ctx: Context):
        self.check_subcommand(ctx)

    @kick_ghosts.command(pass_context=True,
                         brief="Sets the daily kick time.",
                         help="Use the Format '%H:%M' to set the time properly.")
    async def time(self, ctx: Context, time: str):
        """
        Sets the daily kick time.
        Args:
            ctx: The command context provided by the discord.py wrapper.

            time: The daily Time when the user shall be kicked.

        Reply:
            A success message.

        Raises:
            ValueError
        """
        time: datetime = datetime.strptime(time, '%H:%M')
        key = ConfigurationNameEnum.TIME
        await self.db.update_one({key.value: {"$exists": True}}, {key.value: event(hour=time.hour, min=time.minute)})

        embed = Embed(title="Kick Ghosts",
                      description="The time has been updated.")
        await ctx.reply(embed=embed)

    @kick_ghosts.command(pass_context=True,
                         brief="Enables or disables the daily kick.",
                         help="Pleas use 'true' or 'false' to set the mode properly.\n"
                              "Other values that may interpreted as bool could also work.")
    async def enabled(self, ctx: Context, mode: bool):
        """
        Enable or Disable the daily kick
        Args:
            ctx: The command context provided by the discord.py wrapper.

            mode: A boolean that indicates the activation status.

        Reply:
            A success message.

        Raises:
            BadBoolArgument
        """
        key = ConfigurationNameEnum.ENABLED
        self.config[key] = mode
        await self.db.update_one({key.value: {"$exists": True}}, {key.value: mode})

        embed = Embed(title="Kick Ghosts",
                      description="The mode has been updated.")
        await ctx.reply(embed=embed)

    @kick_ghosts.command(pass_context=True,
                         brief="Sets the deadline after the member will be kicked.",
                         help="You can set any natural number. (except 0)")
    async def deadline(self, ctx: Context, days: int):
        """
        Set the deadline after the member will be kicked.
        Args:
            ctx: The command context provided by the discord.py wrapper.

            days: An integer for the deadline after the member will be kicked.

        Reply:
            A success message.

        Raises:
            BadArgument
        """
        if not days > 0:
            raise BadArgument

        key = ConfigurationNameEnum.DEADLINE
        self.config[key] = days
        await self.db.update_one({key.value: {"$exists": True}}, {key.value: days})

        embed = Embed(title="Kick Ghosts",
                      description="The deadline has been updated.")
        await ctx.reply(embed=embed)

    @kick_ghosts.command(pass_context=True,
                         brief="Sets the days to start warn the member.",
                         help="You can set any natural number. (except 0)")
    async def warning(self, ctx: Context, days: int):
        """
        Enable or Disable the daily kick.
        Args:
            ctx: The command context provided by the discord.py wrapper.

            days: An integer for the deadline after the member will be kicked.

        Reply:
            A success message.

        Raises:
            BadArgument
        """
        if not days > 0:
            raise BadArgument

        key = ConfigurationNameEnum.WARNING
        self.config[key] = days
        await self.db.update_one({key.value: {"$exists": True}}, {key.value: days})

        embed = Embed(title="Kick Ghosts",
                      description="The warning has been updated.")
        await ctx.reply(embed=embed)

    # safe_roles group

    @group(pass_context=True,
           name="safeRoles",
           help="Manages the safe roles.")
    @bot_has_guild_permissions(administrator=True)
    async def safe_roles(self, ctx: Context):
        self.check_subcommand(ctx)

    # noinspection PyUnusedLocal
    @safe_roles.command(pass_context=True,
                        brief="Adds one or more roles to the list of safe roles.",
                        help="Ping all roles you want to add.\n"
                             "You should probably use this role on a private debug chat.")
    async def add(self, ctx: Context, *, roles):  # roles is used for pretty help
        """
        Add one or more roles to the list of safe roles.
        Args:
            ctx: The command context provided by the discord.py wrapper.

            roles: The pinged roles to be added to the safe list.

        Reply:
            A success message.
        """
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
                      description="The role(s) is/are now added to the safe list.")
        await ctx.reply(embed=embed)

    # noinspection PyUnusedLocal
    @safe_roles.command(pass_context=True,
                        aliases=["rem", "rm"],
                        brief="Removes one or more roles to the list of safe roles.",
                        help="Ping all roles you want to remove.\n"
                             "You should probably use this role on a private debug chat.")
    async def remove(self, ctx: Context, *, roles):  # role is used for pretty help
        """
       Remove one or more roles to the list of safe roles.
       Args:
           ctx: The command context provided by the discord.py wrapper.

           roles: The pinged roles to be removed to the safe list.

       Reply:
           A success message.
       """
        key = ConfigurationNameEnum.SAFE_ROLES_LIST.value
        found = await self.db.find({key: {"$exists": True}})
        safe_roles: set[int] = set(found[key])
        safe_roles.difference(ctx.message.raw_role_mentions)
        await self.db.update_one({key: {"$exists": True}}, {key: safe_roles})

        embed = Embed(title="Safe Roles",
                      description="The role(s) is/are now removed from the safe list.")
        await ctx.reply(embed=embed)

    @safe_roles.command(pass_context=True,
                        aliases=["view"],
                        help="Shows all as safe registered roles.")
    async def show(self, ctx: Context):
        """
        Shows the list of safe roles.

        Args:
            ctx: The command context provided by the discord.py wrapper.
        """
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

    @loop(minutes=1)
    async def kick_not_verified(self):
        """
        Kick not verified Ghosts and warn not verified user.
        """

        if not await self.kick():
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
                            value="You are not verified\n",
                            inline=False)
            embed.add_field(name="Solution",
                            value=f"Receive one of these roles:\n"
                                  f"{safe_roles_names}\n"
                                  f"within the next **{left}** days.",
                            inline=False)
            await help_chat.send(embed=embed)  # , content=f"<@{member.id}>")

        for member in kick_member:
            try:
                await member.kick(reason="Too long without verification")
                logger.info('Kicked user: User="{member.name}#{member.discriminator}({member.id})" ')
                embed = Embed(title="Kick Ghosts",
                              description=f"Kicked <@{member.id}>.")
            except Forbidden:
                logger.error(f'Tried to kick User="{member.name}#{member.discriminator}({member.id})" '
                             f'but failed due missing permissions.')
                embed = Embed(title="Kick Ghosts",
                              description=f"Tried to kick <@{member.id}> but failed due missing permissions.")
            await debug_chat.send(embed=embed)

    # Helper methods

    async def kick(self) -> bool:
        """
        Determines the time to execute the method, if it has been activated.

        Return:
            Permission to remove user.
        """

        while self.startup:
            await asyncio.sleep(10)

        now = datetime.now()
        _event: event = self.config[ConfigurationNameEnum.TIME]
        until_time = now.replace(hour=_event.hour, minute=_event.min, second=0, microsecond=0)
        if until_time < now:
            until_time += timedelta(days=1)
        until_time = (until_time.year, until_time.month, until_time.day, until_time.hour, until_time.minute)
        wait_seconds = (datetime(*until_time) - now).total_seconds()
        activate = wait_seconds < 60 * 5
        if activate:
            await asyncio.sleep(wait_seconds)
        return activate and self.config[ConfigurationNameEnum.ENABLED]

    async def assign_variables(self) -> (int, TextChannel, Guild, TextChannel, set[Role], str, int):
        """
        Assign variables for the kick_not_verified method.

        Return:
            A far too fat tuple

        Raises:
            BrokenConfigurationError
        """
        guild: Guild = self.bot.guilds[0]

        key = ConfigurationNameEnum.SAFE_ROLES_LIST.value
        found = await self.db.find_one({key: {"$exists": True}})
        safe_roles: set[Role] = {guild.get_role(safe_role_id) for safe_role_id in found[key]}

        if None in safe_roles:
            logger.error("A non-existent role id was loaded. For security reasons, "
                         "the execution of the member kick was aborted.")
            raise BrokenConfigurationError

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
