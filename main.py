import asyncio
import os

import discord
from discord import Embed
from discord.ext import commands
from discord.ext.commands import Context, CommandInvokeError, CommandNotFound
from pretty_help import PrettyHelp

import core.logger as logger
from core.error.error_handlers import error_handler

intents = discord.Intents.all()

bot = commands.Bot(command_prefix="!", case_insensitive=True, intents=intents)
bot.help_command = PrettyHelp(show_index=True, sort_commands=True, no_category=True, color=0x00f2ff)


async def load_cogs():
    async with bot:
        for filename in os.listdir("./cogs"):
            if filename.endswith(".py") and filename != "upgrade.py":
                await bot.load_extension(f"cogs.{filename[:-3]}")
                logger.get_discord_child_logger("cogs").info(f"Loaded: cogs.{filename[:-3]}")
        await bot.start(os.environ["TOKEN"])


@bot.event
async def on_command_error(ctx: Context, error):
    if isinstance(error, CommandInvokeError):
        error = error.original
    if isinstance(error, CommandNotFound):
        embed = Embed(title="Command not Found")
        command: str = ctx.message.content
        embed.add_field(name="Command", value=f"`{command}`", inline=False)
        embed.add_field(name="Cause", value=error.args[0], inline=False)
        embed.add_field(name="Solution",
                        value=f"I'll send you a help overview.\n"
                              f"You can use {ctx.bot.command_prefix}help to display available commands in future.\n",
                        inline=False)
        await ctx.reply(embed=embed, delete_after=60)
        await ctx.send_help()
        return
    await error_handler(ctx, error)


asyncio.run(load_cogs())
