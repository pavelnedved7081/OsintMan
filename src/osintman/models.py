"""Data models for OsintMan findings.

Every Finding stores: source, target, data, raw payload, collected_at_utc (ISO UTC).
See QWEN.md ("Hard rules" #4) for the contract.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field


def utcnow() -> datetime:
    """Current time as a timezone-aware UTC datetime."""
    return datetime.now(UTC)


class ArticleData(BaseModel):
    """Normalized article payload shared by all collectors."""

    kind: Literal["article"] = "article"
    title: str
    url: str
    domain: str | None = None
    lang: str | None = None
    published_at: datetime | None = None
    extra: dict[str, Any] = Field(default_factory=dict)


class Finding(BaseModel):
    """A single piece of intelligence collected from one source about one target."""

    id: str = Field(default_factory=lambda: uuid4().hex)
    source: str
    target: str
    data: ArticleData | dict[str, Any]
    raw: Any = None
    collected_at_utc: datetime = Field(default_factory=utcnow)
