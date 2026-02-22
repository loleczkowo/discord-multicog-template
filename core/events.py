from inspect import iscoroutinefunction
import asyncio
from typing import Dict, List, Callable, Awaitable
from core.data_types import dtEvent


class Events:
    def __init__(self):
        self.registered: Dict[str, List[Callable]] = {}
        self.async_registered: Dict[str, List[Callable[[any], Awaitable[any]]]] = {}

    def on_event(self, mainevent: dtEvent, *args: dtEvent):
        def _on_event(func):
            events = [mainevent] + list(args)
            if iscoroutinefunction(func):
                for event in events:
                    sevent = event.name
                    if sevent in self.async_registered:
                        self.async_registered[sevent].append(func)
                    else:
                        self.async_registered[sevent] = [func]
            else:
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

        async def _async_call():
            for async_to_run in self.async_registered[sevent]:
                await async_to_run()
        if sevent in self.async_registered:
            asyncio.create_task(_async_call())
        if sevent not in self.registered:
            return
        for to_run in self.registered[sevent]:
            to_run()
