import sys
import importlib
from discord.ext import commands
from core import log
from config import INFO, SUCCESS, CRITICAL


async def load_cogs(bot: commands.Bot, cog_list: list):
    failed = 0
    for cog in cog_list:
        log(INFO(to_discord=True), f"Loading {cog.__name__}...")
        try:
            await bot.add_cog(cog(bot))
            log(SUCCESS(to_discord=True), "Loaded successfully")
        except commands.errors.ExtensionAlreadyLoaded:
            log(INFO(to_discord=True), "Cog is already loaded")
            continue
        except Exception as e:
            failed += 1
            tb = e.__traceback__
            while tb.tb_next:
                tb = tb.tb_next
            log(CRITICAL(to_discord=True), f"Failed to load cog {cog.__name__}: {e}")
    return failed


async def reload_cogs(bot: commands.Bot, cog_list: list):
    failed = 0
    for cog in cog_list:
        cogname = cog.__name__
        log(INFO(to_discord=True), f"Reloading {cogname}...")
        try:
            importlib.invalidate_caches()
            mod = importlib.reload(sys.modules[cog.__module__])
            new_setup = getattr(mod, cogname)
        except Exception as e:
            failed += 1
            log(CRITICAL(to_discord=True), f"Failed to reload module {cogname}: {e}")
            continue

        try:
            await bot.remove_cog(cogname)
            await bot.add_cog(new_setup(bot))
            log(SUCCESS(to_discord=True), "Reloaded successfully")
        except Exception as e:
            failed += 1
            tb = e.__traceback__
            while tb.tb_next:
                tb = tb.tb_next
            log(CRITICAL(to_discord=True), f"Failed to reload cog {cogname}: {e}")
    return failed
