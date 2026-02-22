from discord.ext.commands import Bot
from discord import Guild, ChannelType, Role, Member
from typing import Self


class Chain:
    def __init__(self, attrs, fullreq):
        self.fullreq = fullreq
        self.attrs = attrs

    def __getattr__(self, name) -> Self | ChannelType | Role | Member:
        if name in self.attrs:
            if isinstance(self.attrs[name], dict):
                return Chain(self.attrs[name], name)
            return self.attrs[name]
        raise AttributeError(f"IDsObjects has no attribute '{self.fullreq}'")


class IDsObjects:
    def __init__(self, target):
        self.target_ids = target
        self.objects: dict = {}
        self.is_build = False

    async def _build(self, walk, checking, bot: Bot, curr_guild: Guild):
        objs = {}
        wvars: dict = vars(walk)
        if "GUILD" in wvars.keys():
            curr_guild = await bot.fetch_guild(wvars["GUILD"])
            objs["GUILD"] = curr_guild

        for name, value in wvars.items():
            if name.startswith('__'):
                continue
            if isinstance(value, type):
                objs[name] = await self._build(value, name.upper(), bot, curr_guild)
                continue
            if not isinstance(value, int):
                continue

            # specjal vars
            elif name == "GUILD":
                continue

            # class vars
            if checking not in ["ROLES", "CHANNELS", "USERS"]:
                continue
            if curr_guild is None:
                raise ValueError("Cannot fetch data without GUILD set")
            if checking == "ROLES":
                objs[name] = curr_guild.get_role(value)
            elif checking == "CHANNELS":
                objs[name] = await curr_guild.fetch_channel(value)
            elif checking == "USERS":
                objs[name] = await curr_guild.fetch_member(value)
        return objs

    async def build(self, bot: Bot):
        self.objects = await self._build(self.target_ids, "MAIN", bot, None)
        self.is_build = True

    def __getattr__(self, name) -> Chain | ChannelType | Role | Member:
        if not self.is_build:
            raise AttributeError("IDsObjects has not been built yet")
        if name in self.objects:
            if isinstance(self.objects[name], dict):
                return Chain(self.objects[name], name)
            return self.objects[name]
        raise AttributeError(f"IDsObjects has no attribute '{name}'")
