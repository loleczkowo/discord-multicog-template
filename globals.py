from discord.ext import commands


class Globals:
    bot: commands.Bot | None = None
    connected: bool = False

    closed_console: bool = False  # aka quiet console-ignores most logs
