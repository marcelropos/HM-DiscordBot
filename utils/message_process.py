import re

import discord
from discord.message import Message

from settings_files._global import EmojiIds, ServerIds
from settings_files.all_errors import *
from utils.logbot import LogBot


# noinspection PyBroadException
async def reactions(ctx, bot):
    try:
        if not ctx.author.bot:
            msg = re.sub(r"[^a-zA-Z0-9\s]", "", ctx.content).lower() + " "
            msg += re.sub(r"\.", " ", ctx.content).lower()
            msg_list = list(re.split(r"\s", msg))

            for keyword in msg_list:
                if keyword in EmojiIds.name_set:
                    try:
                        guild = await discord.Client.fetch_guild(bot, ServerIds.GUILD_ID)
                        emoji = await guild.fetch_emoji(emoji_id=EmojiIds.name_set[keyword])
                        channel = await discord.Client.fetch_channel(bot, ctx.channel.id)
                        message = await channel.fetch_message(ctx.id)
                        await message.add_reaction(emoji=emoji)
                    except Exception:
                        pass
    except Exception:
        pass


async def restricted_messages(message: Message):
    # noinspection PyBroadException
    try:
        restricted_channels = {ServerIds.BOT_COMMANDS_CHANNEL, ServerIds.HELP}
        if message.guild and len(message.author.roles) == 1 and message.channel.id in restricted_channels:
            match = re.match("https?://", message.clean_content)
            if match:
                await message.delete()
                await message.channel.send(f"<@{message.author.id}>\n"
                                           f"Non-verified members are not allowed to post links to this channel.")
                LogBot.logger.info(f"Message >>{message.clean_content}<< in channel {message.channel}"
                                   f"from {message.author.display_name}({message.author.id}) "
                                   f"deleted according due restrictions.")
    except Forbidden:
        LogBot.logger.warning("Failed to fulfill restriction.")
    except Exception:
        pass
