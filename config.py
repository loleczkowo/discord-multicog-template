from pathlib import Path
from discord import CustomActivity
from core.data_types import LogType, dtEvent, Category
from core.ids_objects import IDsObjects
from core.events import Events
from core.command_category import Categories

# -- MAIN CONFIG --
TEMPLATE_VERSION = "2.5.2"
BOT_VERSION = "1.0.0"
BOT_GITHUB_LINK = None  # if your bot has a public github put it here so people can find it!
DIR = Path(__file__).parent.resolve()
COMMAND_PREFIX = ":D!"
BOT_ACTIVITY = CustomActivity(name=f"Hello World! (V{BOT_VERSION})")

DISCORD_CHAR_LIMIT = 2000
DISCORD_EMBED_LIMIT = 10


# -- IDS CONFIG --
class IDs:
    GUILD: int = 1078011599924768799

    class ROLES:
        ADMIN: int = 1388671984182890587

    class CHANNELS:
        # the channel where bot logs the console - better to not change name
        CONSOLE_LOGS: int = 1382306883204939887

    class USERS:
        # bot ofwner - better to not change name
        OWNER: int = 791000802260811797


ids_objects = IDsObjects(target=IDs)

# -- EVENTS --
events = Events()
EV_STARTUP = dtEvent("startup")
EV_DISCONECT = dtEvent("disconect")
EV_RECCONECT = dtEvent("startup")
EV_SHUTDOWN = dtEvent("shutdown")


# -- Categories --
CT_MEMBER = Category("Member", sort_priority=0)  # first
CT_ADMIN = Category("Admin", sort_priority=-2)  # almsot last
CT_BOT_OWNER = Category("Bot Owner", sort_priority=-1)  # last
categories = Categories(default_category=CT_MEMBER)


# -- LOGS CONFIG --
LOG_DIR = DIR/"logs"
LOG_RETENTION_DAYS = 3
LOG_TO_CONSOLE = True
LOG_TIME_FORMAT = "%H:%M:%S"


# ignore_closed_console does NOT ignore LOG_TO_CONSOLE=false
QINFO:      type[LogType] = LogType("Qinfo",    to_console=False)  # quiet-log.
INFO:       type[LogType] = LogType("INFO")
SUCCESS:    type[LogType] = LogType("SUCCESS")
USER_INPUT: type[LogType] = LogType("USERINP")
RESPONSE:   type[LogType] = LogType("RESPONSE")  # aka console commmand response
WARNING:    type[LogType] = LogType("WARNING",  ignore_closed_console=True)
ERROR:      type[LogType] = LogType("ERROR",    to_discord=True, ignore_closed_console=True, ping=True)
CRITICAL:   type[LogType] = LogType("CRITICAL", to_discord=True, ignore_closed_console=True, ping=True)
ALL_LOG_TYPES = [INFO, SUCCESS, USER_INPUT, RESPONSE, WARNING, ERROR, CRITICAL]
DEFALUT_PING = IDs.ROLES.ADMIN


# -- MEMORY --
MEMORY_DIR = DIR/"memory"
MEMORY_MAIN_FILE = MEMORY_DIR/"memory.json"
MEMORY_AUTOSAVE_TIME = 5*60
