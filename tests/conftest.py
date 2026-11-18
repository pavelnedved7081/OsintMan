"""Shared pytest fixtures."""

from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture()
def repo_sources_yaml() -> Path:
    """The repository's real sources.yaml (4 configured sources)."""
    return REPO_ROOT / "sources.yaml"
