# noinspection PyUnresolvedReferences
import discord
from discord.ext import commands
# noinspection PyUnresolvedReferences
import os
from settings import ServerIds, DISCORD_BOT_TOKEN, ReadWrite
from utils import UserError, ModuleError, EmojiIds
from discord.ext.commands import CommandNotFound

bot = commands.Bot(command_prefix="!")
bot.remove_command('help')

for filename in os.listdir("./cogs"):
    if filename.endswith(".py") and \
            filename != "main.py":
        bot.load_extension(f"cogs.{filename[:-3]}")


@bot.after_invoke
async def reply_with_read(ctx):
    if not ctx.command_failed:
        emoji = await ctx.guild.fetch_emoji(emoji_id=EmojiIds.Success)
    else:
        emoji = await ctx.guild.fetch_emoji(emoji_id=EmojiIds.Failed)
    await ctx.message.add_reaction(emoji=emoji)


@bot.event
async def on_command_error(ctx, e):
    if isinstance(e, CommandNotFound):
        await ctx.send("Befehl nicht gefunden. `!help` für mehr Information.")
        emoji = await ctx.guild.fetch_emoji(emoji_id=EmojiIds.Failed)
        await ctx.message.add_reaction(emoji=emoji)

    elif isinstance(e, UserError) or\
            isinstance(e, discord.ext.commands.BadArgument) or\
            isinstance(e, ModuleError):
        await ctx.send(f"<@!{ctx.message.author.id}>\n`{str(e)}`")

    elif isinstance(e, discord.ext.commands.MissingRole):
        await ctx.send(f"<@!{ctx.message.author.id}>\n Du hast nicht genügend Rechte für diesen Befehl.\n`{str(e)}`")

    elif isinstance(e, discord.ext.commands.errors.NoPrivateMessage):
        await ctx.send(f"<@!{ctx.message.author.id}>\n Dieser Befehl kann nicht privat an den Bot gesendet werden."
                       f"\n`{str(e)}`")

    elif isinstance(e, discord.ext.commands.MissingRequiredArgument):
        await ctx.send(f"<@!{ctx.message.author.id}>\n Diese Befehl benötigt noch weitere Argumente.\n`{str(e)}`\n"
                       f"`!help` für mehr Information.")

    else:
        await ctx.send("Nicht klassifizierter Fehler. Ein Report wurde erstellt.")
        channel = bot.get_channel(id=ServerIds.DEBUG_CHAT)
        msg = f"Error:\n```{e}```\n```{ctx.message.content}```"
        await channel.send(msg)
        raise e
    return

ReadWrite()  # Init Class
bot.run(DISCORD_BOT_TOKEN())
