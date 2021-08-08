import asyncio
from typing import Union

import aiohttp
from discord import Message, MessageReference, TextChannel, Member, User, Embed
from discord.ext.commands import Bot, Cog
from discord.ext.commands import command, Context

from core.error.error_collection import ManPageNotFound


class Spielereien(Cog):

    def __init__(self, bot: Bot):
        self.bot: Bot = bot

    @command()
    async def ping(self, ctx: Context):
        reply: Message = await ctx.reply("Pong")
        msg: Message = ctx.message
        await reply.edit(content=f"{reply.created_at.timestamp() - msg.created_at.timestamp()}")

    @command()
    async def man(self, ctx: Context, arg: str):

        msg: Message = ctx.message
        mentions: set = set(msg.mentions)

        reference: MessageReference = msg.reference
        if reference:
            channel: TextChannel = ctx.channel
            replied_to: Message = await channel.fetch_message(reference.message_id)
            mentions.add(replied_to.author)

        ping = ""

        for mention in mentions:
            if isinstance(mention, Member):
                mention: Union[Member, User]
                ping += f"<@{mention.id}> "

        result: list = list(await asyncio.gather(
            self.get_page(f"https://man.openbsd.org/{arg}", 1),
            self.get_page(f"https://wiki.archlinux.org/index.php/{arg}", 2)
        ))

        result.sort(key=lambda x: x[0])

        for _, page in result:
            if page.ok:

                if mentions:
                    embed: Embed = Embed(title="Manpage",
                                         # TODO: This message should be stored into the database
                                         description=f"I was asked to show you this man page:\n"
                                                     f"It contains useful information that will hopefully help you.\n"
                                                     f"On your UNIX/UNIX-like system you can probably run "
                                                     f"`$ man {arg}` to receive this manpage.\n"
                                                     f"For now you can also click on this link to gather these information.\n"
                                                     f"{page.url}")
                    await ctx.reply(embed=embed, content=ping)
                else:
                    embed: Embed = Embed(title="Manpage",
                                         description=f"On your UNIX/UNIX-like system you can probably run `$ man {arg}`"
                                                     f"{page.url}")
                    await ctx.reply(embed=embed)
                return
        else:
            raise ManPageNotFound(arg)

    @staticmethod
    async def get_page(url, priority=0):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    pass
                return priority, response
        except aiohttp.ClientError:
            return priority, None


def setup(bot: Bot):
    bot.add_cog(Spielereien(bot))
