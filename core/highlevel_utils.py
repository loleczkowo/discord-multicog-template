from discord.ext.commands import Bot
from globals import Globals as G
from config import events, EV_SHUTDOWN, INFO, QINFO
from .logs import log, discord_log
# high lever utils to prevend loop imports


async def run_shutdown(bot: Bot):
    if G.controlled_shutdown:
        return  # already in shutdown process, ignore
    log(INFO, "Running shutdown process")
    G.controlled_shutdown = True
    if bot.is_closed():
        G.connected = False
    if G.connected:
        discord_log(INFO, "## BOT SHUTDOWN")
    log(QINFO, "Calling shutdown events")
    events.call(EV_SHUTDOWN)
    log(QINFO, "Closing events")
    await events.close_all_shutdown_functions()
    log(QINFO, "Closing bot connection")
    if not bot.is_closed():
        G.connected = False
        await bot.close()
