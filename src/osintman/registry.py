"""Collector registry: name -> Collector.

Collectors implement the contract from QWEN.md:

    class Collector:
        name: str
        async def collect(self, target: str, cfg: SourceConfig) -> list[Finding]

Registry stays EMPTY in milestone M0; collectors are added one per task via
@register (or register()).
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from osintman.config import SourceConfig
from osintman.models import Finding


@runtime_checkable
class Collector(Protocol):
    """Structural protocol every collector must satisfy."""

    name: str

    async def collect(self, target: str, cfg: SourceConfig) -> list[Finding]: ...


_registry: dict[str, type[object]] = {}


def register(cls: type[object]) -> type[object]:
    """Class decorator: register a collector under its ``name`` attribute."""
    name = getattr(cls, "name", None)
    if not isinstance(name, str) or not name:
        raise ValueError(f"collector {cls!r} must define a non-empty string 'name'")
    if name in _registry:
        raise ValueError(f"collector name already registered: {name}")
    _registry[name] = cls
    return cls


def get(name: str) -> type[object] | None:
    """Return the collector class registered under *name*, or None."""
    return _registry.get(name)


def names() -> list[str]:
    """Sorted names of all registered collectors."""
    return sorted(_registry)


def all_collectors() -> dict[str, type[object]]:
    """Snapshot of the current registry mapping."""
    return dict(_registry)


def clear() -> None:
    """Empty the registry (used by tests)."""
    _registry.clear()
