import datetime
import asyncio
from time import gmtime, strftime
from typing import List
from discord import Role
from globals import Globals as G
from config import (
    LOG_DIR, LOG_RETENTION_DAYS, LOG_TO_CONSOLE, LOG_TIME_FORMAT,
    DEFALUT_PING, ALL_LOG_TYPES, DISCORD_CHAR_LIMIT,
    ERROR, QINFO, ids_objects, events, EV_STARTUP)
from core.data_types import LogType


_TYPE_WIDTH = max(len(t.name) for t in ALL_LOG_TYPES)
_WHITESPACE = " "*(_TYPE_WIDTH+len(strftime(LOG_TIME_FORMAT, gmtime()))+1)
send_to_discord_list: List[str] = []

LOG_DIR.mkdir(parents=True, exist_ok=True)


def _plain_log(log_text: str, log_type: LogType):
    if log_type.to_console and LOG_TO_CONSOLE and (
         log_type.ignore_closed_console or not G.closed_console):
        print(log_text)

    if not log_type.to_file:
        return

    today = datetime.date.today().isoformat()
    log_file = LOG_DIR / f"{today}.log"
    with log_file.open("a", encoding="utf-8") as f:
        f.write(log_text + "\n")
    cutoff = datetime.datetime.now()-datetime.timedelta(days=LOG_RETENTION_DAYS)
    for path in LOG_DIR.glob("*.log"):
        try:
            date_str = path.stem
            file_date = datetime.datetime.fromisoformat(date_str)
        except Exception:
            continue
        if file_date < cutoff:
            path.unlink()


def get_logs(lines: int):
    today = datetime.date.today().isoformat()
    log_file = LOG_DIR / f"{today}.log"
    with open(log_file, "r", encoding="utf-8") as f:
        lines = f.readlines()
    return lines[-int(lines):]


def log(log_type: LogType, message: str, *args, join=""):
    message = message+join+join.join([str(a) for a in args])
    if log_type.to_discord:
        discord_log(log_type, message)
    lines = message.split("\n")
    head = f"{strftime(LOG_TIME_FORMAT, gmtime())} {log_type.name.ljust(_TYPE_WIDTH)}"
    header = f"{head} || {lines[0]}"

    if len(lines) > 1:
        if log_type.newline_formatting:
            ind = _WHITESPACE+"  | "
            body = "\n".join(f"{ind}{lins}" for lins in lines[1:])
        else:
            body = "\n".join(lines[1:])
        _plain_log(f"{header}\n{body}", log_type)
    else:
        _plain_log(header, log_type)


# -- DISCORD LOG HELL --

def _plain_discord_log(log_text: str):
    global send_to_discord_list
    send_to_discord_list.append(log_text)


def discord_log(log_type: LogType, log_text: str, *args, join=""):
    log_text = log_text+join+join.join([str(a) for a in args])
    global send_to_discord_list
    ping = log_type.ping
    if ping is True:
        ping = DEFALUT_PING
    if isinstance(ping, Role):
        ping = ping.id
    if ping is not False:
        s_message = f"-# *`[{log_type.name}]`* <@&{ping}>"
    else:
        s_message = f"-# *`[{log_type.name}]`*"
    f_message = f"{s_message}\n{log_text}"
    _plain_discord_log(f_message)


@events.on_event(EV_STARTUP, close_on_shutdown=True)
async def discord_log_loop():
    await G.bot.wait_until_ready()
    log(QINFO(to_discord=False), "Discord log loop has started.")
    try:
        while True:
            await send_discord_logs()
            await asyncio.sleep(0.5)
    except asyncio.CancelledError:
        log(QINFO(to_discord=False), "Discord log loop has stopped.")


async def send_discord_logs():
    global send_to_discord_list
    if not send_to_discord_list:
        return
    if G.connected is False or not ids_objects.is_build:
        return
    current_len = 0
    number_to_send = 0
    for checkmessage in send_to_discord_list:
        current_len += len(checkmessage)+1
        if current_len > DISCORD_CHAR_LIMIT:
            break
        number_to_send += 1
    if number_to_send == 0:
        try:
            if "\n" in send_to_discord_list[0]:
                splits = send_to_discord_list[0].split("\n")
                if len(splits[0]) < DISCORD_CHAR_LIMIT-3:
                    while len(splits) > 1 and len(
                         splits[0]+splits[1]) < DISCORD_CHAR_LIMIT-4:
                        splits[0] += "\n"+splits.pop(1)
                    if splits[0].count("```") & 1:
                        to_discord = [splits[0]+"```"]
                        send_to_discord_list[0] = "```"+"\n".join(splits[1:])
                    else:
                        to_discord = [splits[0]]
                        send_to_discord_list[0] = "\n".join(splits[1:])
                else:
                    to_discord = [splits[0][:DISCORD_CHAR_LIMIT]]
                    send_to_discord_list[0] = \
                        splits[0][DISCORD_CHAR_LIMIT:]+"\n"+"\n".join(splits[1:])
            else:
                to_discord = [send_to_discord_list[0][:DISCORD_CHAR_LIMIT]]
                send_to_discord_list[0] = send_to_discord_list[0][DISCORD_CHAR_LIMIT:]
        except Exception as e:
            try:
                log(ERROR(to_discord=False), f"send_discord_logs error: {e}")
                send_to_discord_list.pop(0)
            except Exception:
                pass
            return
    else:
        to_discord = []
        for _ in range(number_to_send):
            try:
                to_discord.append(send_to_discord_list.pop(0))
            except Exception:
                continue
    try:
        await ids_objects.CHANNELS.CONSOLE_LOGS.send("\n".join(to_discord))
    except Exception as e:
        log(ERROR(to_discord=False), f"send_discord_logs error: {e}")
