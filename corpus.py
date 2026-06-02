# corpus.py — Mine the daily corpus for patterns and themes
#
# What this does:
#   - Reads learning_log.jsonl (every run's curated items + notes)
#   - Reads vault/raw/clippings/*.md (the final outputs in Obsidian)
#   - Aggregates: ticker frequency, sector mix, source quality, themes, trends
#   - Surfaces the strongest signals: "curated but never noted" (potentially noise),
#     promotion rate per ticker, weekly theme drift, source-to-material ratio
#
# Used by:
#   - learn.py — included as a 6th source so the learn cycle gets analytical
#     summaries (not raw data lists). Lets Claude reason about what worked.
#   - CLI — inspect the corpus directly:
#         python corpus.py             # full summary text (last 30 days)
#         python corpus.py tickers     # ticker frequency table
#         python corpus.py themes      # significant terms over time
#         python corpus.py sources     # source-to-material ratio
#         python corpus.py notes       # what got promoted to notes
#         python corpus.py --days 60   # custom lookback

import json
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from config import LOCAL_TZ

# ── Paths ─────────────────────────────────────────────────────────────────────
_HERE              = os.path.dirname(os.path.abspath(__file__))
LOG_PATH           = os.path.join(_HERE, "output", "learning_log.jsonl")
VAULT_CLIPPINGS    = os.path.join(
    os.path.expanduser("~"), "OneDrive", "Documentos",
    "Obsidian Vault", "raw", "clippings",
)

DEFAULT_LOOKBACK_DAYS = 30

# Tokens we ignore when computing themes — stopwords across PT/ES/EN
_STOPWORDS = set("""
the a an of in to for on at by with from is are was were be been being has have
had do does did and or but if not no yes new latest news today this that these
those will would could should may might must can com br pt es en e o a os as
um uma uns umas para por com que se de da do das dos no na nos nas em mais
del la el las los una uno unos unas para por con que se de del lo en mas
y o é são foram era em está estão tem teve tinha será seria pode poderia
sobre como mais menos muito muita pouco pouca muitos muitas pouquinho
to be on of in at for with from up down about under over after before
sao tem teve tera havia ha hao through across between
""".split())

# Tokens we boost as "thematic" — capitalized terms, regulators, key concepts
_THEMATIC_PATTERNS = [
    re.compile(r"\b[A-Z][A-Z0-9]{1,5}\b"),                     # acronyms (AMX, IFT, ANATEL)
    re.compile(r"\b\d+\s*[GMK]Hz\b", re.IGNORECASE),           # spectrum bands (700 MHz, 5G)
    re.compile(r"\b5G\b|\b4G\b|\b3G\b|\bFTTH\b|\bMVNO\b"),     # tech labels
]

# Regulators / proper nouns commonly written in title case (not all-caps)
# but are real themes worth tracking
_NAMED_THEMES = {
    "Anatel", "Cofeces", "IFT", "CRT", "CRC", "Subtel", "Osiptel",
    "Enacom", "Conatel", "ICT", "Promtel", "Cofetel", "Senacon",
    "ANP", "BAIT", "OMV", "OMVs",
}

# Generic business titles to suppress — appear constantly, not real themes
_THEME_BLOCKLIST = {
    "CEO", "CTO", "CFO", "COO", "CIO", "CMO", "CHRO", "CRO",
    "VP", "SVP", "EVP", "AVP",
    "USD", "EUR", "BRL", "MXN", "CLP", "COP", "GBP", "JPY", "CNY", "ARS",
    "INC", "LLC", "LTD", "SA", "NV", "CO", "JR", "SR",
    "Q1", "Q2", "Q3", "Q4", "FY", "YR", "MO", "WK",
    "NYSE", "NASDAQ", "B3", "BMV", "BVL",
    "PR", "ESG", "AI", "IT", "ML", "ER", "OK", "USA", "EU", "UK",
    "BRT", "GMT", "PST", "EST", "UTC", "PT", "ES", "EN",
}


