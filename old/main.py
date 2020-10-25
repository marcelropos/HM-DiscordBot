import re
#  import time

import discord

from old.RoleManager import ServerRoles
from old.ServerHelp import ServerHelp
from old.TemChannels import TmpChannels


# noinspection PyMethodMayBeStatic
class MyClient(discord.Client):
    # Einloggen
    # noinspection PyMethodMayBeStatic,PyAttributeOutsideInit
    async def on_ready(self):
        activity = discord.Game(name="Hört auf !help")
        await client.change_presence(status=discord.Status.online, activity=activity)
        channel = client.get_channel(id=762736695116169217)
        await channel.send("System online, waiting for your demands.")

    # Wenn Nachricht gepostet wird
    # noinspection PyMethodMayBeStatic,PyUnusedLocal
    async def on_message(self, message):
        if message.author == client.user:
            return

        if message.channel.id == 762736695116169217:
            print(message.content)

        if message.content.startswith("!"):
            emoji = await client.guilds[0].fetch_emoji(emoji_id=762601788200321025)  # emoji=:read:
            await message.add_reaction(emoji=emoji)

            if message.content.startswith("!members"):
                async for member in message.guild.fetch_members(limit=None):
                    print(member.name, member.roles)

            elif message.content.startswith("!count"):
                i = 0
                async for _ in message.guild.fetch_members(limit=None):
                    i += 1
                await message.channel.send(i)

            msg = str(message.content)
            msg = msg.lower()

            if message.content.startswith("!get role ids") and message.channel.id == 762736695116169217:
                for x in message.guild.roles:
                    await message.channel.send(f"{x.name}: {x.id}")

            elif message.content.startswith("!get my id"):
                await message.channel.send(f"<@!{message.author.id}>: {message.author.id}")

            elif message.content.startswith("!turn off"):
                if message.author.id == 259082447491301377:
                    activity = discord.Game(name="Geht schlafen.", type=3)
                    await client.change_presence(status=discord.Status.offline, activity=activity)
                    await message.channel.send("Okay bis später")
                    await self.close()

            #  only to test
            elif message.content.startswith("!msg channel") and message.channel.id == 762736695116169217:
                channel = client.get_channel(id=762736695116169217)
                await channel.send("msg not reply")

            elif "!add role" in msg:
                module = ServerRoles(message, msg)
                await module.start()

            elif msg == "!help":
                module = ServerHelp(message, msg)
                await module.help()

            elif "!my-data" in msg:
                module = ServerHelp(message, msg)
                await module.my_data()

            elif "!rules" in msg:
                module = ServerHelp(message, msg)
                await module.rules()

            elif "!mk channel" in msg:
                module = TmpChannels(message, msg)
                await module.mk_channel()

            elif "!move to" in msg:
                return
                # noinspection PyUnreachableCode
                matches = re.finditer(r"[0-9]{6}]", msg)
                for x in matches:
                    print(x)
                    start, end = x.span()
                    c_token = msg[start:end]

                if self.tmp_channel.exist_channel(c_token):
                    text, voice = self.tmp_channel.exist_channel(c_token)
                    member = await message.guild.fetch_member(message.author.id)
                    member.move_to(voice)

            elif "!" == msg:
                return

            else:
                print("Anfrage nicht verstanden")

        elif message.channel.id == 762673629946314775:
            emoji = await client.guilds[0].fetch_emoji(emoji_id=762601788200321025)  # emoji=:read:
            await message.add_reaction(emoji=emoji)
            await message.channel.send(
                f"Hallo <@!{message.author.id}>,\n"
                f"mit ```!help``` bekommst du eine Übersicht, was ich für dich tun kann.")

    # await message.channel.send(message.author.guild.members)

    # noinspection PyUnusedLocal,PyMethodMayBeStatic,PyUnreachableCode
    async def on_raw_reaction_add(self, payload):
        return
        print(str(payload))
        channel = client.get_channel(payload.channel_id)
        user = client.get_user(payload.user_id)
        message = await channel.fetch_message(payload.message_id)
        #  await channel.send(str(user) + " reacted on " + message.content + " with " + str(payload.emoji))

    # noinspection PyUnusedLocal
    async def on_voice_state_update(self, member, before, after):
        _ = await TmpChannels.rem_channel()


TmpChannels()  # Init class variable for temp Channels

client = MyClient()
with open("token.txt", "r") as token:
    try:
        client.run(token.read())
    except Exception:
        pass
