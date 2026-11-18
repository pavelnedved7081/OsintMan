"""Pydantic-validated loader for sources.yaml (+ .env via python-dotenv)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict, Field, ValidationError

DEFAULT_CONFIG_PATH = Path("sources.yaml")


class Defaults(BaseModel):
    model_config = ConfigDict(extra="forbid")

    timeout_seconds: float = 20
    retries: int = 2


class FeedConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    url: str
    lang: str | None = None


class SourceConfig(BaseModel):
    """Per-source settings every collector must obey (QWEN.md hard rule #3)."""

    model_config = ConfigDict(extra="forbid")

    enabled: bool = True
    ttl_minutes: int = 15
    min_interval_seconds: float = 0
    params: dict[str, Any] = Field(default_factory=dict)
    feeds: list[FeedConfig] = Field(default_factory=list)


class AppConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    defaults: Defaults = Field(default_factory=Defaults)
    sources: dict[str, SourceConfig] = Field(default_factory=dict)

    def enabled_sources(self) -> dict[str, SourceConfig]:
        return {name: cfg for name, cfg in self.sources.items() if cfg.enabled}


class ConfigError(RuntimeError):
    """Raised when sources.yaml is missing or invalid."""


def load_config(path: str | Path = DEFAULT_CONFIG_PATH) -> AppConfig:
    """Load and validate sources.yaml; also loads .env into the environment."""
    load_dotenv(override=False)
    p = Path(path)
    if not p.is_file():
        raise ConfigError(f"config file not found: {p}")
    try:
        raw = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:  # pragma: no cover - error surface
        raise ConfigError(f"invalid YAML in {p}: {exc}") from exc
    try:
        return AppConfig.model_validate(raw)
    except ValidationError as exc:
        raise ConfigError(f"invalid config in {p}:\n{exc}") from exc
