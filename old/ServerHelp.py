import discord
#  import re


class ServerHelp:

    def __init__(self, message, msg):
        self.message = message
        self.msg = msg

    def start(self):
        pass

    async def help(self):
        embed = discord.Embed(title="Hilfsübersicht", colour=discord.Colour(0x12d4ca),
                              description="Hier findest du eine Liste aller verfügbaren Befehle.")

        embed.set_author(name="Marcel (Anthony)")
        embed.set_footer(text="Erstellt am 07.10.2020 18:00 Uhr")
        embed.add_field(name="Regeln:", value="Auch auf diesem Server gibt es Regeln, diese findest du, "
                                              "indem du mir ```!rules``` schreibst.")
        embed.add_field(name="Rollen:",
                        value="Mit Rollen kann jeder auf dem Server sehen, zu welchem Studiengang oder zu "
                              "welcher Gruppe du angehörst.\n\nGleichzeitig erhält du Zugang zu den Chats, "
                              "die nur diesem Studiengang bzw. dieser Gruppe angehören. Mit ```!add role "
                              "-help``` erhältst du weitere Informationen zu diesem Befehl.")
        embed.add_field(name="Datenschutz:",
                        value="Wenn du wissen willst welche Daten ich so verabeite. Dann frage mich doch mit "
                              "```!my-data``` und ich werde es dir gerne erzählen.")
        embed.add_field(name="Demnächst:",
                        value="Hier werden bald noch weitere tolle Funktionen erscheinen. Ich bitte "
                              "allerdings noch um Geduld.")

        await self.message.channel.send(
            content=f"<@!{self.message.author.id}> vielen Dank für deine Frage.\n Tipp: alle "
                    f"'help' Befehle, kannst du auch via PN"
                    f" an mich richten.", embed=embed)

    async def my_data(self):
        embed = discord.Embed(title="Datenschutz", colour=discord.Colour(0x12d4ca),
                              description="Datenschutz ich wichtig, darum will ich dir auch gerne sagen, "
                                          "was ich verarbeite und was ich wie lange speichere. Natürlich kann "
                                          "sich dies von Zeit zu Zeit mal ändern, also frag mich gerne "
                                          "regelmäßig mal nach dem neuesten Stand.")

        embed.set_author(name="Marcel (Anthony)")
        embed.set_footer(text="Erstellt am 07.10.2020 19:20 Uhr")

        embed.add_field(name="passives Verarbeiten:",
                        value="Für jedes 'Event' auf diesem Server werde benachrichtigt. Dabei bekomme ich "
                              "alle Informationen über dieses Event. Wenn du beispielsweise eine Nachricht "
                              "schreibst, oder einem Sprachkanal beitrittst, dann erlange ich davon Kenntnis. "
                              "Dies bedeutet aber nicht, dass ich diese Information benutze.")
        embed.add_field(name="aktives Verarbeiten:",
                        value="Diese Reaktion <:read:762601788200321025> siehst du doch sicher gerade bei "
                              "deiner Nachricht.\n ```!my-data``` oder? Damit kennzeichne ich Nachrichten, "
                              "die ich verarbeite.")
        embed.add_field(name="Speichern:",
                        value="Derzeit speichere ich keine Daten über dich oder andere hier.\nDennoch weise "
                              "ich wie bei beim passiven Verarbeiten darauf hin, dass einige dieser Events "
                              "möglicherweise im Cache gespeichert sind. Dieser wird nach einiger Zeit aber "
                              "wieder gelöscht.")
        await self.message.channel.send(content=f"<@!{self.message.author.id}> vielen Dank für deine Frage.",
                                        embed=embed)

    async def rules(self):
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
                              "dürfen.")
        embed.add_field(name="Streit / Meinungsverschiedenheit",
                        value="Konstruktive Streitgespräche können auch ohne Beleidigung und mit "
                              "gegenseitigen Respekt geführt werden.\nBeleidigungen und Diskriminierung "
                              "sollen und müssen nicht geduldet werden. Willst du deine Abneigung ausdrücken, "
                              "ist eine 'Ich Botschaft' oft eine gute Lösung.")
        embed.add_field(name="Etikette im Chat",
                        value="Die Themenbezogenen Chats sind dem jeweiligen Thema gewidmet.\nThemenfremde "
                              "Inhalte sind bitte zu vermeiden und können in die dafür vorgesehenen Chats "
                              "oder in den allgemeinen Chats geführt werden.\nIst der Bedarf für dieses "
                              "Spezielle Thema groß, so werde ich gerne eines dafür anlegen.")
        embed.add_field(name="Moderatoren",
                        value="Moderatoren sind für die Einhaltung der Regeln hier, sowie die Etikette, "
                              "die der jeweilige Studiengang sich zusätzlich selbst auferlegen kann, "
                              "verantwortlich.\nSie sind u.a. in der Lage:\n- den Nick zu ändern, "
                              "falls dieser unangemessen ist.\n- Nachrichten zu löschen, wenn diese die freie "
                              "Meinung überschreiten.\n- euch Stumm/Taub zu schalten, falls ihr im "
                              "Sprachchannel unangemessen verhaltet.")
        embed.add_field(name="Ban",
                        value="Ich denke, dies sollte keine Option sein müssen. Diese Maßnahmen will ich erst "
                              "im Einsetzen, wenn es keine andere Möglichkeit mehr gibt.")
        await self.message.channel.send(content=f"<@!{self.message.author.id}> vielen Dank für deine Frage.",
                                        embed=embed)
