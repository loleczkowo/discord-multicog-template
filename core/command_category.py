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
        self._sort_categories_left: List[Category] = []
        self._sort_categories_right: List[Category] = []
        self._sort_categories_middle: List[Category] = []
        self._sort_left_data: Dict[Dict] = {"var": 0, "go": {}}
        self._sort_right_data: Dict[Dict] = {"var": 0, "go": {}}

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

    def get_categories(self):
        return (self._sort_categories_left +
                self._sort_categories_middle +
                self._sort_categories_right)

    def _place_category(self, category: Category):
        def __place_category(level: int, now: Dict, i: int):
            if level <= 0:
                now["var"] = now.get("var", 0) + 1
                return now, i
            if "go" not in now:
                now["go"] = {}
            i2 = i + now.get("var", 0)
            now["go"], fi = __place_category(level-1, now["go"], i2)
            return now, fi

        if category.sort_priority is None:
            if category not in self._sort_categories_middle:
                self._sort_categories_middle.append(category)
            return
        if category in self._sort_categories_left + self._sort_categories_right:
            return
        if category.sort_priority < 0:
            _, i = __place_category(-category.sort_priority-1, self._sort_right_data, 0)
            self._sort_categories_right.insert(
                len(self._sort_categories_right)-i, category)
        else:
            _, i = __place_category(category.sort_priority, self._sort_left_data, 0)
            self._sort_categories_left.insert(i, category)

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
            self._place_category(category)
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
