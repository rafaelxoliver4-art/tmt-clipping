# observer_corpus.py — Parse Rafael's published notes from
# TMT Online Observer Data.docx into structured data, then expose it as the
# HIGHEST-WEIGHT learning signal in the system.
#
# WHY THIS IS THE STRONGEST SIGNAL:
#   The Observer file contains every note Rafael actually published. It's the
#   ground truth of "what was material enough to write about." Anything we
#   curate that he writes about: confirmed material. Anything he writes about
#   that we miss: a curation gap.
#
# WHAT IT DOES:
#   1. Parses the .docx into individual notes (split on 📍 ticker markers)
#   2. Extracts ticker(s), headline, "What happened" body, "UBS's take",
#      and the directional signal (Positive / Negative / Neutral / etc.)
#   3. Caches the parsed result keyed on file mtime — only reparses when
#      Rafael edits the file
#   4. Provides query API for downstream:
#        - Ticker frequency (which names get notes)
#        - Recent notes (for style examples in the note writer prompt)
#        - Signal vocabulary (which signals he uses for which situations)
#
# WHO USES IT:
#   - topics.py:  reinforce_from_observer() boosts topics by +10 per Rafael note
#   - claude_reasoning.py:  injects 2-3 recent real notes as style anchors
#   - learn.py:  feeds structured statistics to the deep learn cycle

import json
import os
import re
import sys
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Tuple

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from claude_data_reader import read_docx_text, CLAUDE_DATA_DIR

# ── Paths ─────────────────────────────────────────────────────────────────────
OBSERVER_FILENAME = "TMT Online Observer Data.docx"
OBSERVER_PATH     = os.path.join(CLAUDE_DATA_DIR, OBSERVER_FILENAME)

_HERE       = os.path.dirname(os.path.abspath(__file__))
CACHE_PATH  = os.path.join(_HERE, "output", "observer_corpus_cache.json")

# ── Note-format markers (from tmt-report-format.md spec) ──────────────────────
_NOTE_START      = "📍"
_TAKE_MARKER     = "🔎"
_WHAT_HAPPENED   = "What happened"
_TAKE_HEADER     = "UBS's take"

# Directional signal vocabulary (from spec) — captured in priority order so
# "Slightly positive" matches before "Positive"
_SIGNAL_PHRASES = [
    "Doesn't move the needle",
    "Mixed but skewed positive",
    "Mixed but skewed negative",
    "Mixed read",
    "Slightly positive",
    "Slightly negative",
    "Positive",
    "Negative",
    "Neutral",
]


# ── Cache helpers ─────────────────────────────────────────────────────────────
def _file_signature(path: str) -> str:
    """Returns 'mtime|size' — cheap signature to detect file changes."""
    try:
        st = os.stat(path)
        return f"{st.st_mtime}|{st.st_size}"
    except OSError:
        return ""


