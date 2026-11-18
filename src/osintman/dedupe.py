"""Canonical-URL normalization used for article dedupe.

Rules (QWEN.md hard rule #5): strip utm_* params, fbclid, gclid and URL
fragments; lowercase the host. Unicode (e.g. Persian) URLs are preserved via
IDNA encoding of the host and percent-encoding of the path/query.
"""

from __future__ import annotations

from urllib.parse import parse_qsl, quote, unquote, urlencode, urlsplit, urlunsplit

_STRIP_PARAMS = {"fbclid", "gclid"}


def _canonical_percent_encode(text: str) -> str:
    """Decode then re-encode percent escapes so raw Unicode and %XX forms match."""
    return quote(unquote(text), safe="!#$%&'()*+,-./:;=?@_~")


def canonical_url(url: str) -> str:
    """Return a canonical form of *url* suitable as a dedupe key."""
    parts = urlsplit(url.strip())
    try:
        host = parts.hostname or ""
    except ValueError:  # malformed IPv6/authority — fall back to raw netloc
        host = parts.netloc
    host = host.lower()
    try:
        host = host.encode("idna").decode("ascii")  # Unicode hosts -> punycode
    except UnicodeError:
        pass  # e.g. empty labels / host too long — keep as-is
    if port := parts.port:
        netloc = f"{host}:{port}"
    else:
        netloc = host
    if userinfo := _userinfo(parts):
        netloc = f"{userinfo}@{netloc}"

    query_pairs = [
        (k, v)
        for k, v in parse_qsl(parts.query, keep_blank_values=True)
        if not (k.lower() in _STRIP_PARAMS or k.lower().startswith("utm_"))
    ]
    query = urlencode(query_pairs, doseq=True)

    # Normalize scheme/host case + percent-encoding; keep path case (significant).
    path = _canonical_percent_encode(parts.path) or "/"
    query = _canonical_percent_encode(query)
    return urlunsplit((parts.scheme.lower(), netloc, path, query, "")).rstrip("?")


def _userinfo(parts) -> str:  # type: ignore[no-untyped-def]
    """Rebuild the userinfo section of the netloc if present."""
    user = parts.username or ""
    if not user:
        return ""
    if parts.password:
        return f"{user}:{parts.password}"
    return user
