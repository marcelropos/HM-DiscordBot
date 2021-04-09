# Discord Conf
import os


class Directories:
    ROOT_DIR = os.getcwd()
    DATA_DIR = os.path.join(ROOT_DIR, 'data')


class EmojiIds:
    Success = 769239335668809779
    Failed = 769239337887596624
    name_set = set()


class DefaultMessages:
    GREETINGS = "System online, waiting for your demands."
    ACTIVITY = "!help"


# noinspection PyPep8Naming
def DISCORD_BOT_TOKEN():
    token = os.environ["TOKEN"]
    return token


# noinspection PyPep8Naming
def COMMAND_PREFIX():
    prefix = os.environ["COMMAND_PREFIX"]
    return prefix


# noinspection PyPep8Naming
def DEBUG_STATUS():
    DEBUG = str(os.environ["DEBUG"])
    if DEBUG == "1" or DEBUG == "true":
        return True
    else:
        return False


class Links:
    EVENTS = "https://www.cs.hm.edu/aktuelles/termine/index.de.html"


class ServerIds:
    DEBUG_CHAT = 762736695116169217
    GUILD_ID = 760453010752143372
    BOT_COMMANDS_CHANNEL = 766024399093497876
    CUSTOM_CHANNELS = 763071118042333226
    NERD_ECKE = 760453011188875303
    AFK_CHANNEL = 760772235538595840
    MODERATOR = 762607212472041492
    INFORMATIK = 762562978523906070
    WIRTSCHAFTSINFORMATIK = 762563012614684713
    DATA_SCIENCE = 762565228826329138
    HM = 766071066468548650
    NOHM = 772091430989987920
    NSFW = 766020273664294953
    CODEING = 769870767759818772
    HELP = 765141613881720862
    NEWS = 781453512793128990


class Messages:
    ROLE_NOT_FOUND = \
        """Group not found:
        The following groups are currently available for selection:
        `{}`
        If you need a different role, contact the moderators."""
    ROLE_NOT_ASSIGNED_ON_SERVER = "The Role: {} was set as an assignable Role but not on the Server"
    WRONG_CHAT = f"This command can be put only in the chat <#{ServerIds.BOT_COMMANDS_CHANNEL}>."
    INCORRECT_CONFIGURATION = "An error has occurred in the bot or server configuration, which prevents the command " \
                              "from being executed at the moment."
    Expected_BUT_GOT = "Expected {} but got {}"


class ServerRoles:
    ALL_GROUPS = {
        "IF2A",
        "IF2B",
        "IF1A",
        "IB2B",
        "IB2C",
        "DC2"
    }
