"""Typer CLI entry point.

Commands:
    osintman scan keyword TEXT [--hours N] [--sources a,b]
    osintman sources
"""

from __future__ import annotations

import asyncio
from typing import Optional

import typer
from rich.console import Console

from osintman import __version__
from osintman.config import ConfigError, load_config
from osintman.core import Orchestrator
from osintman.registry import all_collectors
from osintman.report import print_console, write_report

app = typer.Typer(
    name="osintman",
    help="Passive, public-source media-monitoring OSINT CLI.",
    no_args_is_help=True,
)
keyword_app = typer.Typer(help="Keyword-based scans.", no_args_is_help=True)
app.add_typer(keyword_app, name="keyword")

_console = Console()


def _version_callback(value: bool) -> None:
    if value:
        _console.print(f"osintman {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Optional[bool] = typer.Option(  # noqa: UP045
        None, "--version", callback=_version_callback, is_eager=True,
        help="Show version and exit.",
    ),
) -> None:
    """OsintMan — passive media-monitoring OSINT CLI."""


@keyword_app.command("scan")
def scan_keyword(
    text: str = typer.Argument(..., help="Keyword / phrase to monitor."),
    hours: int = typer.Option(24, "--hours", help="Look-back window in hours."),
    sources: Optional[str] = typer.Option(  # noqa: UP045
        None, "--sources", help="Comma-separated source names (default: all enabled)."
    ),
    config: str = typer.Option("sources.yaml", "--config", help="Path to sources.yaml."),
    output: str = typer.Option("reports", "--output", help="Reports output directory."),
) -> None:
    """Scan configured sources for a keyword and write a report."""
    try:
        cfg = load_config(config)
    except ConfigError as exc:
        _console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=2) from exc

    names = [s.strip() for s in sources.split(",")] if sources else None
    orchestrator = Orchestrator(cfg, collectors=_instantiate_collectors())
    result = asyncio.run(orchestrator.scan(text, source_names=names))

    _console.print(f"[bold]Target:[/bold] {text}  [bold]Window:[/bold] {hours}h")
    print_console(result)
    out_dir = write_report(result, base_dir=output)
    _console.print(f"Report written to [green]{out_dir}[/green]")


@app.command("sources")
def list_sources(
    config: str = typer.Option("sources.yaml", "--config", help="Path to sources.yaml."),
) -> None:
    """List configured sources and their status."""
    try:
        cfg = load_config(config)
    except ConfigError as exc:
        _console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=2) from exc

    registered = set(all_collectors())
    from rich.table import Table

    table = Table(title="Configured sources")
    table.add_column("Name", style="cyan")
    table.add_column("Enabled")
    table.add_column("TTL (min)")
    table.add_column("Min interval (s)")
    table.add_column("Collector ready")
    for name, scfg in cfg.sources.items():
        table.add_row(
            name,
            "yes" if scfg.enabled else "no",
            str(scfg.ttl_minutes),
            str(scfg.min_interval_seconds),
            "yes" if name in registered else "[dim]not yet[/dim]",
        )
    _console.print(table)


def _instantiate_collectors() -> dict:
    """Build name -> collector instances from the registry.

    Empty in M0 by design: collectors are added one per task later.
    """
    instances = {}
    for name, cls in all_collectors().items():
        instances[name] = cls()  # type: ignore[operator]
    return instances


if __name__ == "__main__":  # pragma: no cover
    app()
