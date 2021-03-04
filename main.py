import os
import discord
from discord.ext import commands
from discord.ext.commands import *
import re
from settings_files._global import DISCORD_BOT_TOKEN, EmojiIds, ServerIds
from settings_files.all_errors import *
from utils.ReadWrite import ReadWrite
from utils.embed_generator import BugReport
from utils.database import DB
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
async def reply_with_read(ctx):
    try:
        ctx_id = ctx.id
    except AttributeError:
        ctx_id = ctx.message.id
    logger.debug(ctx_id)

    error_status = DB.conn.execute("SELECT error_status from comand_ctx WHERE (ctx_id=? AND is_command=?)",
                                   (ctx_id, 1)).fetchone()
    if error_status:
        error_status = error_status[0]
        try:
            if error_status:
                try:
                    emoji = await ctx.guild.fetch_emoji(emoji_id=EmojiIds.Failed)
                    await ctx.add_reaction(emoji=emoji)
                except AttributeError:
                    emoji = await ctx.guild.fetch_emoji(emoji_id=EmojiIds.Failed)
                    await ctx.message.add_reaction(emoji=emoji)
                except Exception:
                    try:
                        await ctx.add_reaction(emoji="❌")
                    except AttributeError:
                        await ctx.message.add_reaction(emoji="❌")

            else:
                try:
                    emoji = await ctx.guild.fetch_emoji(emoji_id=EmojiIds.Success)
                    await ctx.add_reaction(emoji=emoji)
                except AttributeError:
                    emoji = await ctx.message.guild.fetch_emoji(emoji_id=EmojiIds.Success)
                    await ctx.message.add_reaction(emoji=emoji)
                except Exception:
                    try:
                        await ctx.add_reaction(emoji="✅")
                    except AttributeError:
                        await ctx.message.add_reaction(emoji="✅")

            DB.conn.execute("DELETE from comand_ctx WHERE (ctx_id=?)",
                            (ctx_id,))

        except Exception:
            logger.exception("Could not add reaction:")


# noinspection PyBroadException,SqlNoDataSourceInspection
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


# noinspection PyBroadException
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
