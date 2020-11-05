# noinspection PyUnresolvedReferences
import discord
from discord.ext import commands
# noinspection PyUnresolvedReferences
import os
from settings import ServerIds, DISCORD_BOT_TOKEN, ReadWrite
from utils import UserError, ModuleError, EmojiIds
from discord.ext.commands import CommandNotFound
import time

bot = commands.Bot(command_prefix="!")
bot.remove_command('help')

for filename in os.listdir("./cogs"):
    if filename.endswith(".py") and \
            filename != "main.py":
        bot.load_extension(f"cogs.{filename[:-3]}")


class BugReport:

    # noinspection PyShadowingNames
    def __init__(self, bot, ctx, e):
        self.bot = bot
        self.ctx = ctx
        self.channel = bot.get_channel(id=ServerIds.DEBUG_CHAT)
        self.embed = discord.Embed(colour=discord.Colour(0x12d4ca),
                                   description="")

        self.embed.set_author(name="Bug Report")
        self.embed.set_footer(text=f"Erstellt am {time.strftime('%d.%m.%Y %H:%M:%S')}")

        self.embed.add_field(name="Error:",
                             value=e,
                             inline=False)

    def user_details(self):
        self.embed.add_field(name="Author",
                             value=f"Name: `{self.ctx.author.name}`\n"
                                   f"ID: `{self.ctx.author.id}`",
                             inline=False)

        self.embed.add_field(name="Command:",
                             value=f"`{self.ctx.message.content}`",
                             inline=False)

        try:
            roles = ""
            for x in self.ctx.author.roles:
                roles += f"{x.name}\n"

            self.embed.add_field(name="Roles:",
                                 value=roles,
                                 inline=False)
        except AttributeError:
            pass

        if self.ctx.guild:
            guild_id = self.ctx.guild.id
            channel_id = self.ctx.channel.id
            message_id = self.ctx.message.id
            value = f"https://discordapp.com/channels/{guild_id}/{channel_id}/{message_id}"

        else:
            value = "Privatnachricht"
        self.embed.add_field(name="Link to message",
                             value=value,
                             inline=False)

    async def reply(self):
        await self.ctx.send("Nicht klassifizierter Fehler. Ein Report wurde erstellt.")
        await self.channel.send(embed=self.embed)


@bot.after_invoke
async def reply_with_read(ctx):
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
        if msg.startswith("!purge"):
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

    if isinstance(e, CommandNotFound):
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
