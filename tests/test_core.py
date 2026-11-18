"""Orchestrator tests: dedupe, min-interval pacing, error capture. Offline only."""

from __future__ import annotations

import asyncio
import time

from osintman.config import AppConfig, SourceConfig
from osintman.core import Orchestrator
from osintman.models import ArticleData, Finding


def _cfg(**overrides) -> AppConfig:  # type: ignore[no-untyped-def]
    sources = {"s1": SourceConfig(**overrides)}
    return AppConfig(sources=sources)


def _article(url: str, title: str = "t", source: str = "s1") -> Finding:
    return Finding(source=source, target="kw", data=ArticleData(title=title, url=url))


class FakeCollector:
    name = "s1"

    def __init__(self, findings=None, error=None, delay=0.0):
        self._findings = findings or []
        self._error = error
        self._delay = delay
        self.calls = 0

    async def collect(self, target, cfg):
        self.calls += 1
        if self._delay:
            await asyncio.sleep(self._delay)
        if self._error:
            raise self._error
        return list(self._findings)


def test_dedupe_across_sources():
    c = FakeCollector(
        [
            _article("https://e.com/a?utm_source=x"),
            _article("https://E.COM/a#frag"),  # duplicate of previous
            _article("https://e.com/b"),
        ]
    )
    orch = Orchestrator(_cfg(), {"s1": c})
    result = asyncio.run(orch.scan("kw"))
    assert len(result.findings) == 2
    assert result.duplicates == 1


def test_error_captured_not_raised():
    c = FakeCollector(error=RuntimeError("boom"))
    orch = Orchestrator(_cfg(), {"s1": c})
    result = asyncio.run(orch.scan("kw"))
    assert result.findings == []
    assert "boom" in result.errors["s1"]


def test_missing_collector_reported():
    orch = Orchestrator(_cfg(), {})
    result = asyncio.run(orch.scan("kw"))
    assert "no collector" in result.errors["s1"]


def test_min_interval_enforced_between_calls():
    c = FakeCollector([])
    cfg = _cfg(min_interval_seconds=0.2)
    orch = Orchestrator(cfg, {"s1": c})

    async def run_twice():
        await orch.scan("kw")
        t0 = time.monotonic()
        await orch.scan("kw")
        return time.monotonic() - t0

    elapsed = asyncio.run(run_twice())
    assert elapsed >= 0.15  # second call waited for the interval
    assert c.calls == 2


def test_source_selection_filter():
    cfg = AppConfig(
        sources={"a": SourceConfig(), "b": SourceConfig(enabled=False)}
    )
    calls: list[str] = []

    class C:
        name = "a"

        async def collect(self, target, cfg):
            calls.append("a")
            return []

    orch = Orchestrator(cfg, {"a": C()})
    result = asyncio.run(orch.scan("kw", source_names=["a", "b"]))
    assert calls == ["a"]  # b disabled
    assert result.errors == {}
