from dataclasses import dataclass, replace
from discord import Role


@dataclass(frozen=True)
class LogType:
    name: str
    # general config
    ping: Role | int | bool = False
    to_discord: bool = False
    to_file: bool = True
    to_console: bool = True
    ignore_closed_console: bool = False
    # specjal inputs
    newline_formatting: bool = True

    def __call__(self, **changes):
        return replace(self, **changes)


@dataclass
class dtEvent:
    name: str


@dataclass
class Category:
    name: str
    sort_priority: int = None
