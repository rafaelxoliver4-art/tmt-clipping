# merge_and_clean.py — Merge, deduplicate, score and cap headlines for Claude

import json
import os
import re
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
from config import SECTORS, MAX_HEADLINES_PER_SECTOR, MAX_TOTAL_HEADLINES, LOCAL_TZ

# ── Keyword → sector map (lowercase, built once) ─────────────────────────────
def _build_kw_sector_map() -> Dict[str, str]:
    mapping: Dict[str, str] = {}
    # Priority order: covered > keywords > peers (later writes win for peers)
    for sector, data in SECTORS.items():
        for item in data["peers"] + data["keywords"]:
            mapping[item.lower()] = sector
        for item in data["covered"]:          # covered names override
            mapping[item.lower()] = sector
    return mapping

KW_TO_SECTOR = _build_kw_sector_map()

# Flat set of all covered ticker/name strings (lowercase)
COVERED_LOWER = {
    name.lower()
    for data in SECTORS.values()
    for name in data["covered"]
}

# 2026-07-14 (June benchmark audit): also recognise full covered-name ALIASES
# in titles ("Mercado Ads", "Claro Colombia", "TIM Brasil"...) — without this,
# a direct-source story titled around an alias scored relevance 2 (generic)
# and lost its input slot to noise. Ambiguous/short aliases are excluded
# (the force-add ambiguity guard handles those contexts separately).
try:
    from config import COVERED_NAME_ALIASES as _CNA
    COVERED_LOWER |= {
        a.lower() for aliases in _CNA.values() for a in aliases
        if len(a) >= 5 and a.lower() not in {"claro", "vivo", "personal",
                                             "desktop", "sparkle"}
    }
except ImportError:
    pass


def _guess_sector(row: Dict) -> str:
    """Heuristically assign a sector using keyword + title scan."""
    keyword  = (row.get("keyword") or "").lower()
    title    = (row.get("title")   or "").lower()

    # 1. Keyword directly in map
    if keyword in KW_TO_SECTOR:
        return KW_TO_SECTOR[keyword]

    # 2. Keyword from direct scraper is already a sector name
    if keyword in {s.lower() for s in SECTORS}:
        for s in SECTORS:
            if s.lower() == keyword:
                return s

    # 3. Scan title for known names (longest match wins to avoid false positives)
    matches = []
    for kw_lower, sector in KW_TO_SECTOR.items():
        if len(kw_lower) >= 4 and re.search(r"\b" + re.escape(kw_lower) + r"\b", title):
            matches.append((len(kw_lower), sector))
    if matches:
        matches.sort(reverse=True)
        return matches[0][1]

    return "General"


def _relevance_score(row: Dict) -> int:
    """Lower score = higher priority.
       0 = covered ticker mentioned in title
       1 = keyword match (sector-relevant but not covered)
       2 = general / direct source fallback
    """
    title   = (row.get("title") or "").lower()
    keyword = (row.get("keyword") or "").lower()

    if keyword in COVERED_LOWER:
        return 0
    for name in COVERED_LOWER:
        if len(name) >= 3 and re.search(r"\b" + re.escape(name) + r"\b", title):
            return 0
    if keyword in KW_TO_SECTOR:
        return 1
    return 2


def assign_sectors(rows: List[Dict]) -> List[Dict]:
    for row in rows:
        row["sector"] = _guess_sector(row)
    return rows


# No single feed may hog a sector's slots (2026-07-14: 13 recurring Ookla
# boilerplate rows were monopolizing Telecom LatAm every day).
_PER_SOURCE_CAP = 12
# Of the total cap, always keep at least this many slots for the best gnews
# (EXT) rows — otherwise heavy direct-feed days starve covered-ticker gnews
# stories out of the curator's input entirely (2026-07-14 cross-check: 20 of
# 49 benchmark misses were lost at this stage).
_EXT_MIN_SLOTS = 60


