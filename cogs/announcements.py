# noinspection PyUnresolvedReferences
import datetime
import re
from collections import namedtuple

import discord
import requests
from bs4 import BeautifulSoup

from settings_files._global import Links
from settings_files.all_errors import *
from utils.ReadWrite import ReadWrite
from utils.utils import MissingRole
# noinspection PyUnresolvedReferences
from utils.utils import ServerIds


class Announcements(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        #  self.event_scedule.start()

    @staticmethod
    def __event_sort(events):
        def get_key(item):
            return item.end
        return sorted(events, key=get_key)

    @staticmethod
    def __fetch_event(dates, title, message):
        event_obj = namedtuple("Event", ["begin", "end", "title", "message"])
        liste = []
        for x in dates:
            date_string = title[x.start(): x.end()]
            day, month, year = re.split(r"\.", date_string)
            liste.append(datetime.datetime(day=int(day), month=int(month), year=int(year)))
        if datetime.datetime.today().date() <= max(liste).date():
            if datetime.datetime.today().date() >= min(liste).date():
                title = "⚠" + title + "⚠"
            return event_obj(begin=min(liste), end=max(liste), title=title, message=message)

    def __events(self, ctx):
        events_list = []
        link = Links.EVENTS
        r = requests.get(link, timeout=5)
        if not r.ok:
            raise RequestError()

        soup = BeautifulSoup(r.content, features="html.parser")
        embed = discord.Embed(title="Events")
        embed.set_footer(text=f"Source: (Unless otherwise indicated) {link}\n"
                              f"Stand: {datetime.datetime.now().strftime('%d.%m.%Y %H:%M Uhr')}\n"
                              f"All data without warranty.")

        for table in soup.find_all("table"):
            for data in table.find_all("tr"):
                column = data.find_all("td")
                try:
                    dates = re.finditer(r"[0-9]{2}\.[0-9]{2}\.[0-9]{4}", column[0].text)
                    ret = self.__fetch_event(dates, column[0].text, column[1].text)
                    if ret:
                        events_list.append(ret)
                except IndexError:
                    pass
                except ValueError:
                    pass
                except TypeError:
                    pass

        roles = set()
        for x in ctx.author.roles:
            roles.add(x.name)

        root = ReadWrite.read("events")

        for role in roles.intersection(ReadWrite.read("events")):
            for event in root[role]["events"]:
                dates = re.finditer(r"[0-9]{2}\.[0-9]{2}\.[0-9]{4}", event["date"])
                ret = self.__fetch_event(dates, event["date"], event["message"])
                if ret:
                    events_list.append(ret)

        for event in self.__event_sort(events_list):
            embed.add_field(name=event.title, value=event.message, inline=False)

        return embed

    @commands.command()
    @commands.has_role(ServerIds.HM)
    async def events(self, ctx):
        await ctx.author.send(embed=self.__events(ctx))

    @events.error
    async def events_errorhandler(self, ctx, error: CommandInvokeError):
        error = error.original
        if isinstance(error, RequestError):
            await ctx.send()

        elif isinstance(error, MissingRole):
            await ctx.send(f"<@!{ctx.author.id}>\n"
                           f"Verification is required for this command.\n"
                           f"Make a request for this in <#{ServerIds.HELP}>.")
        else:
            raise error


def setup(bot):
    bot.add_cog(Announcements(bot))
