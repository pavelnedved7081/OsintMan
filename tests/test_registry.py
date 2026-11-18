"""Registry tests — registry must be EMPTY in M0; registration machinery works."""

from __future__ import annotations

import pytest

from osintman import registry
from osintman.config import SourceConfig
from osintman.models import Finding


@pytest.fixture(autouse=True)
def _clean_registry():
    saved = dict(registry._registry)
    registry.clear()
    yield
    registry._registry.clear()
    registry._registry.update(saved)


def test_registry_is_empty_in_m0():
    assert registry.names() == []
    assert registry.all_collectors() == {}


def test_register_and_get():
    class Dummy:
        name = "dummy"

        async def collect(self, target: str, cfg: SourceConfig) -> list[Finding]:
            return []

    registry.register(Dummy)
    assert registry.get("dummy") is Dummy
    assert registry.names() == ["dummy"]
    assert isinstance(Dummy(), registry.Collector)


def test_duplicate_name_rejected():
    class A:
        name = "dup"

    class B:
        name = "dup"

    registry.register(A)
    with pytest.raises(ValueError, match="already registered"):
        registry.register(B)


def test_nameless_collector_rejected():
    class NoName:
        pass

    with pytest.raises(ValueError, match="non-empty string"):
        registry.register(NoName)