def cap_per_sector(rows: List[Dict]) -> List[Dict]:
    """Keep at most current_max_per_sector() per sector, total ≤ current_max_total().

    PRIORITY RULES:
    - direct-source rows still outrank EXT rows (2026-05-22 principle kept),
      but WITHIN each group the most relevant rows (covered ticker > keyword
      match > generic) are admitted first, so caps trim generic noise instead
      of material items (2026-07-14).
    - max _PER_SOURCE_CAP rows per source, so boilerplate-heavy feeds can't
      monopolize a sector (2026-07-14).
    - at least _EXT_MIN_SLOTS of the total stay available to EXT rows so the
      curator always sees the best gnews stories too (2026-07-14).
    - caps are Monday-aware: 72h-lookback runs get a wider funnel
      (config.current_max_total / current_max_per_sector).
    """
    from config import current_max_total, current_max_per_sector

    # Build direct-source recognition info once
    direct_info = _direct_source_names()

    def _row_is_direct(r):
        return _is_direct(r, direct_info)

    # Stable sort: direct first, then relevance within each group; within the
    # same relevance, CORE trade feeds (the analyst's actual sources — DPL,
    # Teletime, Mobile Time, TI Inside...) outrank generic high-volume feeds
    # (2026-07-14 June audit: core-feed sector stories kept losing their input
    # slot to TechCrunch/Verge-class volume by ordering luck). Incoming
    # (roughly recency) order is preserved among remaining equals.
    try:
        from config import CORE_DIRECT_SOURCES as _CORE
    except ImportError:
        _CORE = frozenset()
    try:
        from config import SOURCES_ALLOWLIST as _ALLOW
    except ImportError:
        _ALLOW = []

    def _norm_src(s):
        return "".join(ch for ch in _strip_accents((s or "").lower())
                       if ch.isalnum())

    _allow_norm = [_norm_src(a) for a in _ALLOW if len(a) >= 4]

    def _priority(r):
        src = (r.get("source") or "").strip()
        if src in _CORE:                       # direct core trade feed
            return 0
        srcn = _norm_src(src)                  # gnews outlet of a trusted brand
        if srcn and any(a in srcn for a in _allow_norm):
            return 0
        return 1

    rows_sorted = sorted(rows, key=lambda r: (0 if _row_is_direct(r) else 1,
                                              _relevance_score(r),
                                              _priority(r)))

    max_total     = current_max_total()
    max_sector    = current_max_per_sector()
    direct_budget = max_total - _EXT_MIN_SLOTS
    # Per-sector EXT reservation: direct rows may take at most this many of a
    # sector's slots in pass 1, so the sector's best EXT rows always get a look
    # (2026-07-14: 'Software and AI' filled all 80 slots with direct rows and a
    # relevance-0 TOTVS gnews story never reached the curator). Unused reserved
    # slots are backfilled with direct rows in pass 2 — nothing is wasted.
    direct_sector_budget = max(1, max_sector - 12)

    counts: Dict[str, int] = {}
    per_source: Dict[str, int] = {}
    dir_counts: Dict[str, int] = {}
    out: List[Dict] = []
    skipped: List[Dict] = []
    n_direct = 0

    # Pass 1 — direct rows limited per sector and globally; EXT rows get a
    # GUARANTEED per-sector allotment (the 12 reserved slots), so every
    # sector's best gnews stories reach the curator regardless of how much
    # direct volume other sectors produce.
    ext_counts: Dict[str, int] = {}
    for row in rows_sorted:
        if len(out) >= max_total:
            skipped.append(row)
            continue
        sec = row.get("sector", "General")
        src_name = (row.get("source") or "").strip()
        src = (src_name.lower(), sec)  # cap per source PER SECTOR
        # Core trade feeds are curated and prolific (Mobile Time, TELETIME ≈
        # 15-25 stories/day, near-zero boilerplate) — give them more room than
        # generic/boilerplate-prone feeds (2026-07-14 June audit: an analyst
        # pick was Mobile Time's 13th story of the day and got trimmed).
        src_cap = 20 if src_name in _CORE else _PER_SOURCE_CAP
        if counts.get(sec, 0) >= max_sector:
            continue
        if per_source.get(src, 0) >= src_cap:
            continue
        is_dir = _row_is_direct(row)
        if is_dir and (n_direct >= direct_budget
                       or dir_counts.get(sec, 0) >= direct_sector_budget):
            skipped.append(row)
            continue
        if not is_dir and ext_counts.get(sec, 0) >= 12:
            skipped.append(row)   # sector's EXT reservation used; retry pass 2
            continue
        out.append(row)
        counts[sec] = counts.get(sec, 0) + 1
        per_source[src] = per_source.get(src, 0) + 1
        if is_dir:
            dir_counts[sec] = dir_counts.get(sec, 0) + 1
            n_direct += 1
        else:
            ext_counts[sec] = ext_counts.get(sec, 0) + 1

    # Pass 2 — backfill remaining capacity (EXT rows didn't claim their
    # reservation) with the rows deferred above, same order, normal caps.
    for row in skipped:
        if len(out) >= max_total:
            break
        sec = row.get("sector", "General")
        src_name = (row.get("source") or "").strip()
        src = (src_name.lower(), sec)
        src_cap = 20 if src_name in _CORE else _PER_SOURCE_CAP
        if counts.get(sec, 0) >= max_sector:
            continue
        if per_source.get(src, 0) >= src_cap:
            continue
        out.append(row)
        counts[sec] = counts.get(sec, 0) + 1
        per_source[src] = per_source.get(src, 0) + 1
    return out


import unicodedata as _ud


