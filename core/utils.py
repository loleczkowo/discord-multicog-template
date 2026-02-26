from traceback import format_exception
from typing import List, get_args, Union
from discord import Emoji, Member, User, Role, TextChannel, VoiceChannel


def traceback_lines(error) -> List[str]:
    tblines = format_exception(error)
    return [ln for line in tblines for ln in line.rstrip().split("\n")]


def format_traceback(error) -> List[str]:
    lines = traceback_lines(error)
    formatted_lines: List[str] = [lines[0]]
    for line in lines[1:]:
        stripped = line.strip()
        if stripped.startswith("File"):
            parts = stripped.split(", ")
            tmp = parts[0].split(" ")
            tmp[0] = "File"
            parts[0] = " ".join(tmp)
            parts[2] = f"in {parts[2].split()[1]}"
            formatted_lines.append(", ".join(parts))
        elif stripped and all(c in "^~" for c in stripped):
            formatted_lines.append(line)
        elif ":" in line and line[0] != " " and len(line.split(":")) > 1:
            formatted_lines.append(line)
        else:
            formatted_lines.append(line)
    for i in range(1, len(formatted_lines)):
        formatted_lines[i] = f">{formatted_lines[i]}"
    return formatted_lines


def format_time(seconds: float):
    minutes = seconds//60
    seconds = int(seconds-minutes*60)
    hours = int(minutes//60)
    minutes = int(minutes-hours*60)
    text = ""
    if hours > 0:
        text += str(hours)+" hour"+"s"*(hours > 1)+" "
    if minutes > 0:
        text += str(minutes)+" minute"+"s"*(minutes > 1)+" "
    if text != "":
        text += "and "
    text += str(seconds)+" second"+"s"*(not seconds == 1)
    return text


def human_type(tp) -> str:
    if hasattr(tp, "__origin__"):
        if tp.__origin__ is Union:
            return " Or ".join([human_type(typ) for typ in get_args(tp)])
    if tp is int:
        return "Number"
    if tp is str:
        return "Text"
    if tp is Emoji:
        return "Emoji"
    if tp in (User, Member):
        return "User"
    if tp is Role:
        return "Role"
    if tp is TextChannel:
        return "Text Channel"
    if tp is VoiceChannel:
        return "Voice Channel"
    return "Unknown"
