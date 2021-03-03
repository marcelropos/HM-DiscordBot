import os
import discord
from discord.ext import commands
from discord.ext.commands import *
import re
from settings import DISCORD_BOT_TOKEN, ReadWrite, BugReport
from utils.utils import EmojiIds, ServerIds

from utils.logbot import LogBot

logger = LogBot.logger

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix="!", case_insensitive=True)
bot.remove_command('help')

for filename in os.listdir("./cogs"):
    if filename.endswith(".py") and \
            filename != "main.py":
        bot.load_extension(f"cogs.{filename[:-3]}")
        logger.debug(f"Loaded: cogs.{filename[:-3]}")


# noinspection PyBroadException
@bot.after_invoke
async def reply_with_read(ctx):
    try:
        try:
            if not ctx.command_failed:
                emoji = await ctx.guild.fetch_emoji(emoji_id=EmojiIds.Success)
            else:
                emoji = await ctx.guild.fetch_emoji(emoji_id=EmojiIds.Failed)
            await ctx.message.add_reaction(emoji=emoji)
        except AttributeError:
            if not ctx.command_failed:
                await ctx.message.add_reaction(emoji="✅")
            else:
                await ctx.message.add_reaction(emoji="❌")

    except Exception as e:
        msg = str(ctx.message.content)
        if msg.startswith("!purge") or \
                msg.startswith("!tmpc"):
            return
        else:
            error = BugReport(bot, ctx, e)
            error.user_details()
            await error.reply()
            raise e


# noinspection PyBroadException
@bot.event
async def on_command_error(ctx, e):
    try:
        emoji = await ctx.guild.fetch_emoji(emoji_id=EmojiIds.Failed)
        await ctx.message.add_reaction(emoji=emoji)
    except Exception:
        await ctx.message.add_reaction(emoji="❌")

    if isinstance(e, commands.CommandNotFound):
        await ctx.send("Befehl nicht gefunden. `!help` für mehr Information.")
        emoji = await ctx.guild.fetch_emoji(emoji_id=EmojiIds.Failed)
        await ctx.message.add_reaction(emoji=emoji)

    elif isinstance(e, UserError) or \
            isinstance(e, discord.ext.commands.BadArgument) or \
            isinstance(e, ModuleError):
        await ctx.send(f"<@!{ctx.message.author.id}>\n`{str(e)}`")

    elif isinstance(e, discord.ext.commands.MissingRole) or isinstance(e, discord.ext.commands.NotOwner):
        await ctx.send(f"<@!{ctx.message.author.id}>\n Du hast nicht genügend Rechte für diesen Befehl.\n`{str(e)}`")

    elif isinstance(e, discord.ext.commands.errors.NoPrivateMessage):
        await ctx.send(f"<@!{ctx.message.author.id}>\n Dieser Befehl kann nicht privat an den Bot gesendet werden."
                       f"\n`{str(e)}`")

    elif isinstance(e, discord.ext.commands.MissingRequiredArgument):
        await ctx.send(f"<@!{ctx.message.author.id}>\n Diese Befehl benötigt noch weitere Argumente.\n`{str(e)}`\n"
                       f"`!help` für mehr Information.")

    elif isinstance(e, discord.ext.commands.ConversionError):
        await ctx.send(f"<@!{ctx.message.author.id}>\n Bitte überprüfe ob der Befehl korrekt ist.")
        channel = bot.get_channel(id=ServerIds.DEBUG_CHAT)
        msg = f"Error:\n```{e}```\n```{ctx.message.content}```"
        await channel.send(msg)

    else:
        error = BugReport(bot, ctx, e)
        error.user_details()
        await error.reply()
        raise e
    return


ReadWrite()  # Init Class
bot.run(DISCORD_BOT_TOKEN())
