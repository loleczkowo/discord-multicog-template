from discord.ext import commands


class Globals:
    bot: commands.Bot | None = None
    connected: bool = False
    restarting: bool = False
    cog_list: list = []

    closed_console: bool = False  # aka quiet console-ignores most logs
