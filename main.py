import os
import platform
import discord
from discord.ext import commands
from dotenv import load_dotenv

from core import log, discord_log, discord_log_loop
from config import (
    IDs, ids_objects, COMMAND_PREFIX, BOT_VERSION, BOT_ACTIVITY,
    events, EV_STARTUP, EV_RECCONECT,
    INFO, SUCCESS, CRITICAL)
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
bot = commands.Bot(
    command_prefix=COMMAND_PREFIX,
    intents=discord.Intents.all(),
    owner_id=IDs.USERS.OWNER
)


@bot.event
async def on_ready():
    global first_setup
    if not first_setup:
        log(INFO, "Bot connection is back!")
        events.call(EV_RECCONECT)
        return
    first_setup = False
    Globals.bot = bot
    log(SUCCESS, f"Logged in as: {bot.user.name} ({bot.user.id})")
    log(INFO, "building objects")
    await ids_objects.build(bot)
    bot.loop.create_task(discord_log_loop())
    discord_log(INFO, "### --- BOT BOOTING ---")
    discord_log(INFO, "### LOADING STAGE `1/2` *(`COGS`)*")
    log(INFO, "Loading cogs")
    await load_cogs(bot, cog_list)
    discord_log(INFO, "### LOADING STAGE `2/2` *(`SYNC COMMANDS`)*")
    log(INFO, "Syncing commands to guild")
    try:
        await bot.tree.sync()
        await bot.tree.sync(guild=discord.Object(id=IDs.GUILD))
        log(SUCCESS, "Commands synced successfully.")
    except discord.errors.Forbidden as e:
        log(CRITICAL(to_discord=True), f"ERROR while sync: {e}")
    Globals.connected = True
    computer_name = platform.node()
    discord_log(INFO, f"## Bot (`V{BOT_VERSION}`) is connected with `{computer_name}`")
    events.call(EV_STARTUP)
    log(SUCCESS, "Bot fully connected")


@events.on_event(EV_STARTUP, EV_RECCONECT)
async def set_bot_presence():
    await bot.change_presence(activity=BOT_ACTIVITY)


bot.run(bot_token)
