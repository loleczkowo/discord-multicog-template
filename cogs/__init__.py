from .cogscore import load_cogs, reload_cogs
from .core_cogs import PingCog

cog_list = [PingCog]

__all__ = ["load_cogs", "reload_cogs"]
