import json
import asyncio
from .data_types import dtEvent
from .logs import log
from config import (
    events, EV_SHUTDOWN, MEMORY_DIR, MEMORY_MAIN_FILE, EV_STARTUP, MEMORY_AUTOSAVE_TIME,
    QINFO, CRITICAL
)

_EV_AUTOSAVE = dtEvent("memory_autosave")


class Memory:
    def __init__(self, var_name: str, default, cog_local: object = None,
                 save_on_change=False):
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
        events.register(self._save_data, EV_SHUTDOWN)
        events.register(self.save, _EV_AUTOSAVE)

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
        self.touch()
        self._memory = value

    def _load_data(self, name):
        try:
            with open(self._memory_where, "r") as f:
                data = json.load(f)
        except FileNotFoundError:
            data = {}
        except json.JSONDecodeError:
            log(CRITICAL, f"DATA CORRUPT IN `{self._memory_where}`")
            self.close()
            return None
        if name in data:
            return data[name]
        else:
            return None

    def _save_data(self):
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
            self._need_save = False

    def close(self):
        self.closed = True
        self.save()
        events.unregister(self._save_data)
        events.unregister(self.save)


@events.on_event(EV_STARTUP, close_on_shutdown=True)
async def _autosave_loop():
    try:
        while True:
            await asyncio.sleep(MEMORY_AUTOSAVE_TIME)
            log(QINFO, "Autosaving memory")
            events.call(_EV_AUTOSAVE)
    except asyncio.CancelledError:
        pass
