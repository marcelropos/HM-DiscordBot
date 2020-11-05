import json
import os
import discord
from settings import Directories
from utils import UserError


class HelpError(UserError):
    pass


class Embedgenerator:

    def __init__(self, file):
        os.chdir(Directories.DATA_DIR)
        self.file = rf'{os.getcwd()}/{file}.json'

        if not os.path.isfile(self.file):
            raise HelpError("Befehl nicht gefunden.\n"
                            "!help für mehr Informationen")

    def read(self):

        # noinspection PyBroadException
        try:
            with open(self.file, "r", encoding="utf-8")as f:
                payload = json.loads(f.read())
        except Exception as e:
            print(e)
            payload = None
        finally:
            os.chdir(Directories.ROOT_DIR)
            # noinspection PyUnboundLocalVariable
            return payload

    def generate(self):

        # noinspection PyShadowingNames
        jroot = self.read()

        if jroot:
            embed = discord.Embed(title=jroot["embeds"][0]["title"],
                                  colour=discord.Colour(0x12d4ca),
                                  description=jroot["embeds"][0]["description"])

            for x in jroot["embeds"][0]["fields"]:
                try:
                    inline = x["inline"]
                except KeyError:
                    inline = False
                embed.add_field(name=x["name"],
                                value=x["value"],
                                inline=inline)
            return embed

        else:
            embed = discord.Embed(title="Error",
                                  colour=discord.Colour(0x12d4ca),
                                  description="Diese Hilfe scheint es noch nicht zu geben.")
            return embed
