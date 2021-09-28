import asyncio
from datetime import datetime
from io import BytesIO
from typing import Union, Optional

import aiohttp
from aiohttp import ClientResponse
from discord import Message, MessageReference, TextChannel, Member, User, Embed, File
from discord.ext.commands import Bot, Cog, has_guild_permissions
from discord.ext.commands import command, Context
from prettytable import PrettyTable

from core.error.error_collection import ManPageNotFound
from core.logger import get_discord_child_logger

logger = get_discord_child_logger("spielereien")


class Spielereien(Cog):
    """
    Small collection of commands for various purposes.
    """

    def __init__(self, bot: Bot):
        self.bot: Bot = bot
        logger.info(f"The cog is online.")

    def cog_unload(self):
        logger.warning("Cog has been unloaded.")

    @command(help="Computes the time between the command and it's (first) reply.")
    async def ping(self, ctx: Context):
        """
        Replies the needed time to gather and answer the message.

        Args:
            ctx: The command context provided by the discord.py wrapper.

        Replies:
            The time between sending and sending the pong reply.
        """
        reply: Message = await ctx.reply("Pong")
        msg: Message = ctx.message
        await reply.edit(content=f"{reply.created_at.timestamp() - msg.created_at.timestamp()}")

    @command(brief="Searches a manpage",
             help=f"Search for a man page and jump to a section if specified.\n"
                  f"Manpage und subsection must be seperated by an '#'\n"
                  f"  >> Example: <manpage> = bridge#SPANNING_TREE\n")
    async def man(self, ctx: Context, manpage: str):
        """
        Fetches a requested manpage.

        Args:
            ctx: The command context provided by the discord.py wrapper.

            manpage: The command to search for.

        Replies:
            The Manpage.

        Raises:
            ManPageNotFound
        """
        msg: Message = ctx.message
        mentions: set = set(msg.mentions)
        cmd_sec = manpage.split("#")
        cmd = cmd_sec[0]
        if len(cmd_sec) > 1:
            subsection = f"#{cmd_sec[1]}"
        else:
            subsection = ""

        reference: MessageReference = msg.reference
        if reference:
            channel: TextChannel = ctx.channel
            replied_to: Message = await channel.fetch_message(reference.message_id)
            mentions.add(replied_to.author)

        ping = ""

        for mention in mentions:
            if isinstance(mention, Member):
                mention: Union[Member, User]
                ping += mention.mention

        result: list = list(await asyncio.gather(
            self.get_page(f"https://man.openbsd.org/{cmd}", 1),
            self.get_page(f"https://wiki.archlinux.org/index.php/{cmd}", 2)
        ))

        result.sort(key=lambda x: x[0])

        for _, page in result:
            if page.ok:
                answer = f"On your UNIX/UNIX-like system you can probably run " \
                         f"`$ man {cmd}` to receive this manpage.\n" \
                         f"For now you can also click on this link to gather the information.\n{page.url}{subsection}"

                if mentions:
                    embed: Embed = Embed(title="Manpage",
                                         description=f"I was asked to show you this man page:\n"
                                                     f"It contains useful information that will hopefully help you.\n"
                                                     + answer)
                    await ctx.reply(embed=embed, content=ping)
                else:
                    embed: Embed = Embed(title="Manpage",
                                         description=answer)
                    await ctx.reply(embed=embed)
                return
        else:
            raise ManPageNotFound(cmd)

    @command(name="list-guild-member",
             aliases=["lgm"])
    @has_guild_permissions(administrator=True)
    async def list_guild_member(self, ctx: Context):
        """
        Replies a list of all member in the guild with additional information.

        Args:
            ctx: The command context provided by the discord.py wrapper.

        Replies:
            The list.
        """
        column = ["name", "roles", "joined_at", "pending"]
        table = PrettyTable(column)
        members = await ctx.guild.fetch_members(limit=None).flatten()
        for member in members:
            member: Union[Member, User]

            roles = reversed(member.roles)
            role_list = ""
            for role in roles:
                if role.name != "@everyone":
                    role_list += role.name + "\n"

            joined = member.joined_at.strftime("%d.%m.%Y")

            nick = f"Nick: {str(member.nick)}\n" if member.nick else ""
            names = nick + f"Name: {str(member.name)}#{str(member.discriminator)}"

            table.add_row((names, role_list, joined, member.pending))

        table.title = f"List status from {datetime.now().strftime('%d.%m.%Y, %H:%M:%S')}" \
                      f" - there are {len(members)} members"

        await ctx.reply(
            file=File(
                BytesIO(bytes(str(table), encoding='utf-8')),
                filename="List_of_all_members.text"),
            content="Here is a list of all members that are currently on this server.",
            delete_after=600)

    @staticmethod
    async def get_page(url: str, priority: int = 0) -> (int, Optional[ClientResponse]):
        """
        Fetches async the page.

        Args:
            url: The url what else?

            priority: The priority of the requested page:

        Returns:
            A tuple containing the priority in the first position and the page (or none) in the second position.
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    pass
                return priority, response
        except aiohttp.ClientError:
            return priority, None


def setup(bot: Bot):
    bot.add_cog(Spielereien(bot))
