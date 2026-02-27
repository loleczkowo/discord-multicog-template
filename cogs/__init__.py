from globals import Globals
from .cogscore import load_cogs, reload_cogs
from .core_cogs import ControllCog, HelpCog
from .buildin_cogs import RolesCog, PingCog, StarboardCog

cog_list = [PingCog, ControllCog, HelpCog, RolesCog, StarboardCog]
Globals.cog_list = cog_list

__all__ = ["load_cogs", "reload_cogs"]
