# link_resolver.py — resolve news.google.com URLs to real publisher URLs.
#
# Why this exists:
#   Google News RSS items use encoded redirect URLs of the form
#       https://news.google.com/rss/articles/CBMi<base64>
#   These do not resolve via plain HTTP redirect — Google serves a JS page
#   that performs the redirect client-side. To get the real publisher URL
#   we must POST to the internal `batchexecute` endpoint with the encoded
#   article ID. The `googlenewsdecoder` PyPI package does this for us.
#
# Strategy:
#   1. Already-resolved (non-google) URLs pass through unchanged.
#   2. Cache hits return immediately (URLs are deterministic).
#   3. Otherwise call gnewsdecoder() in a thread pool.
#   4. Failures fall back to a Google search URL — same behavior as the
#      old `_rewrite_link` in gnews_scraper.
#
# Cache is keyed by the raw news.google.com URL and persisted to
# `output/url_cache.json`. URLs are deterministic so the cache never invalidates.

import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional
from urllib.parse import quote_plus, urlparse

try:
    from googlenewsdecoder import gnewsdecoder
    _DECODER_AVAILABLE = True
except ImportError:
    _DECODER_AVAILABLE = False

_HERE       = os.path.dirname(os.path.abspath(__file__))
CACHE_FILE  = os.path.join(_HERE, "output", "url_cache.json")
# 2026-05-22: reduced from 8 workers to 4 — bursts of 8 simultaneous decode
# calls were triggering rate-limit fallbacks (~18 of 28 items missing real URL
# in the 16:30 scheduled run). 4 workers cuts the burst in half.
MAX_WORKERS = 4
TIMEOUT_S   = 15      # bumped from 12 — gives slower decodes room
INTERVAL_S  = 1       # gnewsdecoder politeness sleep
RETRY_COUNT = 2       # number of attempts before falling back
RETRY_DELAY = 2.0     # seconds to wait between retries


# ── Cache I/O ────────────────────────────────────────────────────────────────
def _load_cache() -> Dict[str, str]:
    if not os.path.exists(CACHE_FILE):
        return {}
    try:
        with open(CACHE_FILE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_cache(cache: Dict[str, str]) -> None:
    try:
        os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"  [WARN] url_cache write failed: {e}", file=sys.stderr)


# ── Fallback (matches old gnews_scraper._rewrite_link behavior) ──────────────
def google_search_fallback(headline: str, source_domain: str = "") -> str:
    short = (headline or "")[:140].strip()
    if not short:
        return ""
    q = f'"{short}"'
    if source_domain:
        q += f" site:{source_domain}"
    return f"https://www.google.com/search?q={quote_plus(q)}"


def _domain_from(source_url: str) -> str:
    if not source_url:
        return ""
    try:
        n = urlparse(source_url).netloc.lower()
        return n[4:] if n.startswith("www.") else n
    except Exception:
        return ""


# ── Decode one ───────────────────────────────────────────────────────────────
def _decode_one(url: str) -> Optional[str]:
    """Decode a news.google.com URL. Retries with backoff on transient failures
    (rate-limit, timeout). 2026-05-22 — added because 16:30 run hit ~18/28
    fallback rate when bursts of 8 parallel calls were rate-limited."""
    import time
    if not _DECODER_AVAILABLE:
        return None
    if not url.startswith("https://news.google.com/"):
        return url
    for attempt in range(RETRY_COUNT):
        try:
            r = gnewsdecoder(url, interval=INTERVAL_S)
            if r.get("status") and r.get("decoded_url"):
                decoded = r["decoded_url"]
                if decoded.startswith("http"):
                    return decoded
            # status=False or no decoded_url → retry if attempts remain
            if attempt < RETRY_COUNT - 1:
                time.sleep(RETRY_DELAY)
        except Exception:
            if attempt < RETRY_COUNT - 1:
                time.sleep(RETRY_DELAY)
                continue
            return None
    return None


# ── Bulk resolver ────────────────────────────────────────────────────────────
def resolve_items(items: List[Dict]) -> Dict[str, int]:
    """
    Resolve the `link` field of each item to a real publisher URL.
    Mutates items in place. Returns counters for logging:
        {"resolved": N, "fallback": N, "passthrough": N, "cached": N}

    Each item is expected to have keys: link, headline (or title), source.
    Optional: source_url (improves the site: filter on fallback).
    """
    cache = _load_cache()
    counters = {"resolved": 0, "fallback": 0, "passthrough": 0, "cached": 0}

    needs_decode: List[int] = []

    for i, it in enumerate(items):
        link = (it.get("link") or "").strip()
        if not link:
            counters["passthrough"] += 1
            continue
        if not link.startswith("https://news.google.com/"):
            # Already a real URL (direct source) — leave alone.
            counters["passthrough"] += 1
            continue
        cached = cache.get(link)
        if cached:
            it["link"] = cached
            counters["cached"] += 1
            continue
        needs_decode.append(i)

    if needs_decode and _DECODER_AVAILABLE:
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
            futs = {ex.submit(_decode_one, items[i].get("link", "")): i
                    for i in needs_decode}
            for f in as_completed(futs):
                i = futs[f]
                try:
                    decoded = f.result(timeout=TIMEOUT_S)
                except Exception:
                    decoded = None
                original = items[i].get("link", "")
                if decoded and decoded.startswith("http") \
                        and not decoded.startswith("https://news.google.com/"):
                    cache[original] = decoded
                    items[i]["link"] = decoded
                    counters["resolved"] += 1

    # Anything still pointing at news.google.com → Google search fallback
    for it in items:
        link = (it.get("link") or "").strip()
        if link.startswith("https://news.google.com/") or not link:
            headline = it.get("headline") or it.get("title") or ""
            domain   = _domain_from(it.get("source_url", ""))
            fb = google_search_fallback(headline, domain)
            if fb:
                it["link"] = fb
                counters["fallback"] += 1

    _save_cache(cache)
    return counters


# ── CLI smoke test ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    samples = [
        {"link": "https://news.google.com/rss/articles/CBMiFAILEgxiSGV2Y2lQOTRZWg",
         "headline": "test headline", "source": "Test"},
        {"link": "https://example.com/already/real",
         "headline": "should pass through", "source": "Example"},
    ]
    out = resolve_items(samples)
    print("Counters:", out)
    for s in samples:
        print(" ", s["link"][:120])
