"""CLI tests via typer.testing CliRunner — offline, tmp_path reports only."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from osintman.cli import app

runner = CliRunner()


def test_sources_lists_four_configured_sources(repo_sources_yaml: Path):
    result = runner.invoke(app, ["sources", "--config", str(repo_sources_yaml)])
    assert result.exit_code == 0, result.output
    for name in ("gdelt", "google_news_rss", "rss", "hn_algolia"):
        assert name in result.output


def test_sources_missing_config_fails_cleanly(tmp_path: Path):
    result = runner.invoke(app, ["sources", "--config", str(tmp_path / "nope.yaml")])
    assert result.exit_code == 2


def test_version_flag():
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "osintman" in result.output


def test_scan_keyword_writes_report_offline(repo_sources_yaml: Path, tmp_path: Path):
    # No collectors registered in M0 -> sources report "no collector" errors,
    # but the command must still succeed and write a report.
    out_dir = tmp_path / "reports"
    result = runner.invoke(
        app,
        [
            "keyword", "scan", "تهران",
            "--hours", "12",
            "--sources", "hn_algolia",
            "--config", str(repo_sources_yaml),
            "--output", str(out_dir),
        ],
    )
    assert result.exit_code == 0, result.output
    written = list(out_dir.iterdir())
    assert len(written) == 1
    assert (written[0] / "report.md").is_file()
    assert (written[0] / "findings.json").is_file()
    assert (written[0] / "raw").is_dir()
