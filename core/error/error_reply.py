from datetime import datetime
from logging import Logger
from typing import Optional

from discord import Embed, User, Guild, TextChannel, Permissions, HTTPException
from discord.ext.commands import Context, Bot

from core.logger import get_discord_child_logger


async def error_reply(ctx: Context,
                      logger: Logger,
                      cause: str,
                      solution: str,
                      content: str = None,
                      delete_after: Optional[int] = 60) -> None:
    user: User = ctx.author
    embed = Embed(title="Error during command processing occurred")
    command: str = ctx.message.content
    embed.add_field(name="Command", value=f"`{command}`", inline=False)
    embed.add_field(name="Cause", value=cause, inline=False)
    embed.add_field(name="Solution", value=solution, inline=False)
    embed.set_footer(text=user.name, icon_url=user.avatar_url)
    embed.timestamp = ctx.message.created_at
    try:
        await ctx.reply(embed=embed, content=content, delete_after=delete_after)
    except HTTPException as err:
        if "Unknown message" in err.args[0]:
            await ctx.send(embed=embed, content=content, delete_after=delete_after)
        else:
            raise err
    logger.error(f'User="{user.name}#{user.discriminator}({user.id})", Command="{command}", Cause="{cause}"')


async def send_error(chat: TextChannel,
                     action: str,
                     cause: str,
                     solution: str,
                     user: User,
                     delete_after: Optional[int] = 60) -> None:
    embed = Embed(title="Error during action processing occurred")
    embed.add_field(name="Action", value=f"`{action}`", inline=False)
    embed.add_field(name="Cause", value=cause, inline=False)
    embed.add_field(name="Solution", value=solution, inline=False)
    embed.set_footer(text=user.name, icon_url=user.avatar_url)
    embed.timestamp = datetime.now()
    await chat.send(embed=embed, delete_after=delete_after, content=user.mention)
    get_discord_child_logger(action) \
        .error(f'User="{user.name}#{user.discriminator}({user.id})", Action="{action}", Cause="{cause}"')


async def startup_error_reply(
        bot: Bot,
        title: str,
        cause: str,
        solution: str):
    embed = Embed(title=title, description="Please notify the admin immediately")
    embed.add_field(name="Cause", value=cause, inline=False)
    embed.add_field(name="Solution", value=solution, inline=False)

    guild: Guild = bot.guilds[0]
    text_channels: list[TextChannel] = guild.text_channels

    for channel in text_channels:
        permissions: Permissions = channel.permissions_for(guild.get_member(bot.user.id))
        if permissions.read_messages and permissions.send_messages:
            await channel.send(embed=embed)
            break
