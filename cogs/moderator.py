from typing import Union

from discord import TextChannel, User, Member, Embed
from discord.ext.commands import Cog, Bot, command, Context, cooldown, BucketType
from discord.ext.tasks import loop

from cogs.bot_status import listener
from cogs.util.ainit_ctx_mgr import AinitManager
from cogs.util.assign_variables import assign_role, assign_accepted_chats, assign_chat
from cogs.util.placeholder import Placeholder
from core.global_enum import ConfigurationNameEnum
from core.logger import get_discord_child_logger
from core.predicates import bot_chat, has_role_plus

bot_channels: set[TextChannel] = set()
verified = Placeholder()
moderator = Placeholder()
restricted = Placeholder()
mod_chat = Placeholder()
first_init = True

logger = get_discord_child_logger("Moderator")


class Moderator(Cog):
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
        global bot_channels, verified, moderator, moderator, rate, per
        # noinspection PyTypeChecker
        async with AinitManager(self.bot, self.ainit, self.need_init) as need_init:
            if need_init:
                await assign_accepted_chats(self.bot, bot_channels)

                verified.item = await assign_role(self.bot, ConfigurationNameEnum.STUDENTY)
                moderator.item = await assign_role(self.bot, ConfigurationNameEnum.MODERATOR_ROLE)
                restricted.item = await assign_role(self.bot, ConfigurationNameEnum.RESTRICTED)
                mod_chat.item = await assign_chat(self.bot, ConfigurationNameEnum.MOD_CHAT)

    # commands

    @command(brief="Verify a mentioned user")
    @bot_chat(bot_channels)
    @has_role_plus(moderator)
    async def verify(self, ctx: Context, member):  # parameter only for pretty help.
        """
        Assigns a role to the mentioned member.

        Args:
            ctx: The command context provided by the discord.py wrapper.

            member: The member who is to receive a role.


        """
        member: Union[Member, User] = ctx.message.mentions[0]
        await member.add_roles(verified.item, reason=f"{str(ctx.author)}")
        logger.info(f"User {str(member)} was verified by {str(ctx.author)}")

    @command(help="Place or remove a restriction on the mentioned user.")
    @bot_chat(bot_channels)
    @has_role_plus(moderator)
    async def restrict(self, ctx: Context, mode: bool, member):  # parameter only for pretty help.
        global mod_chat, restricted
        """
        Assigns a role to the mentioned member.

        Args:
            ctx: The command context provided by the discord.py wrapper.

            mode: True if the role should be added, false if it should be removed.

            member: The member who is to receive a role.

        """
        member: Union[Member, User] = ctx.message.mentions[0]
        title = "User restriction"
        if mode:
            await member.add_roles(restricted.item, reason=f"{str(ctx.author)}")
            embed = Embed(title=title,
                          description=f"User {str(ctx.author)} has applied the restriction to {str(member)}.")
        else:
            await member.remove_roles(restricted.item, reason=f"{str(ctx.author)}")
            embed = Embed(title=title,
                          description=f"User {str(ctx.author)} has removed the restriction from {str(member)}.")

        await mod_chat.item.send(embed=embed)

    @command(brief="Write an anonymous message to the mods.",
             help="You can send an anonymous message to the mods twice an hour.")
    @cooldown(2, 3600, BucketType.user)
    async def mail(self, ctx: Context, *, message: str):
        embed = Embed(title="Mod Mail",
                      description=message)
        await mod_chat.item.send(embed=embed)
        await ctx.reply(content="The following embed has been sent to the moderator chat.",
                        embed=embed)


def setup(bot: Bot):
    bot.add_cog(Moderator(bot))
