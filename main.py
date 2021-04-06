import os
import discord
from discord.ext.commands import *
from pretty_help import PrettyHelp
from settings_files._global import DISCORD_BOT_TOKEN, EmojiIds, ServerIds, COMMAND_PREFIX
from settings_files.all_errors import *
from utils.logbot import LogBot
from utils.message_process import reactions, restricted_messages
import asyncio

logger = LogBot.logger

intents = discord.Intents.all()

bot = commands.Bot(command_prefix=COMMAND_PREFIX(), case_insensitive=True, intents=intents)
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
    except NotFound:
        pass
    except Exception:
        logger.exception("Could not add reaction:")


# noinspection PyBroadException,SqlNoDataSourceInspection,SqlResolve
@bot.event
async def on_command_error(ctx: Context, error: CommandInvokeError):
    error = error.original
    try:
        if isinstance(error, CommandNotFound):
            await ctx.send(f"<@{ctx.author.id}>\n"
                           f"Command not found. Please edit your message and try again.",
                           delete_after=10)
        elif isinstance(error, UserError) \
                or isinstance(error, MissingRole) \
                or isinstance(error, CheckFailure):
            pass

        elif isinstance(error, MissingRequiredArgument):
            await ctx.send("At least one argument is missing.\n"
                           "Please read the help below and try again.")
            await ctx.send_help(ctx.command)

        elif isinstance(error, BadArgument):
            await ctx.send("Your argument could not be processed.\n"
                           "Please read the help below and try again.")
            await ctx.send_help(ctx.command)
        else:
            raise error
    except Exception:
        logger.exception("Unhandled exception!")
    finally:
        ctx.command_failed = True
        await reply_with_read(ctx)


# noinspection PyBroadException,SqlNoDataSourceInspection,SqlResolve
@bot.event
async def on_message(message):
    try:
        await asyncio.gather(
            reactions(message, bot),
            restricted_messages(message),
            bot.process_commands(message),
            return_exceptions=True
        )
    except Exception:
        LogBot.logger.exception("An unhandled exception is occurred")


bot.run(DISCORD_BOT_TOKEN())