def _strip_accents(s: str) -> str:
    if not s:
        return ""
    nfkd = _ud.normalize("NFKD", s)
    return "".join(c for c in nfkd if not _ud.combining(c))


def _direct_source_names():
    """Returns a list of (name, brand, domain) tuples for each direct source.
       - name:   normalized full name (lowercase, accent-stripped)
       - brand:  first significant token of name (≥4 chars, accent-stripped)
       - domain: hostname extracted from url (no www., lowercase)
       Used by _is_direct to recognize gnews attributions that point at the
       same publisher under a different label."""
    try:
        from config import DIRECT_SOURCES
        from urllib.parse import urlparse
    except Exception:
        return []
    out = []
    for s in DIRECT_SOURCES:
        name = _strip_accents((s.get("name") or "").strip().lower())
        url  = s.get("url") or ""
        try:
            netloc = urlparse(url).netloc.lower()
            if netloc.startswith("www."):
                netloc = netloc[4:]
        except Exception:
            netloc = ""
        # Brand = leading distinctive token(s).
        # 3+ char acronym (CFM, ANS, MEC, CRC, IFT, JOTA, CADE) → use as brand.
        # 1-2 char article (o, el, la) → combine with next word.
        # This catches "CFM" matching "CFM Portal" while avoiding "o globo"
        # tripping on the article "o".
        words = name.split()
        if not words:
            brand = ""
        elif len(words[0]) >= 3:
            brand = words[0]
        elif len(words) >= 2:
            brand = words[0] + " " + words[1]
            if len(brand) < 4:
                brand = ""
        else:
            brand = ""
        out.append({"name": name, "brand": brand, "domain": netloc})
    return out


def _is_direct(row: Dict, direct_info) -> bool:
    """A row is direct if source_type=='direct' OR if its source attribution
       matches any direct source by:
         (a) exact normalized name
         (b) exact brand match (first-word of direct name)
         (c) 'brand ' prefix match (incoming starts with 'brand ')
         (d) direct's domain appears as substring in incoming source
    """
    if (row.get("source_type") or "").strip().lower() == "direct":
        return True
    src_raw = (row.get("source") or "").strip().lower()
    if not src_raw:
        return False
    src = _strip_accents(src_raw)
    for info in direct_info:
        # (a) exact name match
        if src == info["name"]:
            return True
        # (b) brand exact match — "Globant" == "globant"
        if info["brand"] and src == info["brand"]:
            return True
        # (c) brand-prefix match — "valor econômico" starts with "valor "
        if info["brand"] and src.startswith(info["brand"] + " "):
            return True
        # (d) domain appears in source attribution — "expansion.mx" in "expansion.mx"
        if info["domain"] and info["domain"] in src:
            return True
    return False


def _is_direct_strict(row: Dict, direct_info) -> bool:
    """Stricter version — no brand-prefix matching. Used by safety nets
    where false positives from short brand-prefixes ("folha do es" matching
    Folha Equilíbrio e Saúde) cause real damage. Only exact name, brand-exact,
    and domain matches qualify."""
    if (row.get("source_type") or "").strip().lower() == "direct":
        return True
    src_raw = (row.get("source") or "").strip().lower()
    if not src_raw:
        return False
    src = _strip_accents(src_raw)
    for info in direct_info:
        if src == info["name"]:
            return True
        if info["brand"] and src == info["brand"]:
            return True
        if info["domain"] and info["domain"] in src:
            return True
    return False


def format_for_claude(rows: List[Dict]) -> str:
    """
    Compact plain-text block for Claude.
    Format: N. <DIRECT|EXT> [Sector] Source (published): Title [lang]

    The <DIRECT|EXT> tag tells the curator which items come from the curated
    reliable-source list (DIRECT_SOURCES) vs Google News only (EXT).
    CATEGORISE_SYSTEM enforces: prefer DIRECT items; include AT MOST 5 EXT
    items across all sectors, and only if EXTREMELY material to coverage.

    NOTE: We do NOT pass the link to Claude. Link plumbing is 100% the code's
    responsibility — Claude focuses on triage and tagging only. After Claude
    returns curated items, the link is re-attached by (headline, source)
    match against the raw rows.
    """
    direct_names = _direct_source_names()
    lines = []
    for i, r in enumerate(rows, 1):
        sector = r.get("sector", "General")
        source = r.get("source", "?")
        title  = r.get("title", "")
        lang   = r.get("edition_lang", "")
        pub    = r.get("published_local", "")
        tag    = "DIRECT" if _is_direct(r, direct_names) else "EXT"
        lang_tag = f" [{lang}]" if lang and lang != "mixed" else ""
        # Show explicit "date unknown" so the curator can treat these
        # differently (lean on title for freshness signal). Was: omit entirely.
        pub_tag  = f" ({pub})" if pub else " (date unknown)"
        lines.append(f"{i:3}. <{tag}> [{sector}] {source}{pub_tag}: {title}{lang_tag}")
    return "\n".join(lines)


