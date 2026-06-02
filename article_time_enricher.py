# article_time_enricher.py — fetch publication time from article pages.
#
# Why this exists:
#   HTML-scraped sources (Mercado & Consumo, Ecommerce Brasil, Anatel, CADE,
#   etc.) often expose only the day in their listing HTML — no time. The
#   article page itself usually has the precise pubdate in <meta> or <time>
#   tags. We fetch the curated items' article pages to enrich them with
#   HH:MM precision.
#
# Cost: ~1 HTTP call per curated item that's missing time. ~30-60s for 50
# items. Runs in a thread pool for parallelism.
#
# Safe defaults:
#   - Only fetches items where date is "YYYY-MM-DD" (no time already).
#   - Skips google-search and news.google.com URLs.
#   - 8s per-item timeout; failure leaves original date unchanged.

import re
import ssl
import socket
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional

_SSL = ssl.create_default_context()
_TIMEOUT = 8
_WORKERS = 8
# How many bytes of the article to fetch when reading its pubdate. Bumped from
# 30 KB to 220 KB on 2026-05-28: some sites (e.g. Estadão) place the JSON-LD
# "datePublished" block deep in the document (~285 KB), well past 30 KB.
_FETCH_BYTES = 220000

# Patterns to extract publication time from an article page.
# Priority: most-reliable schema.org markup first.
_PATTERNS = [
    # Brazilian-portal data layer: "data_publicacao":"2026-03-23T17:35:20-03:00"
    # Estadão (and others) emit this early in the document (~5 KB in), so it is
    # the most reliable catch for those sources within the fetch window.
    re.compile(r'["\']data_publicacao["\']\s*:\s*["\'](\d{4}-\d{2}-\d{2}T\d{2}:\d{2})', re.I),
    # JSON-LD NewsArticle: "datePublished":"2026-03-23T17:35:20-03:00"
    # The cross-site standard. Added 2026-05-28 after a 2-month-old Estadão
    # article (Google News mis-dated it "today") leaked into the digest because
    # none of the meta/<time> patterns matched.
    re.compile(r'["\']datePublished["\']\s*:\s*["\'](\d{4}-\d{2}-\d{2}T\d{2}:\d{2})', re.I),
    # <meta property="article:published_time" content="2026-05-22T14:30:00...">
    re.compile(r'<meta[^>]+property=["\']article:published_time["\'][^>]+content=["\'](\d{4}-\d{2}-\d{2}T\d{2}:\d{2})', re.I),
    # <meta itemprop="datePublished" content="2026-05-22T14:30:00...">
    re.compile(r'<meta[^>]+itemprop=["\']datePublished["\'][^>]+content=["\'](\d{4}-\d{2}-\d{2}T\d{2}:\d{2})', re.I),
    # Reverse: content="..." first, itemprop after
    re.compile(r'<meta[^>]+content=["\'](\d{4}-\d{2}-\d{2}T\d{2}:\d{2})[^>]+(?:itemprop=["\']datePublished["\']|property=["\']article:published_time["\'])', re.I),
    # <time datetime="2026-05-22T14:30:00...">
    re.compile(r'<time[^>]+datetime=["\'](\d{4}-\d{2}-\d{2}T\d{2}:\d{2})', re.I),
    # Loose: any content="ISO datetime with time"
    re.compile(r'content=["\'](\d{4}-\d{2}-\d{2}T\d{2}:\d{2})', re.I),
]

# Common UA — some sites block default urllib
_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"


