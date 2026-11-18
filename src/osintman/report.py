"""Report writer: Rich console table + reports/<ts>_<slug>/ output directory.

Writes report.md, findings.json and raw/ payloads for one ScanResult.
"""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from pathlib import Path

from rich.console import Console
from rich.table import Table

from osintman.core import ScanResult
from osintman.models import ArticleData


def slugify(text: str, max_len: int = 40) -> str:
    """ASCII-safe filesystem slug; falls back to 'target' for pure-Unicode text."""
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    if not slug:
        slug = "target"
    return slug[:max_len].rstrip("-") or "target"


def render_table(result: ScanResult) -> Table:
    """Build a Rich table summarizing findings."""
    table = Table(title=f"OsintMan findings — {result.target}")
    table.add_column("Source", style="cyan")
    table.add_column("Title", overflow="fold")
    table.add_column("Domain", style="green")
    table.add_column("Published")
    table.add_column("URL", overflow="fold")
    for f in result.findings:
        data = f.data
        if isinstance(data, ArticleData):
            published = data.published_at.isoformat() if data.published_at else "-"
            table.add_row(f.source, data.title, data.domain or "-", published, data.url)
        else:
            table.add_row(f.source, "(non-article)", "-", "-", "-")
    return table


def print_console(result: ScanResult) -> None:
    console = Console()
    if result.findings:
        console.print(render_table(result))
    else:
        console.print("[yellow]No findings.[/yellow]")
    for source, err in result.errors.items():
        console.print(f"[red]source '{source}' error:[/red] {err}")
    console.print(
        f"{len(result.findings)} finding(s), {result.duplicates} duplicate(s) deduped."
    )


def write_report(
    result: ScanResult,
    base_dir: str | Path = "reports",
    timestamp: datetime | None = None,
) -> Path:
    """Write report.md / findings.json / raw/ under reports/<ts>_<slug>/; return dir."""
    ts = timestamp or datetime.now(UTC)
    stamp = ts.strftime("%Y%m%dT%H%M%SZ")
    out = Path(base_dir) / f"{stamp}_{slugify(result.target)}"
    raw_dir = out / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    (out / "findings.json").write_text(
        json.dumps([f.model_dump(mode="json") for f in result.findings],
                   ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    lines = [
        f"# OsintMan report — {result.target}",
        "",
        f"- Generated (UTC): {ts.isoformat()}",
        f"- Findings: {len(result.findings)} | Duplicates removed: {result.duplicates}",
        "",
    ]
    for f in result.findings:
        raw_path = raw_dir / f"{f.id}.json"
        raw_path.write_text(
            json.dumps(f.raw, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8",
        )
        data = f.data
        if isinstance(data, ArticleData):
            published = data.published_at.isoformat() if data.published_at else "n/a"
            lines += [
                f"## [{data.title}]({data.url})",
                f"- source: `{f.source}` | domain: {data.domain or 'n/a'} | "
                f"lang: {data.lang or 'n/a'} | published: {published}",
                f"- collected_at_utc: {f.collected_at_utc.isoformat()}",
                "",
            ]
        else:
            lines += [
                f"## finding `{f.id}` (source: {f.source})",
                f"- collected_at_utc: {f.collected_at_utc.isoformat()}",
                "",
            ]
    for source, err in result.errors.items():
        lines.append(f"> ⚠ source `{source}` error: {err}")
        lines.append("")

    (out / "report.md").write_text("\n".join(lines), encoding="utf-8")
    return out
