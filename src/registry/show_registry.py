from __future__ import annotations

from typing import Any, Callable, Dict, Type

from ..shows.base.show import Show


ShowFactory = Callable[..., Show]


class ShowRegistry:
    def __init__(self) -> None:
        self._registry: Dict[str, ShowFactory] = {}

    def register(self, name: str, factory: ShowFactory) -> None:
        if name in self._registry:
            raise ValueError(f"Show '{name}' is already registered")
        self._registry[name] = factory

    def create(self, name: str, *args: Any, **kwargs: Any) -> Show:
        if name not in self._registry:
            raise KeyError(f"Unknown show '{name}'")
        return self._registry[name](*args, **kwargs)


registry = ShowRegistry()
