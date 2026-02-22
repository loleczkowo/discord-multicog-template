from traceback import format_exception
from typing import List


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
