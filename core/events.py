from inspect import iscoroutinefunction
import asyncio
from typing import Dict, List, Callable, Awaitable
from core.data_types import dtEvent


class Events:
    def __init__(self):
        self.registered: Dict[str, List[Callable]] = {}
        self.async_registered: Dict[str, List[Callable[[any], Awaitable[any]]]] = {}
        self.close_on_shutdown: set[str] = set()  # func.names
        self.close_on_shutdown_tasks: List[asyncio.Task] = []

    def on_event(self, mainevent: dtEvent, *args: dtEvent, close_on_shutdown=False):
        def _on_event(func):
            events = [mainevent] + list(args)
            if iscoroutinefunction(func):
                if close_on_shutdown:
                    self.close_on_shutdown.add(func.__name__)
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
            return func
        return _on_event

    def call(self, event: dtEvent):
        sevent = event.name
        if sevent in self.async_registered:
            for async_to_run in self.async_registered[sevent]:
                task = asyncio.create_task(async_to_run())
                if async_to_run.__name__ in self.close_on_shutdown:
                    self.close_on_shutdown_tasks.append(task)
        if sevent not in self.registered:
            return
        for to_run in self.registered[sevent]:
            to_run()

    async def close_all_shutdown_functions(self):
        if not self.close_on_shutdown_tasks:
            return
        for task in self.close_on_shutdown_tasks:
            task.cancel()
        await asyncio.gather(
            *self.close_on_shutdown_tasks,
            return_exceptions=True
        )

        self.close_on_shutdown_tasks.clear()
