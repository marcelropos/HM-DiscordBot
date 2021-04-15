from typing import Union

import discord
from aiosqlite import Cursor, Connection
from discord import Member, Message, PermissionOverwrite, User
from discord.abc import GuildChannel
from discord.ext.commands import Context, Bot

from utils.logbot import LogBot
# noinspection PyUnresolvedReferences
from utils.tempchannels.database import TempChannelDB


class MaintainChannel:

    @staticmethod
    async def update(ctx: Context, new_token, bot, db: Connection):
        LogBot.logger.debug("Generate new token")

        cursor: Cursor = await db.execute(f"""SELECT token FROM TempChannels where discordUser=?""",
                                          (str(ctx.author.id),))
        token = await cursor.fetchone()

        cursor: Cursor = await db.execute(
            f"""SELECT message_id, channel_id, member_id FROM Invites where token=?""",
            (token[0],))
        invites = await cursor.fetchall()
        for message_id, channel_id, user_id in invites:
            await MaintainChannel.delete_invite(user_id, channel_id, message_id, bot, db)

        await db.execute(f"""UPDATE TempChannels SET token=? where discordUser=?""",
                         (new_token, ctx.author.id))

    # noinspection PyBroadException
    @staticmethod
    async def save_invite(member: Member, message: Message, token: int, db):

        LogBot.logger.debug(f"Save invite with token {token}")
        await db.execute(f"""INSERT into Invites(message_id,token,member_id,channel_id)
                    VALUES(?,?,?,?)""", (message.id, token, member.id, message.channel.id))

    @staticmethod
    async def delete_invite(member_id: int, channel_id: int, message_id: int, bot: Bot,
                            db: Connection):
        # noinspection PyBroadException
        try:
            member = await bot.fetch_user(member_id)
            embed = MaintainChannel.invite_embed(member, "Expired")
            channel = await discord.Client.fetch_channel(bot, channel_id)
            message = await channel.fetch_message(message_id)
            await message.edit(embed=embed)
        except Exception:
            LogBot.logger.exception("Can't edit message: ")
        finally:
            await db.execute(f"""delete from Invites where message_id=?""", (message_id,))

    @staticmethod
    async def rem_channels(member, bot: Bot, db: Connection):
        cursor: Cursor = await db.execute(f"""SELECT * FROM TempChannels""")
        channels = await cursor.fetchall()

        for user_id, text_channel_id, voice_channel_id, token in channels:
            # noinspection PyBroadException
            try:
                if len(member.guild.get_channel(voice_channel_id).members) == 0:
                    await MaintainChannel.rem_channel(user_id, text_channel_id, voice_channel_id, token, bot, db)
            except Exception:
                LogBot.logger.exception("Could not get user")

    # noinspection PyBroadException
    @staticmethod
    async def rem_channel(user_id: int, text: int, voice: int, token: int, bot: Bot,
                          db: Connection):
        LogBot.logger.debug("Delete Channel")

        cursor: Cursor = await db.execute(f"""SELECT message_id, channel_id FROM Invites where token=?""",
                                          (token,))
        invites = await cursor.fetchall()

        for message_id, channel_id in invites:
            await MaintainChannel.delete_invite(user_id, channel_id, message_id, bot, db)
            await db.execute(f"""delete from TempChannels where discordUser=?""", (user_id,))
        try:
            text = bot.get_channel(text)
            await text.delete(reason="No longer used")
        except Exception:
            LogBot.logger.exception("Can't delete text channel")
        try:
            voice = bot.get_channel(voice)
            await voice.delete(reason="No longer used")
        except Exception:
            LogBot.logger.exception("Can't delete voice channel")

    # noinspection PyDunderSlots,PyUnresolvedReferences
    @staticmethod
    async def join(member: Member, voice_c: GuildChannel, text_c: GuildChannel):
        overwrite: PermissionOverwrite = discord.PermissionOverwrite()
        overwrite.connect = True
        overwrite.read_messages = True

        await voice_c.set_permissions(member,
                                      overwrite=overwrite,
                                      reason="access by token")

        await text_c.set_permissions(member,
                                     overwrite=overwrite,
                                     reason="access by token")

        # noinspection PyBroadException
        try:
            await member.move_to(voice_c, reason="want to join this Channel.")
        except Exception:
            pass

    @staticmethod
    def invite_embed(user: Union[Member, User], token):
        embed = discord.Embed(title="Temporary channel invite",
                              colour=discord.Colour(0x12d4ca),
                              description="")

        embed.add_field(name="Creator",
                        value=f"{user.display_name}",
                        inline=False)

        embed.add_field(name="Token",
                        value="The reaction with 🔓 is equivalent to token input.",
                        inline=False)

        embed.add_field(name="Token",
                        value=token,
                        inline=False)
        return embed
