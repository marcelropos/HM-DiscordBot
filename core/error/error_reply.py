from logging import Logger
from typing import Optional, Union

from discord import Embed, User, Member
from discord.ext.commands import Context


async def error_reply(ctx: Context,
                      logger: Logger,
                      cause: str,
                      solution: str,
                      content: str = None,
                      delete_after: Optional[int] = 60) -> None:
    embed = Embed(title="Error during command processing occurred")
    command: str = ctx.message.content
    embed.add_field(name="Command", value=f"`{command}`", inline=False)
    embed.add_field(name="Cause", value=cause, inline=False)
    embed.add_field(name="Solution", value=solution, inline=False)
    user: Union[Member, User] = ctx.author
    await ctx.reply(embed=embed, content=content, delete_after=delete_after)
    logger.error(f'User="{user.name}#{user.discriminator}({user.id})", Command="{command}", Cause="{cause}"')
