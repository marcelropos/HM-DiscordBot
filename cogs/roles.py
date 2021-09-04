from discord import TextChannel
from discord.ext.commands import Cog, Bot, Context, command
from discord.ext.tasks import loop

from cogs.bot_status import listener
from cogs.util.ainit_ctx_mgr import AinitManager
from cogs.util.assign_variables import assign_role
from cogs.util.placeholder import Placeholder
from core.global_enum import ConfigurationNameEnum
from core.predicates import has_not_role, has_role_plus, bot_chat

first_init = True
news = Placeholder()
nsfw = Placeholder()
verified = Placeholder()
bot_channels: set[TextChannel] = set()


class Roles(Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
        self.need_init = True
        if not first_init:
            self.ainit.start()

    @listener()
    async def on_ready(self):
        global first_init
        if first_init:
            first_init = False
            self.ainit.start()

    @loop()
    async def ainit(self):
        """
        Loads the configuration for the module.
        """
        global news, nsfw, verified, bot_channels
        # noinspection PyTypeChecker
        async with AinitManager(bot=self.bot,
                                loop=self.ainit,
                                need_init=self.need_init,
                                bot_channels=bot_channels,
                                verified=verified) as need_init:
            if need_init:
                news.item = await assign_role(self.bot, ConfigurationNameEnum.NEWSLETTER)
                nsfw.item = await assign_role(self.bot, ConfigurationNameEnum.NSFW)

    # Not Safe For Work

    @command(name="nsfw-add",
             help="Add nsfw role")
    @has_role_plus(verified)
    @has_not_role(nsfw)
    @bot_chat(bot_channels)
    async def nsfw_add(self, ctx: Context):
        global nsfw
        await ctx.author.add_roles(nsfw.item, reason="request by user")
        await ctx.reply(content=f"<@{ctx.author.id}> added you to the <@&{nsfw.item.id}> role")

    @command(name="nsfw-rem",
             help="Remove nsfw role")
    @has_role_plus(nsfw)
    @bot_chat(bot_channels)
    async def nsfw_rem(self, ctx: Context):
        global nsfw
        await ctx.author.remove_roles(nsfw.item, reason="request by user")
        await ctx.reply(content=f"<@{ctx.author.id}> removed you from the <@&{nsfw.item.id}> role")

    # News

    @command(name="news-add",
             help="Add news role")
    @has_role_plus(verified)
    @has_not_role(news)
    @bot_chat(bot_channels)
    async def news_add(self, ctx: Context):
        global news
        await ctx.author.add_roles(news.item, reason="request by user")
        await ctx.reply(content=f"<@{ctx.author.id}> added you to the <@&{news.item.id}> role")

    @command(name="news-rem",
             help="Remove news role")
    @has_role_plus(news)
    @bot_chat(bot_channels)
    async def news_rem(self, ctx: Context):
        global news
        await ctx.author.remove_roles(news.item, reason="request by user")
        await ctx.reply(content=f"<@{ctx.author.id}> removed you from the <@&{news.item.id}> role")


def setup(bot: Bot):
    bot.add_cog(Roles(bot))
