from datetime import datetime
from time import sleep
from typing import Union, Callable

import discord
from discord import Embed, Member, User, Message
from discord.ext.commands import Cog, Bot, Context, group, command, is_owner, BadArgument, has_guild_permissions

from core.logger import get_discord_child_logger

logger = get_discord_child_logger("admin")


class Admin(Cog):
    """
    Provides administrative commands for this bot and the sever.
    """

    def __init__(self, bot: Bot):
        self.bot = bot
        logger.info(f"The cog is online.")

    def cog_unload(self):
        logger.warning("Cog has been unloaded.")

    @group(pass_context=True, name="cog", aliases=["module"])
    @has_guild_permissions(administrator=True)
    async def module(self, ctx: Context):
        """
        A group of commands.
        """
        if not ctx.invoked_subcommand:
            raise BadArgument
        member: Union[Member, User] = ctx.author
        logger.info(f'User="{member.name}#{member.discriminator}({member.id})", Command="{ctx.message.content}"')

    @module.command(pass_context=True, help="Loads a cog.")
    async def load(self, ctx: Context, cog: str):
        """
        Loads a cog.

        Args:
            ctx: The command context provided by the discord.py wrapper.

            cog: The filename of the cog to be loaded.

        Replies:
            A success message.
        """
        await self.bot.load_extension(f"cogs.{cog}")

        embed = Embed(title="Cog", description=f"The {cog} cog was loaded successfully.")
        await ctx.reply(embed=embed)

    @module.command(pass_context=True, help="Reloads a cog.")
    async def reload(self, ctx: Context, cog: str):
        """
        Reloads a cog.

        Args:
            ctx: The command context provided by the discord.py wrapper.

            cog: The filename of the cog to be reloaded.

        Replies:
            A success message.
        """
        await self.bot.unload_extension(f"cogs.{cog}")
        await self.bot.load_extension(f"cogs.{cog}")
        embed = Embed(title="Cog", description=f"The {cog} cog was reloaded successfully.")
        await ctx.reply(embed=embed)

    @module.command(pass_context=True, help="Unloads a cog.")
    async def unload(self, ctx: Context, cog: str):
        """
        Unloads a cog.

        Args:
            ctx: The command context provided by the discord.py wrapper.

            cog: The filename of the cog to be unloaded.

        Replies:
            A success message.
        """
        await self.bot.unload_extension(f"cogs.{cog}")
        embed = Embed(title="Cog", description=f"The {cog} cog was unloaded successfully.")
        await ctx.reply(embed=embed)

    # Purge group

    @group(pass_context=True, brief="Deletes messages",
           help="Depending on the subcommand either a whole chat is deleted or messages of one or more members.")
    @has_guild_permissions(administrator=True)
    async def purge(self, ctx: Context):
        """
        A group of commands.
        """
        if not ctx.invoked_subcommand:
            raise BadArgument
        member: Union[Member, User] = ctx.author
        logger.info(f'User="{member.name}#{member.discriminator}({member.id})", Command="{ctx.message.content}"')

    @purge.command(brief="Deletes ALL chat messages.",
                   help="All X messages written to the chat with this command will be deleted.")
    @is_owner()
    async def chat(self, ctx: Context, count: int):
        """
        Cleans a chat.

        Args:
            ctx: The command context provided by the discord.py wrapper.

            count: The amount of messages to be cleaned.

        Replies:
            A success message containing the deleted amount of messages.
        """
        count = len(await ctx.channel.purge(limit=count, bulk=True))
        embed = Embed(title=ctx.channel.name,
                      description=f"Purged {count} messages")
        await ctx.send(embed=embed)

    @purge.command(brief="Deletes message from mentioned member.",
                   help="All messages after a certain date and from specified members will be deleted.\n"
                        "Dateformat: dd.mm.yyyy")
    async def member(self, ctx: Context, after, *, mentions):  # parameter only for pretty help.
        """
        Cleans a chat of the messages from a user for the defined time.

        Args:
            ctx: The command context provided by the discord.py wrapper.

            after: Messages younger than after will be deleted.

            mentions: The user to be purged.

        Replies:
            A success message containing the deleted amount of messages.
        """

        after: datetime = datetime.strptime(after, '%d.%m.%y')
        message: Message = ctx.message
        mentions: set[Union[Member, User]] = message.mentions
        check = self.purge_check(mentions)
        count = len(await ctx.channel.purge(after=after, check=check, bulk=True))
        embed = Embed(title=ctx.channel.name,
                      description=f"Purged {count} messages")
        await ctx.send(embed=embed)

    # Single commands

    @command(brief="Tuns off the bot.",
             help="The bot will be shut down properly. The program must be restarted to start the bot.")
    @is_owner()
    async def shutdown(self, _: Context):
        """Closes the bot"""
        logger.warning("Received the shutdown command. All connections will be closed now!")
        await discord.Client.change_presence(self=self.bot,
                                             status=discord.Status.offline)
        await self.bot.close()
        sleep(1)  # this sleep is there to avoid a Exception in asyncio
        logger.warning("All connections are closed. Hope you will activate me again soon.")

    @command(brief="Toggle command",
             help="Enables/Disables a command.")
    @has_guild_permissions(administrator=True)
    async def toggle(self, ctx: Context, *, cmd):
        """Enables or disables an existing bot command."""
        command = self.bot.get_command(cmd)
        title = "Toggle command"

        if command is None:
            embed = Embed(title=title,
                          description=f"Command not found!")
            await ctx.reply(embed=embed)
        elif ctx.command == command:
            embed = Embed(title=title,
                          description=f"Can't disable the command to disable itself. You do see the problem don't you?")
            await ctx.reply(embed=embed)
        else:
            command.enabled = not command.enabled
            x = "enabled" if command.enabled else "disabled"
            embed = Embed(title=title,
                          description=f"You {x} {command.qualified_name}")
            await ctx.reply(embed=embed)

    # Static methods

    @staticmethod
    def purge_check(mentions: set[Union[Member, User]]) -> Callable[[Message], bool]:
        """
        Returns predicate for message deletion.

        Args:
            mentions: A set of member which messages shall be deleted.

        Returns:
            A predicate
        """

        def check(message: Message) -> bool:
            """
            Replies to the question if a certain message shall be deleted.

            Args:
                message: The message.

            Returns:
                The confirmation or disapproval.
            """
            for member in mentions:
                if message.author.id == member.id:
                    return True
            return False

        return check


async def setup(bot: Bot):
    await bot.add_cog(Admin(bot))
