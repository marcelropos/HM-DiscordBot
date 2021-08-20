from discord import TextChannel
from discord.ext.commands import Cog, Bot, Context, command
from discord.ext.tasks import loop

from cogs.botStatus import listener
from cogs.util.accepted_chats import assign_role, assign_accepted_chats
from cogs.util.ainit_ctx_mgr import AinitManager
from cogs.util.place_holder import Placeholder
from core.globalEnum import ConfigurationNameEnum
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
        async with AinitManager(self.bot, self.ainit, self.need_init) as need_init:
            if need_init:
                await assign_accepted_chats(self.bot, bot_channels)

                verified.item = await assign_role(self.bot, ConfigurationNameEnum.STUDENTY)
                news.item = await assign_role(self.bot, ConfigurationNameEnum.NEWSLETTER)
                nsfw.item = await assign_role(self.bot, ConfigurationNameEnum.NSFW)

    # ===================Not Safe For Work=================== #

    @command(name="nsfw-add",
             help="Add nsfw role")
    @has_role_plus(verified)
    @has_not_role(nsfw)
    @bot_chat(bot_channels)
    async def nsfw_add(self, ctx: Context):
        global nsfw
        await ctx.author.add_roles(nsfw.item, reason="request by user")

    @command(name="nsfw-rem",
             help="Remove nsfw role")
    @has_role_plus(nsfw)
    @bot_chat(bot_channels)
    async def nsfw_rem(self, ctx: Context):
        global nsfw
        await ctx.author.remove_roles(nsfw.item, reason="request by user")

    # ===================News=================== #

    @command(name="news-add",
             help="Add news role")
    @has_role_plus(verified)
    @has_not_role(news)
    @bot_chat(bot_channels)
    async def news_add(self, ctx: Context):
        global news
        await ctx.author.add_roles(news.item, reason="request by user")

    @command(name="news-rem",
             help="Remove news role")
    @has_role_plus(news)
    @bot_chat(bot_channels)
    async def news_rem(self, ctx: Context):
        global news
        await ctx.author.remove_roles(news.item, reason="request by user")


def setup(bot: Bot):
    bot.add_cog(Roles(bot))
