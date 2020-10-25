import discord
import re


class ServerRoles:

    def __init__(self, message, msg):
        self.msg = msg
        self.message = message
        parameters = re.split(" ", msg)
        self.role = parameters[2]

        self.study = [("!add role informatik", "Informatik"),
                      ("!add role wirtschaftsinformatik", "Wirtschaftsinformatik"),
                      ("!add role data-science", "data-Science")]

        self.group = [("!add role if1a", "IF1A"),
                      ("!add role if1b", "IF1B"),
                      ("!add role ib1a", "IB1A"),
                      ("!add role ib1b", "IB1B"),
                      ("!add role ib1c", "IB1C"),
                      ("!add role ib1d", "IB1D")]

    async def start(self):
        if "!add role -help" in self.msg:
            await self.help()
            return

        for x in self.study:
            if x[0] in self.msg:
                await self.add_study(x[1])
                return

        for x in self.group:
            if x[0] in self.msg:
                await self.add_group(x[1])
                return

        await self.message.channel.send(f"Leider habe ich deine Anfrage nicht verstanden <@!{self.message.author.id}>."
                                        f"\nVersuche es doch mal mit ```!add role -help```")

    async def help(self):
        embed = discord.Embed(title="Rollen", colour=discord.Colour(0x12d4ca),
                              description="Mit Rollen kann jeder auf dem Server sehen, zu welchem "
                                          "Studiengang "
                                          "oder zu welcher Gruppe du angehörst.\n\nGleichzeitig erhält du "
                                          "Zugang zu den Chats, die nur diesem Studiengang bzw. dieser "
                                          "Gruppe "
                                          "angehören.")
        embed.set_author(name="Marcel (Anthony)")
        embed.set_footer(text="Erstellt am 07.10.2020 19:00 Uhr")
        embed.add_field(name="Informatik:",
                        value="```!add role informatik``` Exclusiv für diesen Studiengang stehen noch "
                              "folgende Befehle zur Verfügung. ```!add role IF1A``` ```!add role IF1B```")
        embed.add_field(name="Wirtschaftsinformatik:",
                        value="```!add role wirtschaftsinformatik```Exclusiv für diesen Studiengang stehen "
                              "noch folgende Befehle zur Verfügung ```!add role IB1A``` ```!add role "
                              "IB1B``` "
                              "```!add role IB1C``` ```!add role IB1D```")
        embed.add_field(name="data-Science:", value="```!add role data-science``` ")
        await self.message.channel.send(content=f"<@!{self.message.author.id}> vielen Dank für deine Frage.",
                                        embed=embed)

    @staticmethod
    def no_study(got_roles):
        studiengang = [762565228826329138,  # Wirtschaftsinformatik
                       762563012614684713,  # data Sience
                       762562978523906070]  # Informatik
        for x in got_roles:
            for y in studiengang:
                if x.id == y:
                    return False
        return True

    @staticmethod
    def no_group(got_roles):
        groups = [763714090454745098,  # IF1A
                  763714190195294269,  # IF1B
                  763714403009953823,  # IB1A
                  763714479916711957,  # IB1B
                  763714528424361995,  # IB1C
                  763714568761376788]  # IB1D
        for x in got_roles:
            for y in groups:
                if x.id == y:
                    return False
        return True

    async def add_study(self, new_role):
        got_roles = self.message.guild.roles
        role = discord.utils.get(got_roles, name="Studierende")
        await self.message.author.add_roles(role)
        if self.no_study(self.message.author.roles):
            role = discord.utils.get(self.message.guild.roles, name=new_role)
            await self.message.author.add_roles(role)
            return
        await self.message.channel.send(f"Anscheinend bist du nicht berechtigt diese "
                                        f"Rolle zu erhalten.\n<@!{self.message.author.id}>")

    async def add_group(self, new_role):
        got_roles = self.message.author.roles
        if not self.no_study(got_roles):
            if self.no_group(got_roles):
                role = discord.utils.get(self.message.guild.roles, name=new_role)
                await self.message.author.add_roles(role)
                return
        await self.message.channel.send(f"Anscheinend bist du nicht berechtigt diese "
                                        f"Rolle zu erhalten.\n<@!{self.message.author.id}>")