# ── Re-attach link + source_url after the curator returns ─────────────────────
# Claude only emits {ticker, headline, source, date} — links live with the code.
# We match curator output back to raw rows by (normalised headline, source) and
# attach `link` + `source_url` so the link resolver can decode and the email
# can render the right href.

def _covered_names():
    """Return the set of ticker symbols + company-name aliases from
    SECTORS.covered + COVERED_NAME_ALIASES. Used by enforce_covered_inclusion
    to guarantee that any DIRECT-source headline mentioning a covered name
    reaches the digest. Result is lowercase, accent-stripped.
    """
    try:
        from config import SECTORS, COVERED_NAME_ALIASES
    except Exception:
        try:
            from config import SECTORS
            COVERED_NAME_ALIASES = {}
        except Exception:
            return set()
    out = set()
    # 1. Tickers from SECTORS.covered (short, may not survive word-boundary)
    for sec, info in SECTORS.items():
        for name in info.get("covered", []) or []:
            n = _strip_accents(str(name).lower()).strip()
            if n and len(n) >= 3:
                out.add(n)
    # 2. Full company names from COVERED_NAME_ALIASES — these are the
    # primary matcher since headlines use names not tickers
    for ticker, aliases in (COVERED_NAME_ALIASES or {}).items():
        for alias in aliases:
            n = _strip_accents(str(alias).lower()).strip()
            if n and len(n) >= 3:
                out.add(n)
    return out


def _alias_to_ticker():
    """Reverse-map alias → ticker so the safety net can tag items with the
    correct covered-ticker symbol (not the alias text)."""
    try:
        from config import COVERED_NAME_ALIASES
    except Exception:
        return {}
    out = {}
    for ticker, aliases in (COVERED_NAME_ALIASES or {}).items():
        for alias in aliases:
            out[_strip_accents(str(alias).lower()).strip()] = ticker
    return out


_AMBIGUOUS_ALIASES = {
    # Short / common-word aliases that collide with non-corporate usage
    "vivo",     # Portuguese verb "alive"
    "claro",    # Portuguese word "clear"
    "tigo",     # short, rare collisions but guard anyway
    "tim",      # English name TIM, ambiguous
    "telcel",   # specific enough but guard
    "telmex",   # specific
    "endava",   # rare collisions
    "afya",
}

_CORPORATE_QUALIFIERS = {
    "acoes", "acao", "anuncia", "anunciou", "reporta", "reportou",
    "lucro", "prejuizo", "receita", "ebitda", "trimestre", "resultado",
    "balanco", "grupo", "holding", "participacoes", "s.a", "s/a", "sa",
    "investidor", "investidores", "bovespa", "b3", "rating", "guidance",
    "ipo", "follow-on", "follow on", "oferta", "secundaria", "primaria",
    "btg", "itau bba", "itau bb", "xp", "bradesco bbi", "safra", "morgan",
    "goldman", "ubs", "target", "preco-alvo", "compra", "venda", "neutro",
    "outperform", "overweight", "underweight", "underperform",
    "dividendo", "dividendos", "jcp", "juros sobre capital proprio",
    "controlada", "subsidiaria", "ms&a", "fusao", "aquisicao",
    "earnings", "results", "press release", "press-release",
    "spectrum", "espectro", "5g", "anatel", "ift", "leilao",
}


