# OsintMan

Passive, public-source media-monitoring OSINT CLI. Collect live articles for a
keyword from multiple sources, dedupe by canonical URL, and write reports.
Milestone M0: core scaffold — no collectors registered yet, no API keys needed.

## Install

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

Requires Python 3.11+.

## Quickstart

```bash
# List configured sources (from sources.yaml)
osintman sources

# Scan a keyword (collectors land in later milestones; registry is empty in M0)
osintman keyword scan "iran" --hours 24 --sources gdelt,rss
```

Reports are written to `reports/<UTC timestamp>_<slug>/` (`report.md`,
`findings.json`, `raw/`).

## Development

```bash
pytest -q        # offline tests only (respx mocks + local fixtures)
ruff check .     # lint
mypy src         # strict type-check
```

## Configuration

- `sources.yaml`: per-source `enabled`, `ttl_minutes`, `min_interval_seconds`, params.
- `.env` (copy `.env.example`): environment variables only — never secrets in code.
  M0 needs no keys.

See `QWEN.md` for architecture, hard rules, and the collector contract.
