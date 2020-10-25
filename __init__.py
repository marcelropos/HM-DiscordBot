# noinspection PyUnresolvedReferences
import discord
from discord.ext import commands
# noinspection PyUnresolvedReferences
import os
from settings import ServerIds, DISCORD_BOT_TOKEN, ReadWrite
from utils import UserError, ModuleError
from discord.ext.commands import CommandNotFound

bot = commands.Bot(command_prefix="!")
bot.remove_command('help')

for filename in os.listdir("./cogs"):
    if filename.endswith(".py") and \
            filename != "__init__.py":
        bot.load_extension(f"cogs.{filename[:-3]}")


@bot.after_invoke
async def reply_with_read(ctx):
    if not ctx.command_failed:
        await ctx.message.add_reaction("✅")
    else:
        await ctx.message.add_reaction("❌")


@bot.event
async def on_command_error(ctx, e):
    if isinstance(e, CommandNotFound):
        await ctx.send("Befehl nicht gefunden.")
        await ctx.message.add_reaction("❌")
    elif isinstance(e, UserError) or\
            isinstance(e, discord.ext.commands.BadArgument) or\
            isinstance(e, ModuleError):
        await ctx.send(f"<@!{ctx.message.author.id}>\n{str(e)}")
    elif isinstance(e, discord.ext.commands.MissingRole):
        await ctx.send(f"<@!{ctx.message.author.id}>\n Du hast nicht genügend Rechte für diesen Befehl.")
    elif isinstance(e, discord.ext.commands.errors.NoPrivateMessage):
        await ctx.send(f"<@!{ctx.message.author.id}>\n Dieser Befehl kann nicht privat an den Bot gesendet werden.")
    else:
        await ctx.send("Nicht klassifizierter Fehler.")
        channel = bot.get_channel(id=ServerIds.DEBUG_CHAT)
        await channel.send(e)
        raise e
    return

ReadWrite()  # Init Class
bot.run(DISCORD_BOT_TOKEN())
