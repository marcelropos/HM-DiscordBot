# Discord Conf
import os


class Directories:
    ROOT_DIR = os.getcwd()
    DATA_DIR = os.path.join(ROOT_DIR, 'data')


class EmojiIds:
    Success = 769239335668809779
    Failed = 769239337887596624


class DefaultMessages:
    GREETINGS = "System online, waiting for your demands."
    ACTIVITY = "!help"


# noinspection PyPep8Naming
def DISCORD_BOT_TOKEN():
    token = os.environ["TOKEN"]
    return token


# noinspection PyPep8Naming
def DEBUG_STATUS():
    DEBUG = int(os.environ["DEBUG"])
    if DEBUG == "1" or DEBUG == "true":
        return True
    else:
        return False


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
    IF1A = 763714090454745098
    IF1B = 763714190195294269
    IB1A = 763714403009953823
    IB1B = 763714479916711957
    IB1C = 763714528424361995
    NSFW = 766020273664294953
    CODEING = 769870767759818772


class ServerRoles:
    MODERATOR_ROLE_NAME = "Mod"
    INFORMATIK = "IF"
    WIRTSCHAFTSINFORMATIK = "IB"
    DATA_SCIENCE = "DC"
    HM = "HM"
    NOHM = "NO-HM"
    IF1A = "IF1A"
    IF1B = "IF1B"
    IB1A = "IB1A"
    IB1B = "IB1B"
    IB1C = "IB1C"
    IB1D = "IB1D"
    NSFW = "NSFW"
    CODEING = "coding"

    ALL_COURSES = {
        "IF",
        "IB"
        "DC"
    }

    ALL_GROUPS = {
        "IF1A",
        "IF1B",
        "IB1A",
        "IB1B",
        "IB1C",
        "IB1D"
    }
