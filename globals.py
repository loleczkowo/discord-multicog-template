from discord.ext import commands
from typing import List


class Globals:
    bot: commands.Bot | None = None
    connected: bool = False
    restarting: bool = False
    controlled_shutdown: bool = False
    cog_list: List[commands.Cog] = []

    closed_console: bool = False  # aka quiet console-ignores most logs
