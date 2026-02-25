from typing import Callable, Dict, List, Tuple
from .data_types import Category
from discord.ext.commands import Command
from discord.app_commands import Command as AppCommand


class Categories:
    def __init__(self, *, default_category: Category):
        self.categories: Dict[str, Tuple[List[str], List[str]]] = {}
        self.default_category: Category = default_category
        # category: (["commandname"], ["slashcommandname"])
        self._func_category: Dict[int, Tuple[Category, str, bool]] = {}
        # CLEANUP DATA id(func): (category, funcname, isapp)
        self._cog_registered: Dict[str, List[Callable]] = {}  # classname: [func]

    def set_cog_category(self, category: Category):
        def ctg(cls: type):
            cls.__custom_cmd_category_class__ = category
            return cls
        return ctg

    def set_category(self, category: Category):
        def ctg(func: Callable):
            func.__custom_cmd_category__ = category
            return func
        return ctg

    def load_cog(self, cog: type):
        default = self.default_category
        if hasattr(cog, "__custom_cmd_category_class__"):
            default = cog.__custom_cmd_category_class__
        for attr_name in dir(cog):
            if attr_name.startswith("__"):
                continue
            attr = getattr(cog, attr_name)

            category = None
            if hasattr(attr, "__custom_cmd_category__"):
                category: Category = getattr(attr, "__custom_cmd_category__")
            elif hasattr(attr, "callback"):
                if hasattr(attr.callback, "__custom_cmd_category__"):
                    category: Category = attr.callback.__custom_cmd_category__
            if isinstance(attr, Command):
                app_cmd = False
            elif isinstance(attr, AppCommand):
                app_cmd = True
            else:
                if category is None:
                    continue
                raise RuntimeError("Only commands can have categories")
            if category is None:
                category = default
            cmd_name = getattr(attr, "qualified_name")
            if category.name not in self.categories:
                self.categories[category.name] = ([], [])
            self.categories[category.name][app_cmd].append(cmd_name)

            self._func_category[id(attr)] = (category, cmd_name, app_cmd)
            if cog.__class__.__name__ in self._cog_registered:
                self._cog_registered[cog.__class__.__name__].append(attr)
            else:
                self._cog_registered[cog.__class__.__name__] = [attr]

    def unload_cog(self, cogname: str):
        if cogname not in self._cog_registered:
            return
        for attr in self._cog_registered[cogname]:
            category, cmd_name, app_cmd = self._func_category[id(attr)]
            self.categories[category.name][app_cmd].remove(cmd_name)
            del self._func_category[id(attr)]
        del self._cog_registered[cogname]
