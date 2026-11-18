"""Async orchestrator: runs collectors, enforces pacing, dedupes findings.

Per-source min_interval_seconds is enforced across calls within one scan via
per-source locks + last-call timestamps. Articles are deduped by canonical URL
(see :mod:`osintman.dedupe`).
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field

from osintman.config import AppConfig, SourceConfig
from osintman.dedupe import canonical_url
from osintman.models import ArticleData, Finding
from osintman.registry import Collector


@dataclass
class ScanResult:
    """Outcome of one scan over a set of sources for one keyword target."""

    target: str
    findings: list[Finding] = field(default_factory=list)
    duplicates: int = 0
    errors: dict[str, str] = field(default_factory=dict)


class Orchestrator:
    """Runs registered collectors against a target with pacing + dedupe."""

    def __init__(self, config: AppConfig, collectors: dict[str, Collector]) -> None:
        self._config = config
        self._collectors = collectors
        self._locks: dict[str, asyncio.Lock] = {}
        self._last_call: dict[str, float] = {}

    def _lock(self, name: str) -> asyncio.Lock:
        if name not in self._locks:
            self._locks[name] = asyncio.Lock()
        return self._locks[name]

    async def _enforce_interval(self, name: str, cfg: SourceConfig) -> None:
        interval = cfg.min_interval_seconds
        async with self._lock(name):
            now = time.monotonic()
            last = self._last_call.get(name)
            if last is not None and interval > 0:
                wait = interval - (now - last)
                if wait > 0:
                    await asyncio.sleep(wait)
            self._last_call[name] = time.monotonic()

    async def scan(self, target: str, source_names: list[str] | None = None) -> ScanResult:
        """Collect from enabled sources (optionally restricted to *source_names*)."""
        enabled = self._config.enabled_sources()
        if source_names is not None:
            selected = {n: enabled[n] for n in source_names if n in enabled}
        else:
            selected = enabled

        result = ScanResult(target=target)
        tasks = [
            self._run_one(name, cfg, target) for name, cfg in selected.items()
        ]
        outcomes = await asyncio.gather(*tasks) if tasks else []

        seen: set[str] = set()
        for name, findings, error in outcomes:
            if error is not None:
                result.errors[name] = error
                continue
            for f in findings:
                key = _dedupe_key(f)
                if key in seen:
                    result.duplicates += 1
                    continue
                seen.add(key)
                result.findings.append(f)
        return result

    async def _run_one(
        self, name: str, cfg: SourceConfig, target: str
    ) -> tuple[str, list[Finding], str | None]:
        collector = self._collectors.get(name)
        if collector is None:
            return name, [], "no collector implemented/registered"
        try:
            await self._enforce_interval(name, cfg)
            findings = await collector.collect(target, cfg)
            return name, findings, None
        except Exception as exc:  # noqa: BLE001 — report, never crash the scan
            return name, [], f"{type(exc).__name__}: {exc}"


def _dedupe_key(finding: Finding) -> str:
    data = finding.data
    if isinstance(data, ArticleData):
        return f"article:{canonical_url(data.url)}"
    return f"other:{finding.source}:{finding.id}"
