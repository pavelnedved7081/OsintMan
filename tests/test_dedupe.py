"""Unit tests for canonical-URL dedupe (incl. Persian/Unicode URLs + utm params).

Offline only — no network access.
"""

from __future__ import annotations

import pytest

from osintman.dedupe import canonical_url


def test_strips_utm_params_and_fragment():
    url = "https://Example.COM/article?utm_source=x&utm_medium=social&id=42#comments"
    assert canonical_url(url) == "https://example.com/article?id=42"


def test_strips_fbclid_gclid():
    url = "https://site.com/p?a=1&fbclid=abc&gclid=xyz"
    assert canonical_url(url) == "https://site.com/p?a=1"


def test_lowercases_host_keeps_path_case():
    url = "HTTPS://WWW.BBC.CO.UK/Persian/Article-1"
    assert canonical_url(url) == "https://www.bbc.co.uk/Persian/Article-1"


def test_persian_unicode_url_is_stable_and_normalized():
    base = "https://biazaannews.ir/اخبار/تهران-۱۴۰۳"
    tracked = base + "?utm_campaign=fb#top"
    assert canonical_url(tracked) == canonical_url(base)
    # Unicode path is percent-encoded (UTF-8) and stable across calls
    canon = canonical_url(base)
    assert canon.startswith("https://biazaannews.ir/%D8%A7")
    assert "#" not in canon


def test_unicode_percent_encoded_equivalence():
    from urllib.parse import quote

    raw = "https://example.ir/اخبار"
    encoded = "https://example.ir/" + quote("اخبار")
    assert canonical_url(raw) == canonical_url(encoded)


def test_default_path_added_and_empty_query_removed():
    assert canonical_url("https://Site.com") == "https://site.com/"


def test_port_preserved():
    assert canonical_url("http://LOCALHOST:8000/x?b=2&a=1") == "http://localhost:8000/x?b=2&a=1"


def test_dedupe_key_via_orchestrator_counts_duplicates():
    from osintman.core import _dedupe_key
    from osintman.models import ArticleData, Finding

    f1 = Finding(
        source="a", target="t",
        data=ArticleData(title="x", url="https://e.com/p?utm_source=news"),
    )
    f2 = Finding(
        source="b", target="t",
        data=ArticleData(title="x copy", url="https://E.com/p#frag"),
    )
    assert _dedupe_key(f1) == _dedupe_key(f2)


@pytest.mark.parametrize(
    ("u1", "u2"),
    [
        ("https://a.com/x?utm_term=1", "https://a.com/x"),
        ("https://A.com/x/", "https://a.com/x/"),
    ],
)
def test_canonical_equivalences(u1: str, u2: str):
    assert canonical_url(u1) == canonical_url(u2)