def enforce_covered_inclusion(report: dict, raw_rows: list, max_add: int = 10,
                              max_per_ticker: int = 2) -> dict:
    """Server-side safety net (added 2026-05-25; extended to all sources
    2026-05-28): make sure every row whose title contains a covered ticker /
    company name is in the curator's digest, regardless of source (DIRECT or
    Google News). For ambiguous aliases (Vivo/Tim/etc.), also requires a
    corporate qualifier OR ticker form in the title. Capped at max_per_ticker
    per name so one busy name can't flood the digest.
    """
    direct_info = _direct_source_names()
    covered = _covered_names()
    alias_map = _alias_to_ticker()
    if not covered:
        return {"added": 0, "already_present": 0, "skipped": 0}

    in_digest_titles = set()
    in_digest_urls = set()
    for sec, items in report.items():
        if sec == "_raw" or not isinstance(items, list):
            continue
        for it in items:
            t = _norm_title(it.get("headline", ""))
            if t:
                in_digest_titles.add(t)
            u = _norm_url_key(it.get("link", ""))
            if u:
                in_digest_urls.add(u)

    counter = {"added": 0, "already_present": 0, "skipped": 0}
    added_keys = set()
    per_ticker = {}   # cap forced additions per ticker so one busy name can't
                      # flood the digest with many near-duplicate variants

    for row in raw_rows:
        if counter["added"] >= max_add:
            break
        # Covered-name stories must survive regardless of source. Until
        # 2026-05-28 this was DIRECT-only; extended to ALL sources (incl.
        # Google News) so a covered-name story carried only by gnews isn't
        # dropped by the EXT cap or curator. The covered-name-in-title check
        # plus the ambiguity guard below keep false positives out, and the
        # downstream article-time check still handles stale items.
        title = row.get("title", "") or ""
        title_norm = _strip_accents(title.lower())
        import re as _re
        best_pos = None
        hit_name = None
        for cn in covered:
            if cn in title_norm:
                pat = r"(?:^|[^a-z0-9])" + _re.escape(cn) + r"(?:[^a-z0-9]|$)"
                m = _re.search(pat, title_norm)
                if m and (best_pos is None or m.start() < best_pos):
                    best_pos = m.start()
                    hit_name = cn
        if not hit_name:
            continue
        # 2026-07-14: force-add is DIRECT-only again. The 2026-05-28 extension
        # to gnews existed because EXT starvation could hide covered stories
        # from the curator entirely; cap_per_sector now GUARANTEES gnews slots
        # per sector, so covered gnews stories reach the curator and must earn
        # selection on materiality. Auto-injecting gnews rows shipped alias-
        # collision junk straight into the digest (TASE:AMX = Automax Motors,
        # "Posi Metallic" brake pads, Globant eSports, CINT price-action spam).
        if not _is_direct(row, direct_info):
            counter["skipped"] += 1
            continue
        # Guard: don't force-include a company's OWN website / PR content (e.g.
        # "Globant Newsroom", a TOTVS blog). If the source name itself contains a
        # covered name, it's the company's own channel — marketing, not news.
        _src_norm = _strip_accents((row.get("source", "") or "").lower())
        if any(re.search(r"(?:^|[^a-z0-9])" + re.escape(cn) + r"(?:[^a-z0-9]|$)", _src_norm)
               for cn in covered if len(cn) >= 4):
            counter["skipped"] += 1
            continue
        # Ambiguity guard: ambiguous aliases need ticker or corporate qualifier
        if hit_name in _AMBIGUOUS_ALIASES:
            ticker_guess = alias_map.get(hit_name, hit_name.upper())
            has_ticker = ticker_guess.lower() in title_norm or \
                         (ticker_guess + "3").lower() in title_norm
            has_qualifier = any(q in title_norm for q in _CORPORATE_QUALIFIERS)
            if not (has_ticker or has_qualifier):
                counter["skipped"] += 1
                continue
        # Skip if already in digest (title or URL match)
        tk = _norm_title(title)
        uk = _norm_url_key(row.get("link", ""))
        if tk in in_digest_titles or (uk and uk in in_digest_urls):
            counter["already_present"] += 1
            continue
        if tk in added_keys:
            continue
        # Prefer the proper ticker symbol over the matched alias text
        ticker = alias_map.get(hit_name, hit_name.upper())
        # Per-ticker cap: surface a name's top story or two, not every variant.
        if per_ticker.get(ticker, 0) >= max_per_ticker:
            counter["skipped"] += 1
            continue
        added_keys.add(tk)
        per_ticker[ticker] = per_ticker.get(ticker, 0) + 1
        # Place force-added covered-name items in their PROPER sector (2026-06-03)
        # so covered-name news shows under its theme, not a catch-all section.
        # (The "Covered-name guarantee: N force-added" console line keeps the
        # dev-facing signal that the safety net fired.)
        sec_name = _guess_sector(row)
        if sec_name not in report:
            report[sec_name] = []
        report[sec_name].append({
            "ticker": ticker,
            "headline": title,
            "source": row.get("source", ""),
            "date": row.get("published_local", ""),
            "link": row.get("link", ""),
        })
        counter["added"] += 1

    return counter


def _norm_title(s: str) -> str:
    """Normalise a title for fuzzy matching:
       NFKD-fold accents, lowercase, strip all non-alphanumeric.
       Google News often appends ' - Source Name' to titles; strip that first
       so the normalised form matches whether the curator preserved it or not.
    """
    import re as _re, unicodedata
    if not s:
        return ""
    s = s.strip()
    # Strip the trailing " - Anything" or " | Anything" tail — Google News
    # source-suffix that the curator usually removes.
    s = _re.sub(r"\s+[-–—|]\s+[^-–—|]{2,60}$", "", s)
    nfkd = unicodedata.normalize("NFKD", s)
    ascii_only = "".join(c for c in nfkd if not unicodedata.combining(c))
    return _re.sub(r"[^a-z0-9]+", "", ascii_only.lower()).strip()


