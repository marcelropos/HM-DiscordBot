import os
import discord
from discord.ext.commands import *
import re
# noinspection PyProtectedMember
from settings_files._global import DISCORD_BOT_TOKEN, EmojiIds, ServerIds
from settings_files.all_errors import *
from utils.ReadWrite import ReadWrite
from utils.database import DB
from utils.logbot import LogBot
import asyncio

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


# noinspection PyBroadException,SqlNoDataSourceInspection
async def reply_with_read(ctx):
    try:
        ctx_id = ctx.id
    except AttributeError:
        ctx_id = ctx.message.id
    logger.debug(ctx_id)
    error_status = DB.conn.execute("SELECT error_status from comand_ctx WHERE (ctx_id=?)",
                                   (ctx_id,)).fetchone()
    if error_status:
        error_status = error_status[0]
        try:
            if error_status:
                await asyncio.sleep(1)  # prevents being to fast
                try:  # remove_reaction
                    await ctx.clear_reactions()
                    emoji = await ctx.guild.fetch_emoji(emoji_id=EmojiIds.Failed)
                    await ctx.add_reaction(emoji=emoji)
                except AttributeError:
                    await ctx.message.clear_reactions()
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
        logger.debug(ctx.message.id)
        DB.conn.execute(f"UPDATE comand_ctx SET error_status = 1 WHERE ctx_id=?", (ctx.message.id,))
        if isinstance(e, CommandNotFound):
            await ctx.send("Befehl nicht gefunden.")
        elif isinstance(e, UserError) or isinstance(e, MissingRole):
            pass
        else:
            raise e
    except Exception:
        logger.exception("Unhandled exception!")
    finally:
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
        if ctx.content.startswith("!"):
            DB.conn.execute("INSERT INTO comand_ctx(ctx_id) VALUES(?)", (ctx.id,))
        try:
            await bot.process_commands(ctx)
        except Exception:
            logger.exception("An error occurred:")
        finally:
            if ctx.content.startswith("!"):
                await reply_with_read(ctx)


ReadWrite()  # Init Class
bot.run(DISCORD_BOT_TOKEN())
