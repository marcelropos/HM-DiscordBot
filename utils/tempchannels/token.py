import logging
import re

import discord
from aiosqlite import Connection
from discord import Message
from discord.ext.commands import Bot, Context

from settings_files.all_errors import CouldNotSendMessage
from utils.tempchannels.maintainchannels import MaintainChannel
from utils.utils import accepted_channels

logger = logging.getLogger("discord")


class Token:

    @staticmethod
    async def token_send(bot: Bot, ctx: Context, token: int, user, db):
        await accepted_channels(bot, ctx)
        embed = MaintainChannel.invite_embed(ctx.author, f"```!tmpc join {token}```")
        matches = re.finditer(r"[0-9]+", user)
        for match in matches:
            start, end = match.span()
            user_id = user[start:end]
            user = await discord.Client.fetch_user(bot, user_id)
            send_error = False
            error_user = set()

            # noinspection PyBroadException
            try:
                message = await user.send(embed=embed)
                await MaintainChannel.save_invite(ctx.author, message, token, db)
                await message.add_reaction(emoji="🔓")
            except Exception:
                error_user.add(str(user))
                send_error = True

            if send_error:
                raise CouldNotSendMessage(f"Invitation could not be sent to: {error_user}.\n"
                                          f"Possibly this is caused by the settings of the users.")

    @staticmethod
    async def token_place(ctx: Context, token: int, db: Connection):
        logger.debug(f"Place Token for {str(ctx.author)}")
        embed = MaintainChannel.invite_embed(ctx.author, f"```!tmpc join {token}```")
        message: Message = await ctx.send(embed=embed)
        # noinspection PyBroadException
        try:
            await MaintainChannel.save_invite(ctx.author, message, token, db)
            await message.add_reaction(emoji="🔓")
        except Exception:
            await message.delete()
            await ctx.send("Internal error occurred. Could not create a invite.")
