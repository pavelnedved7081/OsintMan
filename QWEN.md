# OSINTMAN — Live media-monitoring OSINT CLI (media-first)

## Purpose
Passive, public-source media intelligence. Collect live articles for a keyword
from multiple sources, dedupe, report. Later milestones: watch-mode with diffs.

## Stack (pinned)
Python 3.11+, httpx (async), Typer, Rich, pydantic v2, feedparser, tenacity,
PyYAML, python-dotenv. Tests: pytest + respx. Lint: ruff. Types: mypy strict.

## Hard rules
1. PASSIVE ONLY: public APIs/feeds. No logins, no active scanning, no breach data.
2. No secrets in code. Env vars only. Milestone M0 needs NO API keys.
3. Every collector obeys sources.yaml: enabled, ttl_minutes, min_interval_seconds.
4. Every Finding stores: source, target, data, raw payload, collected_at_utc (ISO UTC).
5. Dedupe articles by canonical URL (strip utm_*, fbclid, gclid, fragments; lowercase host).
6. Tests NEVER hit the real network: respx mocks + local fixtures only.
7. One collector per task. Never refactor unrelated modules.
8. Definition of done: code + `pytest -q` green + `ruff check` clean +
   sources.yaml entry + docstring with the API docs URL.

## Architecture
src/osintman/: models.py (Finding, ArticleData), config.py (sources.yaml + env),
registry.py (name -> collector), core.py (async orchestrator, per-source
min-interval, dedupe), report.py (Rich table + reports/<ts>_<slug>/report.md,
findings.json, raw/), cli.py (Typer: `osintman scan keyword TEXT [--hours N]
[--sources a,b]`, `osintman sources`), collectors/ (one file per source).

## Collector contract
class Collector: name: str;
async def collect(self, target: str, cfg: SourceConfig) -> list[Finding]
ArticleData: title, url, domain, lang, published_at (UTC|None), extra: dict.

## API notes (verify against official docs when implementing)
- GDELT DOC 2.0: https://api.gdeltproject.org/api/v2/doc/doc — mode=ArtList,
  format=json, maxrecords<=250, timespan e.g. "24h", sort=DateDesc.
  May return plain-text errors with HTTP 200: handle defensively.
- Google News RSS: https://news.google.com/rss/search?q=<kw>&hl=fa&gl=IR&ceid=IR:fa
  Links are Google redirects: keep original URL in raw; real domain from <source>.
- HN Algolia: https://hn.algolia.com/api/v1/search_by_date?query=<kw>&tags=story
- RSS: feedparser; keyword filter on title+summary must be Unicode-aware (Persian).
