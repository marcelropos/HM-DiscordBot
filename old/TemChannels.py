# noinspection PyUnresolvedReferences
import discord
from old.ServerTools import token


class TmpChannels:
    tmp_dict = dict()

    def __init__(self, message=None, msg=None):
        self.message = message
        self.msg = msg

    @staticmethod
    def get_category(message, name):
        for x in message.guild.categories:
            if x.name == name:
                return x
        return None

    @classmethod
    def add_channel(cls, text, voice):
        c_token = token()
        cls.tmp_dict[c_token] = (text, voice)
        return c_token

    @classmethod
    async def rem_channel(cls):
        for x in cls.tmp_dict:
            text, voice = cls.tmp_dict[x]
            members = voice.members
            if len(members) == 0:
                await text.delete()
                await voice.delete()

    async def mk_channel(self):
        msg = self.message.content
        msg = str(msg)
        msg = msg.split(" ")
        member = await self.message.guild.fetch_member(self.message.author.id)
        voice_c = await self.message.guild.create_voice_channel(msg[2], category=self.get_category(self.message, "Custom"))
        text_c = await self.message.guild.create_text_channel(msg[2], category=self.get_category(self.message, "Custom"))
        permissions = text_c.permissions_for(member=member)
        permissions.Permissions.none()

        # noinspection PyUnusedLocal
        c_token = TmpChannels.add_channel(text_c, voice_c)
        await member.move_to(voice_c)
        #  await text_c.send(f"Mit >!move to {c_token}< können auch deine Freunde den Channel betreten.")