def _fetch_head(url: str) -> Optional[bytes]:
    """Fetch the leading chunk of an article page (head + opening body is
    enough for almost all date markup). Window is _FETCH_BYTES."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": _UA, "Range": f"bytes=0-{_FETCH_BYTES}"})
        with urllib.request.urlopen(req, timeout=_TIMEOUT, context=_SSL) as r:
            return r.read(_FETCH_BYTES)
    except Exception:
        # Some sites reject Range header; try without
        try:
            req = urllib.request.Request(url, headers={"User-Agent": _UA})
            with urllib.request.urlopen(req, timeout=_TIMEOUT, context=_SSL) as r:
                return r.read(_FETCH_BYTES)
        except Exception:
            return None


def _extract_time(html_bytes: bytes) -> Optional[str]:
    """Return 'YYYY-MM-DD HH:MM' if any pattern matches, else None."""
    if not html_bytes:
        return None
    try:
        txt = html_bytes.decode("utf-8", errors="replace")
    except Exception:
        return None
    for pat in _PATTERNS:
        m = pat.search(txt)
        if m:
            iso = m.group(1)  # e.g. "2026-05-22T14:30"
            return iso[:10] + " " + iso[11:16]
    return None


def _enrich_one(item: Dict) -> bool:
    """Mutate item in place if we can extract a more precise time.
    Returns True if updated."""
    url = (item.get("link") or "").strip()
    if not url or not url.startswith("http"):
        return False
    # Skip Google search / news.google.com (no article content there)
    if "google.com/search" in url or "news.google.com" in url:
        return False
    raw = _fetch_head(url)
    if not raw:
        return False
    when = _extract_time(raw)
    if not when:
        return False
    # Sanity: keep the existing date but replace with the more precise one
    item["date"] = when
    return True


def enrich(items: List[Dict]) -> Dict[str, int]:
    """Enrich items that have date-only timestamps with HH:MM from the
    article page. Returns counters: {checked, updated, skipped}.
    """
    if not items:
        return {"checked": 0, "updated": 0, "skipped": 0}
    # Only target items that have date-only (10 chars, no space-HH:MM)
    to_check = []
    skipped = 0
    for i, it in enumerate(items):
        d = (it.get("date") or "").strip()
        if len(d) == 10 and not it.get("_time_enriched"):
            # Looks like YYYY-MM-DD without HH:MM
            to_check.append(i)
        else:
            skipped += 1
    if not to_check:
        return {"checked": 0, "updated": 0, "skipped": skipped}
    updated = 0
    with ThreadPoolExecutor(max_workers=_WORKERS) as ex:
        futs = {ex.submit(_enrich_one, items[i]): i for i in to_check}
        for f in as_completed(futs):
            try:
                if f.result(timeout=_TIMEOUT + 2):
                    items[futs[f]]["_time_enriched"] = True
                    updated += 1
            except Exception:
                pass
    return {"checked": len(to_check), "updated": updated, "skipped": skipped}


# ── Freshness verification (added 2026-05-26) ─────────────────────────────────
# Root-cause fix for stale-leak bug: HTML scrapers fall back to "today" when
# the listing page has no date near a link (e.g. Estadão "recommended"
# sidebar cross-links to weeks-old articles). Those leak into the digest
# dated today. This verifies each curated item's REAL pubdate from the
# article page and flags items older than the lookback window for removal.

def _real_date_of(item: Dict) -> Optional[str]:
    """Fetch the article and return its real 'YYYY-MM-DD HH:MM' pubdate,
    or None if not determinable."""
    url = (item.get("link") or "").strip()
    if not url or not url.startswith("http"):
        return None
    if "google.com/search" in url or "news.google.com" in url:
        return None
    raw = _fetch_head(url)
    if not raw:
        return None
    return _extract_time(raw)


def verify_freshness(items: List[Dict], max_age_hours: int) -> Dict:
    """Fetch each item's article page, read the real pubdate, and:
      - if real date is within max_age_hours: update item['date'] to the
        precise value (also enriches HH:MM)
      - if real date is OLDER than max_age_hours: mark for removal
      - if real date can't be determined: leave item untouched (keep it)
    Returns {checked, corrected, stale_titles: [...]}.
    The caller is responsible for removing items whose 'headline' is in
    stale_titles from the report.
    """
    from datetime import datetime, timedelta
    try:
        from config import LOCAL_TZ
    except Exception:
        LOCAL_TZ = None
    if not items:
        return {"checked": 0, "corrected": 0, "stale_titles": []}

    now = datetime.now(LOCAL_TZ) if LOCAL_TZ else datetime.now()
    cutoff = now - timedelta(hours=max_age_hours)

    # Only verify items with a real http link (skip google-search fallbacks)
    to_check = [i for i, it in enumerate(items)
                if (it.get("link") or "").startswith("http")
                and "google.com/search" not in (it.get("link") or "")
                and "news.google.com" not in (it.get("link") or "")]

    corrected = 0
    stale_titles = []

    def _check(i):
        return i, _real_date_of(items[i])

    with ThreadPoolExecutor(max_workers=_WORKERS) as ex:
        futs = {ex.submit(_check, i): i for i in to_check}
        for f in as_completed(futs):
            try:
                i, real = f.result(timeout=_TIMEOUT + 2)
            except Exception:
                continue
            if not real:
                continue
            # Parse real date
            try:
                real_dt = datetime.strptime(real, "%Y-%m-%d %H:%M")
                if LOCAL_TZ:
                    real_dt = real_dt.replace(tzinfo=LOCAL_TZ)
            except Exception:
                continue
            if real_dt < cutoff:
                # Stale — flag for removal
                stale_titles.append(items[i].get("headline", ""))
            else:
                # Fresh — correct the displayed date to the precise value
                items[i]["date"] = real
                items[i]["_time_enriched"] = True
                corrected += 1

    return {"checked": len(to_check), "corrected": corrected,
            "stale_titles": stale_titles}
