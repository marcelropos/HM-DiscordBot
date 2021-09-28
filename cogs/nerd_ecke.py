from typing import Union

from discord import Member, User, VoiceState, TextChannel, Embed, Role
from discord.ext.commands import Cog, Bot, group, has_guild_permissions, Context, BadArgument
from discord.ext.tasks import loop

from cogs.bot_status import listener
from cogs.util.ainit_ctx_mgr import AinitManager
from cogs.util.assign_variables import assign_chat
from cogs.util.placeholder import Placeholder
from core.global_enum import CollectionEnum, ConfigurationNameEnum
from core.logger import get_discord_child_logger
from core.predicates import bot_chat
from mongo.primitive_mongo_data import PrimitiveMongoData

bot_channels: set[TextChannel] = set()
nerd_channel = Placeholder()
first_init = True

logger = get_discord_child_logger("Nerd-Ecke")


class NerdEcke(Cog):
    """
    Nerd commands.
    """

    def __init__(self, bot: Bot):
        self.bot: Bot = bot
        self.need_init = True
        if not first_init:
            self.ainit.start()

    @loop()
    async def ainit(self):
        """
        Loads the configuration for the module.
        """
        global bot_channels, nerd_channel
        # noinspection PyTypeChecker
        async with AinitManager(bot=self.bot,
                                loop=self.ainit,
                                need_init=self.need_init,
                                bot_channels=bot_channels) as need_init:
            if need_init:
                nerd_channel.item = await assign_chat(self.bot, ConfigurationNameEnum.NERD_VOICE_CHANNEL)
        logger.info(f"The cog is online.")

    def cog_unload(self):
        logger.warning("Cog has been unloaded.")

    @listener()
    async def on_ready(self):
        global first_init
        if first_init:
            first_init = False
            self.ainit.start()

    @listener()
    async def on_voice_state_update(self, member: Union[Member, User], before: VoiceState, after: VoiceState):
        if before.channel == nerd_channel.item or after.channel == nerd_channel.item:
            role: Role = member.guild.default_role

            members: set[Union[Member, User]] = {member for member in nerd_channel.item.members if not member.bot}

            if members:
                await nerd_channel.item.set_permissions(role, connect=True, reason="Nerd is here.")
            else:
                await nerd_channel.item.set_permissions(role, connect=False, reason="No nerds are here.")

    @group(pass_context=True,
           name="nerd",
           help="Nerd commands.")
    @bot_chat(bot_channels)
    @has_guild_permissions(administrator=True)
    async def nerd(self, ctx: Context):
        if not ctx.invoked_subcommand:
            raise BadArgument
        member: Union[Member, User] = ctx.author
        logger.info(f'User="{member.name}#{member.discriminator}({member.id})", Command="{ctx.message.content}"')

    @nerd.command(pass_context=True,
                  name="voice",
                  brief="Sets the nerd voice channel.",
                  help="The sacred nerd channel, "
                       "which is indisputably the center of everything, can be marked with this command.")
    async def study_channel_voice(self, ctx: Context, channel: int):
        """
        Saves the nerd channel voice chat

        Args:
            ctx: The command context provided by the discord.py wrapper.

            channel: The voice_channel id.
        """

        global nerd_channel
        db = PrimitiveMongoData(CollectionEnum.CHANNELS)
        key = ConfigurationNameEnum.NERD_VOICE_CHANNEL

        find = {key.value: {"$exists": True}}
        if await db.find_one(find):
            await db.update_one(find, {key.value: channel})
        else:
            await db.insert_one({key.value: channel})

        nerd_channel.item = ctx.guild.get_channel(channel)
        embed = Embed(title="Nerd Channel",
                      description=f"Set Voice Channel successfully!")
        await ctx.reply(embed=embed)


def setup(bot: Bot):
    bot.add_cog(NerdEcke(bot))
