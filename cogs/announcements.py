# noinspection PyUnresolvedReferences
import datetime
import re
from collections import namedtuple
import discord
import requests
from bs4 import BeautifulSoup
from discord.ext import commands, tasks
from utils import ReadWrite
from settings import Links

# noinspection PyUnresolvedReferences
from utils import ServerIds, ModuleError


class RequestError(ModuleError):
    pass


class Announcements(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.events = []
        #  self.event_scedule.start()

    def __event_sort(self):
        def getkey(item):
            return item.end

        self.events = sorted(self.events, key=getkey)

    def __fetch_event(self, dates, title, message):
        eventobj = namedtuple("Event", ["begin", "end", "title", "message"])
        liste = []
        for x in dates:
            date_string = title[x.start(): x.end()]
            day, month, year = re.split(r"\.", date_string)
            liste.append(datetime.datetime(day=int(day), month=int(month), year=int(year)))
        if datetime.datetime.today() <= max(liste):
            if datetime.datetime.today() >= min(liste):
                title = "⚠" + title + "⚠"
            self.events.append(eventobj(begin=min(liste), end=max(liste), title=title, message=message))

    def __events(self):
        link = Links.EVENTS
        r = requests.get(link, timeout=5)
        if not r.ok:
            raise RequestError()

        soup = BeautifulSoup(r.content, features="html.parser")
        embed = discord.Embed(title="Veranstaltungen")
        embed.set_footer(text=f"Quelle: {link}\n und eigene Erg\u00e4nzungen."
                              f"Stand: {datetime.datetime.now().strftime('%d.%m.%Y %H:%M Uhr')}\n"
                              f"Alle Angaben ohne gewähr.")

        for table in soup.find_all("table"):
            for data in table.find_all("tr"):
                column = data.find_all("td")
                try:
                    dates = re.finditer(r"[0-9]{2}\.[0-9]{2}\.[0-9]{4}", column[0].text)
                    self.__fetch_event(dates, column[0].text, column[1].text)
                except IndexError:
                    pass
                except ValueError:
                    pass
                except TypeError:
                    pass

        payload = ReadWrite.read("events")
        for event in payload["events"]:
            dates = re.finditer(r"[0-9]{2}\.[0-9]{2}\.[0-9]{4}", event["date"])
            self.__fetch_event(dates, event["date"], event["message"])

        self.__event_sort()

        for event in self.events:
            embed.add_field(name=event.title, value=event.message, inline=False)

        return embed

    @commands.command()
    @commands.has_role(ServerIds.HM)
    async def events(self, ctx):
        await ctx.send(embed=self.__events())

    @tasks.loop(minutes=10)
    async def event_scedule(self):
        channel = discord.Client.get_channel(self=self.bot,
                                             id=ServerIds.DEBUG_CHAT)
        if channel:
            await channel.send(embed=self.__events())

    @events.error
    async def events_errorhandler(self, ctx, error):
        if isinstance(error, RequestError):
            await ctx.send()

        else:
            raise error


def setup(bot):
    bot.add_cog(Announcements(bot))
