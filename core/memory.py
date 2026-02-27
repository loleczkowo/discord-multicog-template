import json
import asyncio
from typing import Dict
from .data_types import dtEvent
from .logs import log
from config import (
    events, EV_SHUTDOWN, MEMORY_DIR, MEMORY_MAIN_FILE, EV_STARTUP, MEMORY_AUTOSAVE_TIME,
    QINFO, CRITICAL
)

_EV_AUTOSAVE = dtEvent("memory_autosave")


class Memory:
    _memories: Dict[str, "Memory"] = {}
    # "memorywhere_varname": object

    def __new__(cls, var_name: str, default, cog_local: object = None,
                save_on_change=False):
        if cog_local is not None:
            _memory_where = \
                MEMORY_DIR/"cogs"/f"Cmemory_{cog_local.__class__.__name__}.json"
        else:
            _memory_where = MEMORY_MAIN_FILE
        key = f"{_memory_where}_{var_name}"
        if key in cls._memories:
            if not cls._memories[key]._save_on_change:
                cls._memories[key]._save_on_change = save_on_change
            return cls._memories[key]
        instance = super().__new__(cls)
        cls._memories[key] = instance
        return instance

    def __init__(self, var_name: str, default, cog_local: object = None,
                 save_on_change=False):
        if getattr(self, "_initialized", False):
            return
        if cog_local is not None:
            self._memory_where = \
                MEMORY_DIR/"cogs"/f"Cmemory_{cog_local.__class__.__name__}.json"
        else:
            self._memory_where = MEMORY_MAIN_FILE

        self._memory_name = var_name
        self._save_on_change = save_on_change
        self._memory = self._load_data(var_name)
        self._need_save = False
        self.closed = False
        if self._memory is None:
            self._memory = default
            self._save_data()
        events.register(self.close, EV_SHUTDOWN)
        events.register(self.save, _EV_AUTOSAVE)
        self._initialized = True

    def touch(self):
        if self.closed:
            raise RuntimeError("Memory already closed")
        if self._save_on_change:
            self._save_data()
        else:
            self._need_save = True

    @property
    def mem(self):
        return self._memory

    @mem.setter
    def mem(self, value):
        self._memory = value
        self.touch()

    def _load_data(self, name):
        try:
            with open(self._memory_where, "r") as f:
                data = json.load(f)
        except FileNotFoundError:
            data = {}
        except json.JSONDecodeError:
            log(CRITICAL, f"DATA CORRUPT IN `{self._memory_where}`")
            self._need_save = False
            self.close()
            return None
        if name in data:
            return data[name]
        else:
            return None

    def _save_data(self):
        self._need_save = False
        try:
            with open(self._memory_where, "r") as f:
                data = json.load(f)
        except FileNotFoundError:
            data = {}
        except json.JSONDecodeError:
            log(CRITICAL, f"DATA CORRUPT IN `{self._memory_where}`")
            self.close()
            return
        data[self._memory_name] = self._memory
        with open(self._memory_where, "w") as f:
            json.dump(data, f, indent=4)

    def save(self):
        if not self._save_on_change and self._need_save:
            self._save_data()

    def close(self):
        if self.closed:
            return
        self.closed = True
        self.save()
        events.unregister(self._save_data)
        events.unregister(self.save)
        del self.__class__._memories[f"{self._memory_where}_{self._memory_name}"]


@events.on_event(EV_STARTUP, close_on_shutdown=True)
async def _autosave_loop():
    try:
        while True:
            await asyncio.sleep(MEMORY_AUTOSAVE_TIME)
            log(QINFO, "Autosaving memory")
            events.call(_EV_AUTOSAVE)
    except asyncio.CancelledError:
        pass
