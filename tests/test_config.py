"""Tests for the pydantic-validated config loader (offline, tmp files only)."""

from __future__ import annotations

from pathlib import Path

import pytest

from osintman.config import AppConfig, ConfigError, load_config


def test_load_repo_sources_yaml(repo_sources_yaml: Path):
    cfg = load_config(repo_sources_yaml)
    assert set(cfg.sources) == {"gdelt", "google_news_rss", "rss", "hn_algolia"}
    assert cfg.defaults.timeout_seconds == 20
    assert cfg.defaults.retries == 2
    gdelt = cfg.sources["gdelt"]
    assert gdelt.enabled is True
    assert gdelt.ttl_minutes == 15
    assert gdelt.min_interval_seconds == 5
    assert gdelt.params["maxrecords"] == 100
    rss = cfg.sources["rss"]
    assert len(rss.feeds) == 3
    assert rss.feeds[0].name == "BBC Persian"
    assert rss.feeds[0].lang == "fa"
    assert cfg.enabled_sources() == cfg.sources


def test_missing_file_raises(tmp_path: Path):
    with pytest.raises(ConfigError, match="not found"):
        load_config(tmp_path / "nope.yaml")


def test_invalid_keys_rejected(tmp_path: Path):
    p = tmp_path / "bad.yaml"
    p.write_text("sources:\n  x:\n    enabled: true\n    typo_field: 3\n", encoding="utf-8")
    with pytest.raises(ConfigError):
        load_config(p)


def test_defaults_applied_and_disabled_filtered(tmp_path: Path):
    p = tmp_path / "min.yaml"
    p.write_text(
        "defaults: { timeout_seconds: 5, retries: 0 }\n"
        "sources:\n  a: {}\n  b: { enabled: false }\n",
        encoding="utf-8",
    )
    cfg = load_config(p)
    assert cfg.defaults.timeout_seconds == 5
    assert cfg.sources["a"].ttl_minutes == 15  # default
    assert list(cfg.enabled_sources()) == ["a"]


def test_empty_appconfig_valid():
    assert AppConfig().sources == {}
