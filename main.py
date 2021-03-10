import os
import discord
from discord.ext.commands import *
from pretty_help import PrettyHelp
import re
# noinspection PyProtectedMember
from settings_files._global import DISCORD_BOT_TOKEN, EmojiIds, ServerIds
from settings_files.all_errors import *
from utils.ReadWrite import ReadWrite
from utils.database import DB
from utils.logbot import LogBot
import asyncio

logger = LogBot.logger

intents = discord.Intents.all()

bot = commands.Bot(command_prefix=".!", case_insensitive=True, intents=intents)
bot.help_command = PrettyHelp(show_index=True, sort_commands=True, no_category=True, color=0x00f2ff)

for filename in os.listdir("./cogs"):
    if filename.endswith(".py") and \
            filename != "main.py":
        bot.load_extension(f"cogs.{filename[:-3]}")
        logger.debug(f"Loaded: cogs.{filename[:-3]}")


# noinspection PyBroadException,SqlNoDataSourceInspection,SqlResolve
@bot.after_invoke
async def reply_with_read(ctx: Context):
    try:
        failed = await ctx.guild.fetch_emoji(emoji_id=EmojiIds.Failed)
        success = await ctx.guild.fetch_emoji(emoji_id=EmojiIds.Success)
    except AttributeError:
        failed = "❌"
        success = "✅"
    try:
        bot_id = ctx.bot.user.id
        await asyncio.sleep(0.2)
        if ctx.command_failed:
            await ctx.message.remove_reaction(success, discord.Object(id=bot_id))
            await ctx.message.add_reaction(emoji=failed)
        else:
            await ctx.message.remove_reaction(failed, discord.Object(id=bot_id))
            await ctx.message.add_reaction(emoji=success)

    except AttributeError:
        pass
    except Forbidden:
        pass
    except Exception:
        logger.exception("Could not add reaction:")


# noinspection PyBroadException,SqlNoDataSourceInspection,SqlResolve
@bot.event
async def on_command_error(ctx: Context, e):
    try:
        logger.debug(ctx.message.id)
        if isinstance(e, CommandNotFound):
            await ctx.send(f"<@{ctx.author.id}>\n"
                           f"Command not found. Please edit your message and try again.",
                           delete_after=10)
        elif isinstance(e, UserError) or isinstance(e, MissingRole):
            pass
        else:
            raise e
    except Exception:
        logger.exception("Unhandled exception!")
    finally:
        ctx.command_failed = True
        await reply_with_read(ctx)


# noinspection PyBroadException,SqlNoDataSourceInspection,SqlResolve
@bot.event
async def on_message(ctx):
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

    finally:
        try:
            await bot.process_commands(ctx)
        except Exception:
            logger.exception("An error occurred:")


ReadWrite()  # Init Class
bot.run(DISCORD_BOT_TOKEN())
