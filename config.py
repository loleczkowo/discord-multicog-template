from pathlib import Path
from discord import CustomActivity
from core.data_types import LogType, dtEvent
from core.ids_objects import IDsObjects
from core.events import Events
# flake8: noqa

# -- MAIN CONFIG --
BOT_VERSION = "1.0.0"
DIR = Path(__file__).parent.resolve()
COMMAND_PREFIX = ":D!"
BOT_ACTIVITY = CustomActivity(name=f"Hello World! (V{BOT_VERSION})")

# -- IDS CONFIG --

class IDs:
    GUILD:int = 1078011599924768799

    class ROLES:
        ADMIN:int = 1388671984182890587

    class CHANNELS:
        # the channel where bot logs the console - better to not change name
        CONSOLE_LOGS:int = 1382306883204939887

    class USERS:
        # bot ofwner - better to not change name
        OWNER:int = 791000802260811797


ids_objects = IDsObjects(target=IDs)

# -- EVENTS --
events = Events()
EV_STARTUP = dtEvent("startup")
EV_RECCONECT = dtEvent("startup")



# -- LOGS CONFIG --
LOG_DIR = DIR/"logs"
LOG_RETENTION_DAYS = 3
LOG_TO_CONSOLE = True
LOG_TIME_FORMAT = "%H:%M:%S"
DISCORD_CHAR_LIMIT = 2000


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