# ── Corpus loaders ────────────────────────────────────────────────────────────
def _load_log_entries(days: int = DEFAULT_LOOKBACK_DAYS) -> List[Dict]:
    """Load learning_log.jsonl entries within the lookback window."""
    if not os.path.exists(LOG_PATH):
        return []
    cutoff = (datetime.now(LOCAL_TZ) - timedelta(days=days)).strftime("%Y-%m-%d")
    out: List[Dict] = []
    try:
        with open(LOG_PATH, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    e = json.loads(line)
                    if e.get("date", "") >= cutoff:
                        out.append(e)
                except json.JSONDecodeError:
                    pass
    except OSError:
        pass
    return out


def _load_clipping_files(days: int = DEFAULT_LOOKBACK_DAYS) -> List[str]:
    """List vault clipping markdown files within the lookback window."""
    if not os.path.isdir(VAULT_CLIPPINGS):
        return []
    cutoff = (datetime.now(LOCAL_TZ) - timedelta(days=days)).strftime("%Y-%m-%d")
    files = []
    try:
        for fname in os.listdir(VAULT_CLIPPINGS):
            if fname.endswith(".md") and fname[:10] >= cutoff:
                files.append(os.path.join(VAULT_CLIPPINGS, fname))
    except OSError:
        pass
    return sorted(files)


# ── Theme extraction ──────────────────────────────────────────────────────────
def _extract_themes(headline: str) -> List[str]:
    """
    Pull thematic tokens from a headline.
    Catches: all-caps acronyms (AMX, IFT, 5G), spectrum bands (700 MHz),
    tech labels (FTTH, MVNO), and named regulators (Anatel, IFT, Subtel).
    Filters: stopwords + generic business titles (CEO/CTO/Q1/USD/etc.).
    """
    found: List[str] = []

    # 1) Pattern-based extraction (acronyms, spectrum, tech)
    for pat in _THEMATIC_PATTERNS:
        for m in pat.findall(headline):
            tok = m.upper().strip()
            if (tok and len(tok) >= 2
                    and tok.lower() not in _STOPWORDS
                    and tok not in _THEME_BLOCKLIST):
                found.append(tok)

    # 2) Named-theme matching (Anatel-style title-case proper nouns)
    for theme in _NAMED_THEMES:
        if re.search(rf"\b{re.escape(theme)}\b", headline, re.IGNORECASE):
            found.append(theme.upper())

    return found


def _extract_note_ticker(note_text: str) -> str:
    """Extract the ticker from a note's headline (📍 TICKER: ...)."""
    m = re.search(r"📍\s*([A-Z][A-Z0-9/\-\.]*)", note_text)
    return m.group(1) if m else ""


# ── The core aggregation ──────────────────────────────────────────────────────
def summarize(days: int = DEFAULT_LOOKBACK_DAYS) -> Dict:
    """
    Aggregate the past `days` of pipeline activity into a single summary dict.
    This is the analytical view of the corpus — what was scraped, curated,
    promoted to notes, and which themes/sources/tickers dominated.
    """
    entries = _load_log_entries(days)

    ticker_curated: Counter   = Counter()
    sector_curated: Counter   = Counter()
    source_curated: Counter   = Counter()
    ticker_noted:   Counter   = Counter()
    theme_curated:  Counter   = Counter()
    weekly_tickers: Dict      = defaultdict(Counter)
    weekly_themes:  Dict      = defaultdict(Counter)

    headlines_by_ticker: Dict = defaultdict(list)

    for e in entries:
        date = e.get("date", "")
        week = date[:7] if date else "unknown"  # YYYY-MM bucket

        for item in e.get("curated_items", []):
            t   = item.get("ticker", "?") or "?"
            s   = item.get("sector", "?") or "?"
            src = item.get("source", "") or ""
            hdl = item.get("headline", "") or ""

            ticker_curated[t] += 1
            sector_curated[s] += 1
            if src:
                source_curated[src] += 1
            weekly_tickers[week][t] += 1

            for theme in _extract_themes(hdl):
                # Don't double-count tickers as themes
                if theme != t:
                    theme_curated[theme] += 1
                    weekly_themes[week][theme] += 1

            if len(headlines_by_ticker[t]) < 5:
                headlines_by_ticker[t].append(hdl)

        for note in e.get("notes_written", []):
            t = _extract_note_ticker(note)
            if t:
                # Notes can carry multi-ticker tags like AMX/TEF-BZ; count each
                for sub in t.split("/"):
                    sub = sub.strip()
                    if sub:
                        ticker_noted[sub] += 1

    # Promotion rate: how often a curated ticker actually became a full note
    promotion_rate: Dict[str, float] = {}
    for t, count in ticker_curated.most_common(20):
        notes = ticker_noted.get(t, 0)
        promotion_rate[t] = round(notes / count, 3) if count else 0.0

    # Tickers curated 3+ times but never promoted to a note
    curated_but_never_noted = [
        t for t, n in ticker_curated.most_common()
        if n >= 3 and t not in ticker_noted and t not in ("?", "Sector")
    ]

    # Source-to-material ratio: sources that contributed the most curated items
    # (proxy for source quality — what the curator actually selects)
    top_sources = source_curated.most_common(15)

    return {
        "window_days":            days,
        "total_runs":             len(entries),
        "total_curated":          sum(ticker_curated.values()),
        "total_notes":            sum(ticker_noted.values()),
        "ticker_curated":         dict(ticker_curated.most_common(25)),
        "ticker_noted":           dict(ticker_noted.most_common(20)),
        "sector_curated":         dict(sector_curated.most_common()),
        "source_curated":         dict(top_sources),
        "theme_curated":          dict(theme_curated.most_common(25)),
        "promotion_rate":         promotion_rate,
        "curated_but_never_noted": curated_but_never_noted[:15],
        "headlines_by_ticker":    dict(headlines_by_ticker),
        "weekly_tickers":         {k: dict(v.most_common(5)) for k, v in sorted(weekly_tickers.items())},
        "weekly_themes":          {k: dict(v.most_common(5)) for k, v in sorted(weekly_themes.items())},
    }


# ── Formatted text outputs ────────────────────────────────────────────────────
def build_summary_text(days: int = DEFAULT_LOOKBACK_DAYS) -> str:
    """
    Format the corpus summary for inclusion in the learn cycle prompt.
    Designed so Claude can reason about WHAT WORKED, not just WHAT HAPPENED.
    """
    s = summarize(days)
    if s["total_runs"] == 0:
        return "(no past runs to analyze yet — corpus is empty)"

    p: List[str] = []
    p.append(f"=== CORPUS ANALYSIS (last {days} days, {s['total_runs']} runs) ===")
    p.append(f"Curated items: {s['total_curated']:,} | Notes written: {s['total_notes']}")

    p.append("\n--- Top 10 most curated tickers ---")
    for i, (t, n) in enumerate(list(s["ticker_curated"].items())[:10]):
        rate = s["promotion_rate"].get(t, 0.0)
        rate_str = f"  [{rate*100:.0f}% promoted to note]" if rate > 0 else "  [never noted]"
        p.append(f"  {t:<14} {n:>3}x{rate_str}")

    p.append("\n--- Tickers promoted to full notes ---")
    if s["ticker_noted"]:
        for t, n in s["ticker_noted"].items():
            p.append(f"  {t}: {n} note(s)")
    else:
        p.append("  (no notes written in window)")

    if s["curated_but_never_noted"]:
        p.append("\n--- Curated 3+ times but never promoted to a note ---")
        p.append("    (signal: either too noisy to deserve a note, or genuinely")
        p.append("     material color that the note selector is missing)")
        for t in s["curated_but_never_noted"]:
            sample = s["headlines_by_ticker"].get(t, [])
            sample_txt = " | ".join(h[:70] for h in sample[:2])
            p.append(f"  {t}: e.g. {sample_txt}")

    p.append("\n--- Sector mix ---")
    for sec, n in s["sector_curated"].items():
        p.append(f"  {sec}: {n}")

    p.append("\n--- Top sources contributing curated items ---")
    for src, n in list(s["source_curated"].items())[:10]:
        p.append(f"  {src}: {n}")

    if s["theme_curated"]:
        p.append("\n--- Themes (acronyms, regulators, tech labels) ---")
        for theme, n in list(s["theme_curated"].items())[:15]:
            p.append(f"  {theme}: {n}x")

    if s["weekly_tickers"]:
        p.append("\n--- Monthly ticker trend (top 5 per month) ---")
        for month, tickers in s["weekly_tickers"].items():
            top = ", ".join(f"{t}:{n}" for t, n in tickers.items())
            p.append(f"  {month}: {top}")

    return "\n".join(p)


# ── CLI for direct inspection ────────────────────────────────────────────────
def _print_tickers(s: Dict) -> None:
    print(f"\nTicker activity (last {s['window_days']} days):\n")
    print(f"  {'Ticker':<14} {'Curated':>8} {'Noted':>6} {'Promo%':>7}")
    print(f"  {'-'*14} {'-'*8} {'-'*6} {'-'*7}")
    for t, n in s["ticker_curated"].items():
        notes = s["ticker_noted"].get(t, 0)
        rate  = s["promotion_rate"].get(t, 0.0)
        print(f"  {t:<14} {n:>8} {notes:>6} {rate*100:>6.0f}%")


def _print_themes(s: Dict) -> None:
    print(f"\nThemes (last {s['window_days']} days):\n")
    for theme, n in s["theme_curated"].items():
        print(f"  {theme:<14} {n:>4}x")
    print(f"\nMonthly drift:\n")
    for month, themes in s["weekly_themes"].items():
        print(f"  {month}: {', '.join(f'{t}:{n}' for t,n in themes.items())}")


def _print_sources(s: Dict) -> None:
    print(f"\nTop sources (last {s['window_days']} days):\n")
    for src, n in s["source_curated"].items():
        print(f"  {src:<35} {n:>4}x")


def _print_notes(s: Dict) -> None:
    print(f"\nNotes promoted (last {s['window_days']} days):\n")
    if not s["ticker_noted"]:
        print("  (no notes written in window)")
        return
    for t, n in s["ticker_noted"].items():
        curated = s["ticker_curated"].get(t, 0)
        rate = s["promotion_rate"].get(t, 0.0)
        print(f"  {t:<14}  {n} note(s) from {curated} curated items  ({rate*100:.0f}%)")
    print(f"\nCurated frequently but never noted:")
    for t in s["curated_but_never_noted"]:
        print(f"  {t}: {s['ticker_curated'].get(t, 0)}x curated")


def main() -> None:
    days = DEFAULT_LOOKBACK_DAYS
    if "--days" in sys.argv:
        try:
            days = int(sys.argv[sys.argv.index("--days") + 1])
        except (ValueError, IndexError):
            pass

    cmd = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else "summary"
    s = summarize(days)

    if s["total_runs"] == 0:
        print(f"\nNo runs in the last {days} days yet. Run the pipeline a few times first.")
        return

    if cmd == "tickers":
        _print_tickers(s)
    elif cmd == "themes":
        _print_themes(s)
    elif cmd == "sources":
        _print_sources(s)
    elif cmd == "notes":
        _print_notes(s)
    else:
        print(build_summary_text(days))


if __name__ == "__main__":
    main()
