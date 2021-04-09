import asyncio
import os

import discord
from discord import Role
from discord.ext import commands
from discord.ext.commands import *
from pretty_help import PrettyHelp

from settings_files._global import DISCORD_BOT_TOKEN, EmojiIds, COMMAND_PREFIX, ServerIds, Messages
from settings_files.all_errors import *
from utils.embed_generator import BugReport, error_report
from utils.logbot import LogBot
from utils.message_process import reactions, restricted_messages

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
async def on_command_error(ctx: Context, error):
    if isinstance(error, CommandInvokeError):
        error = error.original

    try:
        if isinstance(error, CommandNotFound):
            await ctx.send(f"<@{ctx.author.id}>\n"
                           f"Command not found. Please edit your message and try again.",
                           delete_after=10)

        elif isinstance(error, MissingRequiredArgument):
            await ctx.send("At least one argument is missing.\n"
                           "Please read the help below and try again.")
            await ctx.send_help(ctx.command)

        elif isinstance(error, BadArgument):
            await ctx.send("Your argument could not be processed.\n"
                           "Please read the help below and try again.")
            await ctx.send_help(ctx.command)
        elif isinstance(error, MissingPermissions):
            await ctx.send("This bot hab not the needed permissions to fulfill your demand.")

        elif isinstance(error, (WrongChatError, NoPrivateMessage)):
            try:
                await ctx.message.delete()
            except Forbidden:
                pass
            try:
                await ctx.send(f"<@!{ctx.author.id}>\n"
                               f"This command may not be used in this chat.\n"
                               f"Please use the chat provided for this purpose. <#{ServerIds.BOT_COMMANDS_CHANNEL}>.",
                               delete_after=60)
            except Forbidden:
                pass

        elif isinstance(error, IncorrectConfigurationException):
            embed = BugReport(bot, ctx, error)
            await embed.reply(Messages.INCORRECT_CONFIGURATION)

        elif isinstance(error, MissingRole):
            error: MissingRole
            role: Role = discord.utils.get(ctx.guild.roles, id=error.missing_role)
            await error_report(
                ctx=ctx,
                reason=f"You need the <@&{role.id}> Role to run this command.",
                solution="Ask for the necessary permissions."
            )

        elif isinstance(error, local_only_handled_errors()):
            pass

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
