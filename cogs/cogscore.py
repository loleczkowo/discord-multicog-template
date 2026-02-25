import sys
import importlib
from discord.ext import commands
from core import log, format_traceback
from config import INFO, SUCCESS, CRITICAL, events, categories


async def load_cogs(bot: commands.Bot, cog_list: list):
    failed = 0
    for cog in cog_list:
        log(INFO(to_discord=True), f"Loading {cog.__name__}...")
        try:
            await bot.add_cog(cog(bot))
            events.load_cog_events(bot.get_cog(cog.__name__))
            categories.load_cog(bot.get_cog(cog.__name__))
            log(SUCCESS, "Loaded successfully")
        except commands.errors.ExtensionAlreadyLoaded:
            log(INFO(to_discord=True), "Cog is already loaded")
            continue
        except Exception as e:
            failed += 1
            tb = "\n".join(format_traceback(e))
            log(CRITICAL(to_discord=True),
                f"Failed to load cog `{cog.__name__}`:\n```{tb}```")
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
            events.reload_cog_events(bot.get_cog(cogname))
            categories.unload_cog(cogname)
            categories.load_cog(bot.get_cog(cogname))
            log(SUCCESS, "Reloaded successfully")
        except Exception as e:
            failed += 1
            tb = "\n".join(format_traceback(e))
            log(CRITICAL(to_discord=True),
                f"Failed to reload cog `{cogname}`:\n```{tb}```")
    return failed