def enforce_ext_cap(report: Dict, raw_rows: List[Dict], max_ext: int = 5) -> Dict[str, int]:
    """
    Code-level safety net: if the curator emitted more than `max_ext` items
    whose source is NOT a configured direct source, drop the lowest-ranked
    surplus EXT items in place. Returns counters.

    'Lowest-ranked' = appears later within its sector (curator already orders
    by materiality, so tail items are the weakest within each sector).
    """
    direct_names = _direct_source_names()
    counters = {"direct_kept": 0, "ext_kept": 0, "ext_dropped": 0}

    # First pass: count & collect ext items with locations
    ext_locations = []  # (sector, index, item)
    for sector, items in report.items():
        if sector == "_raw" or not isinstance(items, list):
            continue
        for idx, it in enumerate(items):
            if _is_direct({"source": it.get("source",""), "source_type": it.get("source_type","")}, direct_names):
                counters["direct_kept"] += 1
            else:
                ext_locations.append((sector, idx, it))

    if len(ext_locations) <= max_ext:
        counters["ext_kept"] = len(ext_locations)
        return counters

    # Keep first `max_ext` ext items (those listed earliest within their sector
    # by the curator, ordered globally by sector iteration). Drop the rest.
    to_keep = set(id(loc[2]) for loc in ext_locations[:max_ext])
    counters["ext_kept"] = max_ext
    for sector, items in report.items():
        if sector == "_raw" or not isinstance(items, list):
            continue
        kept = []
        for it in items:
            if _is_direct({"source": it.get("source",""), "source_type": it.get("source_type","")}, direct_names):
                kept.append(it)
            elif id(it) in to_keep:
                kept.append(it)
            else:
                counters["ext_dropped"] += 1
        report[sector] = kept
    return counters


def reattach_links(report: Dict, raw_rows: List[Dict]) -> Dict[str, int]:
    """
    Walk the curated report and attach `link` (and `source_url` when known)
    to each item by matching against raw_rows. Returns counters.

    Match cascade:
      1. Exact normalised (headline, source) — strongest
      2. Exact normalised headline only
      3. Substring (curator's normalised headline is contained in a raw
         normalised title, or vice-versa) — catches truncation in either
         direction (curator drops " - Source"; raw was already short)
    """
    counters = {"matched": 0, "headline_only": 0,
                "substring": 0, "unmatched": 0}

    # Build lookup tables once
    by_title_source: Dict[tuple, Dict] = {}
    by_title: Dict[str, Dict] = {}
    norm_rows: List[tuple] = []  # (norm_title, row) for substring fallback
    for r in raw_rows:
        t = _norm_title(r.get("title", ""))
        if not t:
            continue
        src = (r.get("source") or "").strip().lower()
        by_title_source.setdefault((t, src), r)
        by_title.setdefault(t, r)
        norm_rows.append((t, r))

    def _substring_lookup(needle: str) -> Optional[Dict]:
        if not needle or len(needle) < 12:
            return None
        # Prefer matches where the curator headline is a prefix of the raw
        # title (most common case — raw has source suffix curator dropped).
        for t, r in norm_rows:
            if t.startswith(needle) or needle.startswith(t):
                return r
        # Then any substring containment, but only if needle is meaningfully
        # long to avoid matching on common prefixes.
        if len(needle) >= 20:
            for t, r in norm_rows:
                if needle in t or t in needle:
                    return r
        return None

    for sector, items in report.items():
        if sector == "_raw" or not isinstance(items, list):
            continue
        for it in items:
            headline = it.get("headline", "")
            source   = (it.get("source") or "").strip().lower()
            t = _norm_title(headline)
            hit = by_title_source.get((t, source))
            high_conf = False
            if hit:
                counters["matched"] += 1
                high_conf = True
            else:
                hit = by_title.get(t)
                if hit:
                    counters["headline_only"] += 1
                    high_conf = True
                else:
                    hit = _substring_lookup(t)
                    if hit:
                        counters["substring"] += 1
            if hit:
                it["link"] = hit.get("link", "")
                if hit.get("source_url"):
                    it["source_url"] = hit["source_url"]
                # Recover the upstream source_type from the matched raw row so
                # enforce_ext_cap can recognise a genuine DIRECT item even when
                # the curator's free-text source label doesn't string-match a
                # configured direct source (abbreviation/translation/added words).
                # Only trust the two high-confidence tiers, not the loose
                # substring fallback. (2026-06-23 — fixes direct news being
                # mislabelled EXT and dropped by the cap.)
                if high_conf and hit.get("source_type"):
                    it["source_type"] = hit["source_type"]
            else:
                counters["unmatched"] += 1
                it.setdefault("link", "")
    return counters