def _load_cache() -> Optional[Dict]:
    if not os.path.exists(CACHE_PATH):
        return None
    try:
        with open(CACHE_PATH, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return None


def _save_cache(data: Dict) -> None:
    try:
        os.makedirs(os.path.dirname(CACHE_PATH), exist_ok=True)
        with open(CACHE_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except OSError as e:
        print(f"  [WARN] Could not write observer cache: {e}")


# ── Note extraction ───────────────────────────────────────────────────────────
def _split_notes(full_text: str) -> List[str]:
    """
    Split the document into individual notes. Each note starts with 📍
    followed by a ticker and colon. Returns the raw text of each note.
    """
    if _NOTE_START not in full_text:
        return []
    chunks = full_text.split(_NOTE_START)
    # First chunk is anything before the first 📍 (file header) — discard
    return [_NOTE_START + c.strip() for c in chunks[1:] if c.strip()]


def _extract_ticker(note_text: str) -> str:
    """
    From a line like '📍 GLOB: AI positioning is credible...' extract 'GLOB'.
    Multi-ticker support: '📍 AMX/TEF-BZ/TIM: ...' -> 'AMX/TEF-BZ/TIM'
    Bracketed forms like '📍 [AMX]:' also handled.
    """
    first_line = note_text.lstrip(_NOTE_START).strip().splitlines()[0] if note_text else ""
    # Match: optional brackets + ticker chars + colon
    m = re.match(r"^\s*\[?([A-Z][A-Z0-9/\-\.&]{0,40}?)\]?\s*:", first_line)
    return m.group(1).strip() if m else ""


def _extract_headline(note_text: str) -> str:
    """The headline is everything after 'TICKER:' on the first line."""
    first_line = note_text.lstrip(_NOTE_START).strip().splitlines()[0] if note_text else ""
    if ":" in first_line:
        return first_line.split(":", 1)[1].strip()
    return first_line.strip()


def _extract_take(note_text: str) -> str:
    """
    Pull out the 'UBS's take' section. Various forms:
      🔎 UBS's take: ...
      UBS's take: ...
      🔎 ...
    """
    # Try 🔎 marker first
    if _TAKE_MARKER in note_text:
        after = note_text.split(_TAKE_MARKER, 1)[1]
    elif _TAKE_HEADER in note_text:
        after = note_text.split(_TAKE_HEADER, 1)[1]
    else:
        return ""
    # Take everything until the next 📍 (next note) or end
    if _NOTE_START in after:
        after = after.split(_NOTE_START)[0]
    return after.lstrip(":").strip()


def _extract_what_happened(note_text: str) -> str:
    """Pull the 'What happened:' section."""
    if _WHAT_HAPPENED not in note_text:
        return ""
    after = note_text.split(_WHAT_HAPPENED, 1)[1]
    # Stop at the take marker or next note
    for stop in (_TAKE_MARKER, _TAKE_HEADER, _NOTE_START):
        if stop in after:
            after = after.split(stop)[0]
    return after.lstrip(":").strip()


def _extract_signal(take_text: str) -> str:
    """Find which directional signal phrase Rafael used in the take."""
    if not take_text:
        return ""
    take_lower = take_text.lower()
    for phrase in _SIGNAL_PHRASES:
        if phrase.lower() in take_lower:
            return phrase
    return ""


def _parse_one_note(raw_text: str, position: int) -> Dict:
    ticker        = _extract_ticker(raw_text)
    headline      = _extract_headline(raw_text)
    what_happened = _extract_what_happened(raw_text)
    take          = _extract_take(raw_text)
    signal        = _extract_signal(take)
    return {
        "position":        position,    # ordering in file (newer notes = later)
        "ticker":          ticker,
        "tickers_split":   [t for t in ticker.split("/") if t.strip()],
        "headline":        headline[:300],
        "what_happened":   what_happened[:1500],
        "take":            take[:1500],
        "signal":          signal,
        "char_count":      len(raw_text),
    }


# ── Public API ────────────────────────────────────────────────────────────────
def parse_observer_doc(force_reparse: bool = False) -> Dict:
    """
    Parse the Observer file into structured notes. Returns:
      {
        "file_signature": "mtime|size",
        "parsed_at": iso_timestamp,
        "total_notes": int,
        "notes": [ {position, ticker, headline, ...}, ... ],
        "ticker_frequency": {TICKER: count},
        "signal_distribution": {Signal: count},
      }

    Cached on file mtime+size — only reparses when the .docx actually changes.
    """
    sig = _file_signature(OBSERVER_PATH)
    if not sig:
        return {"error": f"file not found: {OBSERVER_PATH}", "total_notes": 0,
                "notes": [], "ticker_frequency": {}, "signal_distribution": {}}

    if not force_reparse:
        cache = _load_cache()
        if cache and cache.get("file_signature") == sig:
            return cache  # cache hit — file unchanged

    # Cache miss — reparse
    full_text = read_docx_text(OBSERVER_PATH)
    if not full_text:
        return {"error": "could not read file", "total_notes": 0, "notes": [],
                "ticker_frequency": {}, "signal_distribution": {}}

    raw_notes = _split_notes(full_text)
    parsed: List[Dict] = []
    for i, raw in enumerate(raw_notes):
        note = _parse_one_note(raw, i)
        if note["ticker"]:  # skip noise / non-note 📍 occurrences
            parsed.append(note)

    # Aggregate stats
    ticker_freq: Dict[str, int] = {}
    signal_dist: Dict[str, int] = {}
    for note in parsed:
        # Count each ticker in multi-ticker tags separately
        for t in note["tickers_split"]:
            ticker_freq[t] = ticker_freq.get(t, 0) + 1
        if note["signal"]:
            signal_dist[note["signal"]] = signal_dist.get(note["signal"], 0) + 1

    # Sort dicts by frequency desc for stable downstream use
    ticker_freq = dict(sorted(ticker_freq.items(), key=lambda x: -x[1]))
    signal_dist = dict(sorted(signal_dist.items(), key=lambda x: -x[1]))

    out = {
        "file_signature":     sig,
        "parsed_at":          datetime.now().isoformat(),
        "total_notes":        len(parsed),
        "notes":              parsed,
        "ticker_frequency":   ticker_freq,
        "signal_distribution": signal_dist,
    }
    _save_cache(out)
    return out


def get_recent_notes(n: int = 5) -> List[Dict]:
    """
    Return the last N notes (by file order — assuming newer notes are
    appended at the end). Used to give Claude real style examples when
    writing a new note.
    """
    data = parse_observer_doc()
    if not data.get("notes"):
        return []
    return data["notes"][-n:]


def get_ticker_frequency() -> Dict[str, int]:
    """Map each ticker to how many notes Rafael has written about it."""
    return parse_observer_doc().get("ticker_frequency", {})


def get_signal_distribution() -> Dict[str, int]:
    """Distribution of directional signals Rafael uses."""
    return parse_observer_doc().get("signal_distribution", {})


def find_underrepresented_tickers(min_notes: int = 3,
                                  current_context: str = "") -> List[Tuple[str, int]]:
    """
    Tickers Rafael has written about ≥ min_notes times that are NOT
    explicitly mentioned in the current ANALYST_CONTEXT. These are
    blind spots in the curator.
    """
    freq = get_ticker_frequency()
    out: List[Tuple[str, int]] = []
    for ticker, count in freq.items():
        if count < min_notes:
            continue
        if not current_context or ticker.upper() not in current_context.upper():
            out.append((ticker, count))
    return out


# ── Style block builder for the note writer ───────────────────────────────────
def build_style_examples(n: int = 3, max_chars_per_note: int = 800) -> str:
    """
    Build a "real recent notes" block to inject into the note writer's prompt.
    These are Rafael's actual published notes — style ground truth.
    """
    notes = get_recent_notes(n)
    if not notes:
        return ""

    parts = [
        "### REAL RECENT NOTES (style ground truth — Rafael's actual published work)",
        "",
        "Match this voice, structure, and density. These are the most recent notes from",
        "the published Observer. Note how facts are attributed, takes are hedged, and",
        "signals are explicit.",
        "",
    ]
    for i, note in enumerate(notes, 1):
        ticker = note.get("ticker", "?")
        head   = note.get("headline", "")
        what   = note.get("what_happened", "")[:max_chars_per_note // 2]
        take   = note.get("take", "")[:max_chars_per_note // 2]
        sig    = note.get("signal", "")

        block = f"--- Example {i} | 📍 {ticker}: {head} ---\n"
        if what:
            block += f"What happened:\n{what}\n\n"
        if take:
            block += f"🔎 UBS's take:\n{take}"
        if sig:
            block += f"\n[Signal used: {sig}]"
        parts.append(block)

    return "\n\n".join(parts)


# ── Stats block for the learn cycle ───────────────────────────────────────────
def build_observer_stats_block() -> str:
    """
    Build a structured stats block for the deep learn cycle (every 10 runs).
    Surfaces what Rafael actually writes about — the ground-truth signal of
    materiality.
    """
    data = parse_observer_doc()
    if data.get("total_notes", 0) == 0:
        return "(no Observer notes parsed yet)"

    parts = [
        f"=== OBSERVER PUBLISHED NOTES ANALYSIS ({data['total_notes']} notes parsed) ===",
        "",
        "This is what Rafael actually wrote. Tickers below are MATERIAL by",
        "definition — the curator should never miss them.",
        "",
        "--- Top 20 most-noted tickers (Rafael's revealed priorities) ---",
    ]
    for ticker, count in list(data["ticker_frequency"].items())[:20]:
        parts.append(f"  {ticker:<14} {count} note(s)")

    if data["signal_distribution"]:
        parts.append("")
        parts.append("--- Directional signal usage (Rafael's calibration) ---")
        for sig, count in data["signal_distribution"].items():
            parts.append(f"  {sig:<32} {count}")

    return "\n".join(parts)


# ── CLI ───────────────────────────────────────────────────────────────────────
def main() -> None:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "summary"

    if cmd == "parse":
        data = parse_observer_doc(force_reparse=True)
        print(f"Parsed {data['total_notes']} notes")
        print(f"Cached to: {CACHE_PATH}")

    elif cmd == "tickers":
        freq = get_ticker_frequency()
        print(f"\n{len(freq)} unique tickers, top 30:\n")
        for t, n in list(freq.items())[:30]:
            print(f"  {t:<16} {n} note(s)")

    elif cmd == "signals":
        sigs = get_signal_distribution()
        print(f"\nSignal vocabulary distribution:\n")
        for s, n in sigs.items():
            print(f"  {s:<32} {n}")

    elif cmd == "recent":
        n = int(sys.argv[2]) if len(sys.argv) > 2 else 3
        notes = get_recent_notes(n)
        print(f"\nLast {len(notes)} notes:\n")
        for note in notes:
            print(f"📍 {note['ticker']}: {note['headline']}")
            if note.get("signal"):
                print(f"   [{note['signal']}]")
            print(f"   ({note['char_count']} chars)\n")

    elif cmd == "style":
        print(build_style_examples(3))

    elif cmd == "stats":
        print(build_observer_stats_block())

    elif cmd == "gaps":
        from learn import _read_current_context
        ctx = _read_current_context()
        gaps = find_underrepresented_tickers(min_notes=3, current_context=ctx)
        if not gaps:
            print("\nNo blind spots — every frequently-noted ticker is in ANALYST_CONTEXT.")
        else:
            print(f"\nTickers noted 3+ times but missing from ANALYST_CONTEXT:\n")
            for t, n in gaps:
                print(f"  {t:<14} {n} note(s)")

    else:
        # Default summary
        data = parse_observer_doc()
        print(f"\nObserver file: {OBSERVER_PATH}")
        print(f"  Parsed notes: {data['total_notes']}")
        print(f"  Unique tickers: {len(data.get('ticker_frequency', {}))}")
        print(f"  Signal phrases used: {len(data.get('signal_distribution', {}))}")
        print(f"  Cache: {CACHE_PATH}")
        print(f"\nCommands: parse | tickers | signals | recent [N] | style | stats | gaps")


if __name__ == "__main__":
    main()
