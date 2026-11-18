"""Report writer tests (tmp_path only — reports/ is gitignored)."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from osintman.core import ScanResult
from osintman.models import ArticleData, Finding
from osintman.report import slugify, write_report


def _result() -> ScanResult:
    f = Finding(
        source="gdelt",
        target="تهران",
        data=ArticleData(
            title="Tehran news",
            url="https://example.ir/tehran",
            domain="example.ir",
            lang="fa",
            published_at=datetime(2026, 11, 18, tzinfo=UTC),
        ),
        raw={"article": {"url": "https://example.ir/tehran"}},
    )
    return ScanResult(target="تهران", findings=[f], duplicates=1)


def test_slugify_ascii_and_unicode():
    assert slugify("Hello World!") == "hello-world"
    assert slugify("تهران") == "target"  # pure Unicode falls back


def test_write_report_layout(tmp_path: Path):
    out = write_report(
        _result(), base_dir=tmp_path,
        timestamp=datetime(2026, 11, 18, 12, 30, tzinfo=UTC),
    )
    assert out.name == "20261118T123000Z_target"
    assert (out / "report.md").is_file()
    findings = json.loads((out / "findings.json").read_text(encoding="utf-8"))
    assert findings[0]["source"] == "gdelt"
    assert findings[0]["data"]["title"] == "Tehran news"
    raws = list((out / "raw").glob("*.json"))
    assert len(raws) == 1
    assert json.loads(raws[0].read_text(encoding="utf-8"))["article"]["url"]

    md = (out / "report.md").read_text(encoding="utf-8")
    assert "Tehran news" in md
    assert "https://example.ir/tehran" in md
    assert "collected_at_utc" in md
