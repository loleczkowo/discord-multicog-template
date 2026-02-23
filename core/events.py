from inspect import iscoroutinefunction
import asyncio
from typing import Dict, List, Callable, Awaitable
from core.data_types import dtEvent


class Events:
    def __init__(self):
        self.registered: Dict[str, List[Callable]] = {}
        self.async_registered: Dict[str, List[Callable[[any], Awaitable[any]]]] = {}
        self.close_on_shutdown: List[int] = []  # id(func)
        self.close_on_shutdown_tasks: List[asyncio.Task] = []
        self.func_to_events: Dict[int, List[dtEvent]] = {}  # id(func): event
        self.cog_registered: Dict[str, List[Callable]] = {}  # cog_name: [funcs]

    def register(self, func: Callable, event: dtEvent, *args: dtEvent,
                 close_on_shutdown=False):
        events = [event] + list(args)
        self.func_to_events[id(func)] = events
        if iscoroutinefunction(func):
            if close_on_shutdown:
                self.close_on_shutdown.append(id(func))
            for event in events:
                sevent = event.name
                if sevent in self.async_registered:
                    self.async_registered[sevent].append(func)
                else:
                    self.async_registered[sevent] = [func]
        else:
            if close_on_shutdown:
                raise ValueError("close_on_shutdown works only on async functions")
            for event in events:
                sevent = event.name
                if sevent in self.registered:
                    self.registered[sevent].append(func)
                else:
                    self.registered[sevent] = [func]

    def unregister(self, func: Callable):
        if id(func) not in self.func_to_events:
            return
        events = self.func_to_events[id(func)]
        for event in events:
            sevent = event.name
            if func in self.registered.get(sevent, []):
                self.registered[sevent].remove(func)
            if func in self.async_registered.get(sevent, []):
                self.async_registered[sevent].remove(func)
        if id(func) in self.close_on_shutdown:
            self.close_on_shutdown.remove(id(func))
        del self.func_to_events[id(func)]

    def on_event(self, mainevent: dtEvent, *args: dtEvent, close_on_shutdown=False):
        def _on_event(func: Callable):
            self.register(func, mainevent, *args, close_on_shutdown=close_on_shutdown)
            return func
        return _on_event

    def cog_on_event(self, mainevent: dtEvent, *args: dtEvent, close_on_shutdown=False):
        def _cog_on_event(func: Callable):
            func.__events_run_on__ = [mainevent] + list(args)
            func.__events_close_on_shutdown__ = close_on_shutdown
            return func
        return _cog_on_event

    def load_cog_events(self, cog: object):
        for attr_name in dir(cog):
            attr = getattr(cog, attr_name)
            if hasattr(attr, "__events_run_on__"):
                events = attr.__events_run_on__
                event = events.pop(0)
                close_on_shutdown = attr.__events_close_on_shutdown__
                self.register(attr, event, *events, close_on_shutdown=close_on_shutdown)
                if cog.__class__.__name__ in self.cog_registered:
                    self.cog_registered[cog.__class__.__name__].append(attr)
                else:
                    self.cog_registered[cog.__class__.__name__] = [attr]

    def reload_cog_events(self, cog: object):
        for func in self.cog_registered[cog.__class__.__name__]:
            self.unregister(func)
        self.load_cog_events(cog)

    def call(self, event: dtEvent):
        sevent = event.name
        if sevent in self.async_registered:
            for async_to_run in self.async_registered[sevent]:
                task = asyncio.create_task(async_to_run())
                if id(async_to_run) in self.close_on_shutdown:
                    self.close_on_shutdown_tasks.append(task)
        if sevent not in self.registered:
            return
        for to_run in self.registered[sevent]:
            to_run()

    async def close_all_shutdown_functions(self):
        if not self.close_on_shutdown_tasks:
            return
        for task in self.close_on_shutdown_tasks:
            if task.done():
                continue
            task.cancel()
        await asyncio.gather(
            *self.close_on_shutdown_tasks,
            return_exceptions=True
        )

        self.close_on_shutdown_tasks.clear()