# ── Cross-run dedup ───────────────────────────────────────────────────────────
# Same article often surfaces over consecutive days in Google News. Track
# normalized title keys with their first-seen date and skip recent repeats.
_SEEN_PATH       = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "output", "seen_headlines.jsonl"
)
_SEEN_TTL_DAYS   = 1   # 2026-05-22: analyst chose 24h window. Items shipped in
                       # the last 24h are blocked from re-sending. Items older
                       # than 24h are free to re-appear (analyst preference —
                       # accepts occasional weekly repeat in exchange for
                       # less aggressive blocking).


def _norm_key(title: str) -> str:
    return re.sub(r"[^\w\s]", "", (title or "").lower()).strip()


def _norm_url_key(link: str) -> str:
    """Normalised URL key for dedup. Drops query+fragment, lowercases,
    strips www., trailing slash. So
      https://www.globant.com/news/abc/?utm_source=foo
    and
      https://globant.com/news/abc
    have the SAME key. Catches the same story re-published via different
    aggregators/utm-tracking URLs and via gnews redirect → decoded URL."""
    if not link:
        return ""
    try:
        from urllib.parse import urlparse, urlunparse
        p = urlparse(link.strip().lower())
        netloc = p.netloc[4:] if p.netloc.startswith("www.") else p.netloc
        path = p.path.rstrip("/")
        # Skip Google-search URLs (these are fallback URLs, not real articles)
        if "google.com/search" in p.netloc or "news.google.com" in p.netloc:
            return ""
        if not netloc or not path:
            return ""
        return netloc + path
    except Exception:
        return ""


