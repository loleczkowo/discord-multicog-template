from globals import Globals
from .cogscore import load_cogs, reload_cogs
from .core_cogs import PingCog, ControllCog, HelpCog, RolesCog

cog_list = [PingCog, ControllCog, HelpCog, RolesCog]
Globals.cog_list = cog_list

__all__ = ["load_cogs", "reload_cogs"]
