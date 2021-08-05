import os

import discord
from discord.ext import commands
from discord.ext.commands import Context, CommandInvokeError
from pretty_help import PrettyHelp

import core.logger as logger
from core.error.error_handlers import error_handler

intents = discord.Intents.all()

bot = commands.Bot(command_prefix="!", case_insensitive=True, intents=intents)
bot.help_command = PrettyHelp(show_index=True, sort_commands=True, no_category=True, color=0x00f2ff)

for filename in os.listdir("./cogs"):
    if filename.endswith(".py") and \
            filename != "main.py":
        bot.load_extension(f"cogs.{filename[:-3]}")
        logger.get_discord_child_logger("cogs").info(f"Loaded: cogs.{filename[:-3]}")


@bot.event
async def on_command_error(ctx: Context, error):
    if isinstance(error, CommandInvokeError):
        error = error.original
    await error_handler(ctx, error)


bot.run(os.environ["TOKEN"])
