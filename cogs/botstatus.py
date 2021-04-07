from enum import Enum
from threading import Lock

import discord
from discord.ext.commands import Context, Bot

from settings_files._global import DefaultMessages
from settings_files.all_errors import *
from utils.logbot import LogBot


class Modes(Enum):
    AUTO = "auto"
    Manual = "manual"


class Activity(Enum):
    LISTEN = "listen"
    WATCH = "watch"
    PLAYING = "play"
    AUTO = "auto"


def activity_converter(activity: str) -> Activity:
    activity = activity.lower()
    try:
        return Activity(activity)
    except Exception:
        raise BadArgument("Activity not found")


class Status(Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    IDLE = "idle"
    DND = "dnd"
    AUTO = "auto"


def status_converter(status: str) -> Status:
    status = status.lower()
    try:
        return Status(status)
    except Exception:
        raise BadArgument("Status not found")


class BotStatusValues:
    """Saves the current status and type_of_activity and their modes and prevents simultaneous access to the
    attributes. """

    _lock = Lock()
    _activity = discord.Activity(type=discord.ActivityType.listening,
                                 name=DefaultMessages.ACTIVITY)
    _activity_mode = Modes.AUTO
    _status = discord.Status.online
    _status_mode = Modes.AUTO

    @classmethod
    def get_activity(cls):
        with cls._lock:
            return cls._activity

    @classmethod
    def set_activity(cls, arg):
        with cls._lock:
            cls._activity = arg

    @classmethod
    def get_activity_mode(cls):
        with cls._lock:
            return cls._activity_mode

    @classmethod
    def set_activity_mode(cls, arg):
        with cls._lock:
            cls._activity_mode = arg

    @classmethod
    def get_status(cls):
        with cls._lock:
            return cls._status

    @classmethod
    def set_status(cls, arg):
        with cls._lock:
            cls._status = arg

    @classmethod
    def get_status_mode(cls):
        with cls._lock:
            return cls._status_mode

    @classmethod
    def set_status_mode(cls, arg):
        with cls._lock:
            cls._status_mode = arg


class BotStatus(commands.Cog):
    """Manage status and type_of_activity"""

    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.command(brief="Set type_of_activity",
                      help="""modes:
                         - listen (default)
                         - watch
                         - play""")
    @commands.is_owner()
    async def activity(self, _, type_of_activity: activity_converter, *, activity_argument: str = None):

        if Activity.AUTO == type_of_activity:
            BotStatusValues.set_activity_mode(Modes.AUTO)
        else:
            if not activity_argument:
                raise MissingRequiredArgument("activity_argument is missing")
            BotStatusValues.set_activity_mode(Modes.Manual)

        if Activity.LISTEN == type_of_activity:

            # Setting `Listening ` status
            BotStatusValues.set_activity(discord.Activity(type=discord.ActivityType.listening,
                                                          name=DefaultMessages.ACTIVITY))
        elif Activity.WATCH == type_of_activity:
            # Setting `Watching ` status
            BotStatusValues.set_activity(discord.Activity(type=discord.ActivityType.watching,
                                                          name=activity_argument))
        elif Activity.PLAYING == type_of_activity:
            # Setting `Playing ` status
            BotStatusValues.set_activity(discord.Game(name=activity_argument))

        elif Activity.AUTO == type_of_activity:
            BotStatusValues.set_activity(discord.Activity(type=discord.ActivityType.listening,
                                                          name=activity_argument))
        else:
            raise NotImplementedError(f"Activity {type_of_activity.name} not implemented")

        await self.bot.change_presence(status=self.status,
                                       activity=BotStatusValues.get_activity())

    @commands.command(brief="Change online status",
                      help="""Status:
                         - online
                         - offline
                         - idle
                         - dnd""")
    @commands.is_owner()
    async def status(self, _, *, status: status_converter):

        if Activity.AUTO == status:
            BotStatusValues.set_status_mode(Modes.AUTO)
        else:
            BotStatusValues.set_status_mode(Modes.Manual)

        if Status.ONLINE == status:
            BotStatusValues.set_status(discord.Status.online)
        elif Status.ONLINE == status:
            BotStatusValues.set_status(discord.Status.offline)
        elif Status.IDLE == status:
            BotStatusValues.set_status(discord.Status.idle)
        elif Status.DND == status:
            BotStatusValues.set_status(discord.Status.dnd)
        elif Status.AUTO == status:
            BotStatusValues.set_status(discord.Status.online)
        else:
            raise NotImplementedError(f"Status {status.name} not implemented")

        print(repr(BotStatusValues.get_status()))
        await discord.Client.change_presence(self=self.bot,
                                             status=BotStatusValues.get_status())

        LogBot.logger.debug(f"Status: {BotStatusValues.get_status()} Mode: {BotStatusValues.get_status_mode()}")

    @status.error
    @activity.error
    async def errors(self, ctx: Context, error):
        LogBot.logger.exception("")


def setup(bot: Bot):
    BotStatusValues()
    bot.add_cog(BotStatus(bot))
