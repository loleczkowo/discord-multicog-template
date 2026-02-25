import os
import sys
import asyncio
import platform
import discord
from discord.ext import commands
from dotenv import load_dotenv
from time import time

from core import log, discord_log, run_shutdown, format_time
from config import (
    IDs, ids_objects, COMMAND_PREFIX, BOT_VERSION, BOT_ACTIVITY,
    events, EV_STARTUP, EV_RECCONECT, EV_DISCONECT,
    INFO, SUCCESS, CRITICAL, WARNING)
from globals import Globals
from cogs import load_cogs, cog_list

load_dotenv()
bot_token = os.getenv("BOT_TOKEN")
if not bot_token:
    log(CRITICAL, "BOT_TOKEN environment variable not set.")
    raise ValueError("BOT_TOKEN environment variable not set.")
log(SUCCESS, f"Loaded bot token ('{bot_token[:5]}----------')")

log(INFO, "Launching bot")
first_setup = True
disconnect_time = False
bot = commands.Bot(
    command_prefix=COMMAND_PREFIX,
    intents=discord.Intents.all(),
    owner_id=IDs.USERS.OWNER,
    help_command=None,
)


@bot.event
async def on_ready():
    global first_setup, disconnect_time
    if not first_setup:
        off = disconnect_time - time()
        disconnect_time = False
        to_discord = off > 15  # notify discord when offline>10s
        log(INFO(to_discord=to_discord),
            f"Bot connection is back! offline for `{format_time(off)}`")
        Globals.connected = True
        events.call(EV_RECCONECT)
        return
    first_setup = False
    Globals.bot = bot
    log(SUCCESS, f"Logged in as: {bot.user.name} ({bot.user.id})")
    log(INFO, "building objects")
    await ids_objects.build(bot)
    discord_log(INFO, "## --- BOT BOOTING ---\n### LOADING COGS")
    log(INFO, "Loading cogs")
    await load_cogs(bot, cog_list)
    Globals.connected = True
    computer_name = platform.node()
    discord_log(INFO, f"## Bot (`V{BOT_VERSION}`) is connected with `{computer_name}`")
    events.call(EV_STARTUP)
    log(SUCCESS, "Bot fully connected")


@bot.event
async def on_disconnect():
    global disconnect_time
    if not disconnect_time:
        Globals.connected = False
        disconnect_time = time()
        log(WARNING, "Bot lost connection to discord!")
        events.call(EV_DISCONECT)


@events.on_event(EV_STARTUP, EV_RECCONECT)
async def set_bot_presence():
    await bot.change_presence(activity=BOT_ACTIVITY)


async def main():
    discord.utils.setup_logging()
    try:
        async with bot:
            await bot.start(bot_token)
    except (KeyboardInterrupt, asyncio.exceptions.CancelledError):
        Globals.connected = False
        log(INFO, "Keyboard interrupt received, shutting down.")
        if not Globals.restarting and not Globals.controlled_shutdown:
            await run_shutdown(bot)
    await asyncio.sleep(0)


if __name__ == "__main__":
    asyncio.run(main())

if Globals.restarting:
    os.execv(sys.executable, ['python'] + sys.argv)
else:
    log(INFO, "--- Bot is offline. ---")