def _load_seen() -> Tuple[Dict[str, str], Dict[str, str]]:
    """Return ({title_key: first_seen_date}, {url_key: first_seen_date}).
    Drops entries past TTL.
    """
    out_t: Dict[str, str] = {}
    out_u: Dict[str, str] = {}
    if not os.path.exists(_SEEN_PATH):
        return out_t, out_u
    cutoff = (datetime.now(LOCAL_TZ) - timedelta(days=_SEEN_TTL_DAYS)).strftime("%Y-%m-%d")
    try:
        with open(_SEEN_PATH, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                    key  = rec.get("k", "")
                    ukey = rec.get("u", "")
                    date = rec.get("d", "")
                    if not date or date < cutoff:
                        continue
                    if key:
                        if key not in out_t or date < out_t[key]:
                            out_t[key] = date
                    if ukey:
                        if ukey not in out_u or date < out_u[ukey]:
                            out_u[ukey] = date
                except json.JSONDecodeError:
                    pass
    except OSError:
        pass
    return out_t, out_u


def _save_seen(seen_t: Dict[str, str], seen_u: Dict[str, str]) -> None:
    """Rewrite the seen file with current valid entries (compacts the log).
    Schema per line: {"k": title_key, "u": url_key, "d": date}.
    """
    try:
        os.makedirs(os.path.dirname(_SEEN_PATH), exist_ok=True)
        # Build merged records: union of titles + URLs keyed by date pair
        # Simpler: write title records first, then url-only records for URLs
        # not represented by a title record (rare).
        written_urls = set()
        with open(_SEEN_PATH, "w", encoding="utf-8") as f:
            for k, d in seen_t.items():
                f.write(json.dumps({"k": k, "d": d}, ensure_ascii=False) + "\n")
            for u, d in seen_u.items():
                if u in written_urls:
                    continue
                f.write(json.dumps({"u": u, "d": d}, ensure_ascii=False) + "\n")
                written_urls.add(u)
    except OSError:
        pass


def _cross_run_dedupe(rows: List[Dict]) -> Tuple[List[Dict], int]:
    """FILTER ONLY: drop rows whose normalized title OR canonical URL was already
    seen (i.e. previously DELIVERED) in the last _SEEN_TTL_DAYS days. Does NOT
    persist anything — the seen-set is committed AFTER a successful send via
    commit_delivered_seen(). Previously this marked + saved every surviving row
    here, BEFORE curation/delivery, so a run that later failed, aborted, or
    produced an empty digest still recorded the news as 'seen' and suppressed it
    on the next run for 24h. (2026-06-24 fix — interacts with the auth-abort path.)"""
    seen_t, seen_u = _load_seen()
    kept: List[Dict] = []
    dropped = 0
    for row in rows:
        key  = _norm_key(row.get("title", ""))
        ukey = _norm_url_key(row.get("link", ""))
        # Drop if EITHER title or URL was previously DELIVERED
        if (key and key in seen_t) or (ukey and ukey in seen_u):
            dropped += 1
            continue
        kept.append(row)
    return kept, dropped


def commit_delivered_seen(report: Dict) -> int:
    """Persist the cross-run dedup memory AFTER a successful send, recording ONLY
    the items that actually shipped (the final report) — not every merged row.
    Companion to _cross_run_dedupe's read-only filter: a run that failed, aborted,
    or had an empty digest never reaches here, so it can't suppress undelivered
    news. (2026-06-24)"""
    seen_t, seen_u = _load_seen()
    today = datetime.now(LOCAL_TZ).strftime("%Y-%m-%d")
    n = 0
    for sec, items in report.items():
        if sec == "_raw" or not isinstance(items, list):
            continue
        for it in items:
            key  = _norm_key(it.get("headline", "") or it.get("title", ""))
            ukey = _norm_url_key(it.get("link", "") or "")
            if key and key not in seen_t:
                seen_t[key] = today
                n += 1
            if ukey and ukey not in seen_u:
                seen_u[ukey] = today
    _save_seen(seen_t, seen_u)
    return n


def _cross_dedupe(rows: List[Dict]) -> List[Dict]:
    """
    Deduplicate across the combined gnews + direct list.
    Normalises titles to lowercase stripped of punctuation (same logic as
    gnews_scraper.dedupe). Direct-source rows are kept over gnews duplicates
    because they carry a canonical URL and source name.
    """
    seen: set = set()
    out: List[Dict] = []
    # Stable sort so direct rows come first (source_type != "gnews")
    prioritised = sorted(rows, key=lambda r: 0 if r.get("source_type") != "gnews" else 1)
    for row in prioritised:
        title = (row.get("title") or "").strip()
        key   = re.sub(r"[^\w\s]", "", title.lower()).strip()
        if key and key not in seen:
            seen.add(key)
            out.append(row)
    return out


# ── Opinion / column filter (2026-06-02) ─────────────────────────────────────
# Opinion pieces and signed columns are not actionable for the clipping. Match
# "Opinião" only when it's a section label (next to a separator) so we don't
# catch "pesquisa de opinião"; plus opinion/column/blog URL paths.
_OPINION_TITLE_RE = re.compile(r"(?i)(?:^|[\-–—|]\s*)opini[ãa]o\s*[\-–—:|]")
_OPINION_URL_RE   = re.compile(r"(?i)/(?:opiniao|colunas?|blogs?)/")


def _is_opinion(row: Dict) -> bool:
    title = row.get("title", "") or ""
    link  = row.get("link", "") or ""
    return bool(_OPINION_TITLE_RE.search(title) or _OPINION_URL_RE.search(link))


def run(gnews_rows: List[Dict], direct_rows: List[Dict],
        apply_cross_run_dedup: bool = True) -> Tuple[List[Dict], str]:
    """
    Merge, assign sectors, sort by relevance, cap, and format.
    Returns: (merged_rows, claude_input_string)

    `apply_cross_run_dedup`: pass False in TEST_MODE so sample headlines
    aren't dropped (and don't pollute) the seen_headlines memory.
    """
    all_rows = gnews_rows + direct_rows

    # Drop empty titles
    all_rows = [r for r in all_rows if (r.get("title") or "").strip()]

    # Drop opinion / column pieces — not actionable for the clipping (2026-06-02)
    _op_before = len(all_rows)
    all_rows = [r for r in all_rows if not _is_opinion(r)]
    if _op_before - len(all_rows):
        print(f"  -> opinion filter: removed {_op_before - len(all_rows)}")

    # Cross-source dedup (same story from gnews AND a direct RSS feed)
    before = len(all_rows)
    all_rows = _cross_dedupe(all_rows)
    dropped = before - len(all_rows)
    if dropped:
        print(f"  -> cross-source dedup: removed {dropped} duplicates")

    # Cross-run dedup (story already seen in the last 3 days).
    # Skipped in TEST_MODE so iterative testing doesn't poison the dedup memory
    # with sample headlines, and doesn't get blocked by previous test runs.
    if apply_cross_run_dedup:
        all_rows, dropped_run = _cross_run_dedupe(all_rows)
        if dropped_run:
            print(f"  -> cross-run dedup: removed {dropped_run} headlines seen in last "
                  f"{_SEEN_TTL_DAYS} days")

    # Assign sectors
    assign_sectors(all_rows)

    # Score and sort: covered tickers first, then keyword matches, then general
    all_rows.sort(key=_relevance_score)

    # Cap per sector
    capped = cap_per_sector(all_rows)

    # Format for Claude
    claude_input = format_for_claude(capped)

    return capped, claude_input


if __name__ == "__main__":
    test = [
        {"title": "TOTVS conclui aquisição da Linx por R$7 bilhões",
         "source": "Valor Econômico", "keyword": "TOTVS", "edition_lang": "pt-BR",
         "source_type": "gnews", "link": "https://valor.globo.com/totvs"},
        {"title": "TCS is asking staff to use AI even if it hits revenues",
         "source": "Economic Times", "keyword": "TCS", "edition_lang": "en",
         "source_type": "gnews", "link": ""},
    ]
    rows, text = run(test, [])
    print(text)
