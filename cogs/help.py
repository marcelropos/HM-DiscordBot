# noinspection PyUnresolvedReferences
from discord.ext import commands
from utils import *


class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(aliases=["hilfe"])
    async def help(self, ctx):
        if ctx.invoked_subcommand is None:
            embed = discord.Embed(title="Hilfsübersicht", colour=discord.Colour(0x12d4ca),
                                  description="Hier findest du eine Liste aller verfügbaren Befehle.")

            embed.set_author(name="Marcel (Anthony)")
            embed.set_footer(text="Erstellt am 10.10.2020 20:00 Uhr")
            embed.add_field(name="Regeln:", value="Auch auf diesem Server gibt es Regeln, diese findest du, "
                                                  "indem du mir ```!rules``` schreibst.")
            embed.add_field(name="Rollen:",
                            value="Mit Rollen kann jeder auf dem Server sehen, zu welchem Studiengang oder zu "
                                  "welcher Gruppe du angehörst.\n\nGleichzeitig erhält du Zugang zu den Chats, "
                                  "die nur diesem Studiengang bzw. dieser Gruppe angehören. Mit ```!help roles``` "
                                  "erhältst du weitere Informationen zu diesem Befehl.")
            embed.add_field(name="Datenschutz:",
                            value="Wenn du wissen willst welche Daten ich so verabeite. Dann frage mich doch mit "
                                  "```!my-data``` und ich werde es dir gerne erzählen.")

            embed.add_field(name="Temporäre Channel:",
                            value="Du kannst auf diesem Server natürlich auch temporäre Channel erstellen."
                                  "Mehr Infos erhälst du mit ```!help tmpc```")

            await ctx.send(
                content=f"<@!{ctx.author.id}> vielen Dank für deine Frage.\n Tipp: alle "
                        f"'help' Befehle, kannst du auch via PN"
                        f" an mich richten.", embed=embed)

    @commands.command(aliases=["my-data"])
    async def my_data(self, ctx):
        embed = discord.Embed(title="Datenschutz", colour=discord.Colour(0x12d4ca),
                              description="Datenschutz ich wichtig, darum will ich dir auch gerne sagen, "
                                          "was ich verarbeite und was ich wie lange speichere. Natürlich kann "
                                          "sich dies von Zeit zu Zeit mal ändern, also frag mich gerne "
                                          "regelmäßig mal nach dem neuesten Stand.")

        embed.set_author(name="Marcel (Anthony)")
        embed.set_footer(text="Bearbeitet am 03.11.2020 18:00 Uhr")

        embed.add_field(name="passives Verarbeiten:",
                        value="Für jedes 'Event' auf diesem Server wird der Bot benachrichtigt. Dabei bekomme ich "
                              "alle Informationen über dieses Event. Wenn du beispielsweise eine Nachricht "
                              "schreibst, oder einem Sprachkanal beitrittst, dann erlange ich davon Kenntnis. "
                              "Dies bedeutet aber nicht, dass ich diese Information benutze.\n"
                              "Diese Informationen können auch in Cache gespeichert werden.")
        embed.add_field(name="aktives Verarbeiten:",
                        value="Mit <:dynoSuccess:769239335668809779>,<:DynoFail:769239337887596624> oder "
                              "<:read:762601788200321025> siehst du ob der Bot"
                              "deine Nachricht in irgendwie verarbeitet hat.")
        embed.add_field(name="Speichern:",
                        value="Wenn du einen temporären Channel erstellst, wird dieser an deinen Account gebunden.  "
                              "Diese Information wird gespeichert, damit ein missbräuchliches Erstellen von Räumen "
                              "unterbunden wird.")
        await ctx.send(content=f"<@!{ctx.author.id}> vielen Dank für deine Frage.",
                       embed=embed)

    @commands.command()
    async def rules(self, ctx):
        embed = discord.Embed(title="Regeln", colour=discord.Colour(0xffff),
                              description="Jede Gesellschaft hat und braucht Regeln. Im Allgemeinen ist der "
                                          "gesunde Menschenverstand ausreichend. Behandle jeden so, "
                                          "wie du auch von ihnen behandelt werden willst. Wenn du dies tust, "
                                          "dann musst du auch nicht mehr weiterlesen.")

        embed.set_author(name="Marcel (Anthony)")
        embed.set_footer(text="Erstellt am 07.10.2020 22:00 Uhr")

        embed.add_field(name="Meinungsfreiheit",
                        value="Dieser Server soll ein Ort der Bildung und der freien Meinung sein.\nAlle "
                              "sollen die Möglichkeit haben, sich frei zu äußern und ihre Ansichten kund zu "
                              "tun.\nNatürlich bedeutet dies nicht, dass extremistische und/oder "
                              "menschenverachtende Meinungen oder Inhalte hier geteilt werden können bzw. "
                              "dürfen.", inline=False)
        embed.add_field(name="Streit / Meinungsverschiedenheit",
                        value="Konstruktive Streitgespräche können auch ohne Beleidigung und mit "
                              "gegenseitigen Respekt geführt werden.\nBeleidigungen und Diskriminierung "
                              "sollen und müssen nicht geduldet werden. Willst du deine Abneigung ausdrücken, "
                              "ist eine 'Ich Botschaft' oft eine gute Lösung.", inline=False)
        embed.add_field(name="Etikette im Chat",
                        value="Die Themenbezogenen Chats sind dem jeweiligen Thema gewidmet.\nThemenfremde "
                              "Inhalte sind bitte zu vermeiden und können in die dafür vorgesehenen Chats "
                              "oder in den allgemeinen Chats geführt werden.\nIst der Bedarf für dieses "
                              "Spezielle Thema groß, so werde ich gerne eines dafür anlegen.", inline=False)
        embed.add_field(name="Moderatoren",
                        value="Moderatoren sind für die Einhaltung der Regeln hier, sowie die Etikette, "
                              "die der jeweilige Studiengang sich zusätzlich selbst auferlegen kann, "
                              "verantwortlich.\nSie sind u.a. in der Lage:\n- den Nick zu ändern, "
                              "falls dieser unangemessen ist.\n- Nachrichten zu löschen, wenn diese die freie "
                              "Meinung überschreiten.\n- euch Stumm/Taub zu schalten, falls ihr im "
                              "Sprachchannel unangemessen verhaltet.", inline=False)
        embed.add_field(name="Ban",
                        value="Ich denke, dies sollte keine Option sein müssen. Diese Maßnahmen will ich erst "
                              "im Einsetzen, wenn es keine andere Möglichkeit mehr gibt.", inline=False)
        await ctx.channel.send(content=f"<@!{ctx.author.id}> vielen Dank für deine Frage.",
                               embed=embed)

    @help.command(aliases=["study", "group", "role"])
    async def roles(self, ctx):
        embed = discord.Embed(title="Rollen", colour=discord.Colour(0x12d4ca),
                              description="Mit Rollen kann jeder auf dem Server sehen, zu welchem Studiengang oder zu "
                                          "welcher Gruppe du angehörst.\n\nGleichzeitig erhält du Zugang zu den "
                                          "Chats, die nur diesem Studiengang bzw. dieser Gruppe angehören.")

        embed.set_author(name="Marcel (Anthony)")
        embed.set_footer(text="Erstellt am 10.10.2020 20:00 Uhr")

        embed.add_field(name="Informatik:",
                        value="```!study IF``` Exclusiv für diesen Studiengang stehen noch folgende Befehle zur "
                              "Verfügung. ```!group IF1A``` ```!group IF1B```", inline=True)
        embed.add_field(name="Wirtschaftsinformatik:",
                        value="```!study IB```Exclusiv für diesen Studiengang stehen noch folgende Befehle zur "
                              "Verfügung ```!group IB1A``` ```!group IB1B``` ```!group IB1C``` ```!group IB1D```",
                        inline=True)
        embed.add_field(name="data-Science:", value="```!study DC``` ", inline=True)
        embed.add_field(name="Falsche(r) Studiengang/Gruppe", value="```Deine Rolle kann nur"
                                                                    " vom Admin entfernt werden```")
        embed.add_field(name="NSFW", value="Mit `!nsfw-add` oder `#nsfw-rem` kannst du dir die Rolle für den Channel: "
                                           "<#766307455856410634> geben.", inline=False)

        embed.add_field(name="Bot Coder", value="Mit `!coding` kannst du teil des Botcoding Teams werden.",
                        inline=False)

        await ctx.send(content=f"<@!{ctx.author.id}> vielen Dank für deine Frage.", embed=embed)

    @help.command()
    async def tmpc(self, ctx):
        embed = discord.Embed(title="Temporäre Channel", colour=discord.Colour(0x12d4ca),
                              description="Hier ist eine kleine Anleitung wie du eigene temporäre Channel erstellt.")

        embed.set_author(name="Marcel (Anthony)")
        embed.set_footer(text="Erstellt am: 03.11.2020 17:45 Uhr")

        embed.add_field(name="Schritt 2", value="`!tmpc {Name des Channels}`", inline=False)
        embed.add_field(name="Schritt 3", value="Du wirst nun in diesen Channel gezogen.", inline=False)
        embed.add_field(name="Schritt 4",
                        value="Gib diesen Token an deine Kommilitonen, damit diese auch beitreten können."
                              "Diese können dem Bot privat schreiben, damit der Token nicht für alle sichtbar ist.",
                        inline=False)
        embed.add_field(name="Schritt 5",
                        value="Deine Kommilitonen, welche auch mit einem VC verbunden sein müssen benutzen den Token.",
                        inline=False)
        embed.add_field(name="Schritt 6", value="Alle verlassen den Channel, der Channel wird gelöscht", inline=False)

        await ctx.send(content=f"<@!{ctx.author.id}> vielen Dank für deine Frage.", embed=embed)


def setup(bot):
    bot.add_cog(Help(bot))
