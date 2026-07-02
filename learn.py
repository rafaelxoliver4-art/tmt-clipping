# learn.py — Continuous learning: analyze all sources and improve wiki_context.py
#
# Sources (in priority order):
#   1. NEWS_WRITER_CONTEXT.md       — master editorial framework (Obsidian wiki)
#   2. output/learning_log.jsonl    — what the pipeline curated in each daily run
#   3. Obsidian vault conversations — Rafael's real News Writer sessions with Claude
#      (raw/conversations/*.md — where note triage, writing, and feedback happen)
#   4. Claude Code conversation history — sessions from this project's .claude dir
#
# Called automatically every 10 pipeline runs (from run_daily.py --auto-learn).
# Can also be run manually:
#   python learn.py                  # interactive, shows diff, asks to apply
#   python learn.py --auto           # apply without prompting
#   python learn.py --days 60        # look back 60 days (default 30)
#   python learn.py --dry-run        # show changes, don't modify any file

import json
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from email_sender import _load_env as _load_dotenv
_load_dotenv()

from config import LOCAL_TZ
from claude_reasoning import _call_claude_cli, _call_claude_api, _extract_text
from corpus import build_summary_text as build_corpus_summary
from watchlist import save_auto_suggestions, load_manual_watchlist
from claude_data_reader import load_reference_docs
from observer_corpus import build_observer_stats_block, find_underrepresented_tickers

# ── Paths ─────────────────────────────────────────────────────────────────────
_HERE             = os.path.dirname(os.path.abspath(__file__))
LEARNING_LOG_PATH = os.path.join(_HERE, "output", "learning_log.jsonl")
WIKI_CONTEXT_PATH = os.path.join(_HERE, "wiki_context.py")

# News Writer project — Obsidian vault
_VAULT_ROOT       = r"C:\Users\Rafael\OneDrive\Documentos\Obsidian Vault"
NEWS_WRITER_CTX   = os.path.join(_VAULT_ROOT, "wiki", "NEWS_WRITER_CONTEXT.md")
VAULT_CONV_DIR    = os.path.join(_VAULT_ROOT, "raw", "conversations")

# Claude Code conversation history — per-project JSONL files
_CLAUDE_PROJECTS  = os.path.join(os.path.expanduser("~"), ".claude", "projects")
_PROJECT_DIRS = [
    os.path.join(_CLAUDE_PROJECTS,
                 "C--Users-Rafael-OneDrive--rea-de-Trabalho-Python-News-Scraper-Claude"),
    os.path.join(_CLAUDE_PROJECTS,
                 "C--Users-Rafael-OneDrive--rea-de-Trabalho-Claude-Data-Claude-Code"),
    os.path.join(_CLAUDE_PROJECTS,
                 "c--Users-Rafael-OneDrive--rea-de-Trabalho-Python"),
]

CLIPPING_EXAMPLES_PATH = os.path.join(_HERE, "examples", "clipping_examples.txt")

DEFAULT_LOOKBACK_DAYS  = 30
MAX_VAULT_CONV_FILES   = 20    # most recent N .md conversation files to read
MAX_CLAUDE_CONV_FILES  = 15    # most recent N Claude Code JSONL sessions
MAX_CHARS_PER_CONV     = 3000  # chars per file to avoid prompt bloat


# ── Source 5: Real clipping examples (editorial ground truth) ─────────────────
def load_clipping_examples() -> str:
    """
    Load past real TMT News Clipping examples provided by Rafael.
    These are editorial ground truth: correct ticker tags, multi-ticker format,
    section structure, and materiality bar — not for pattern-matching future news.
    """
    if not os.path.exists(CLIPPING_EXAMPLES_PATH):
        return "(no clipping examples file found)"
    try:
        with open(CLIPPING_EXAMPLES_PATH, encoding="utf-8", errors="replace") as f:
            content = f.read()
        # Cap to avoid prompt bloat — first 8000 chars covers most examples
        if len(content) > 8000:
            content = content[:8000] + "\n…[truncated — see examples/clipping_examples.txt]"
        return f"=== REAL CLIPPING EXAMPLES (editorial ground truth) ===\n{content}"
    except OSError:
        return "(could not read clipping examples)"


# ── System prompt ──────────────────────────────────────────────────────────────
LEARN_SYSTEM = """You are a senior LatAm TMT equity research analyst helping maintain an
automated news curator for UBS LatAm TMT equity research.

The curator uses ANALYST_CONTEXT (in wiki_context.py) to guide two tasks:
  1. Curating a daily news clipping — which stories are material and to which covered ticker?
  2. Writing short analytical notes — what is the investment angle and directional signal?

You receive eight inputs:
  A. Current ANALYST_CONTEXT (what the curator knows today)
  B. Pipeline run log — which tickers/topics were curated most, which notes were written
  C. News Writer session excerpts — Rafael's real editorial triage decisions and note-writing
     feedback from the Obsidian vault conversations
  D. Claude Code session excerpts — conversations in this project (code + reasoning sessions)
  E. Real clipping examples — actual past TMT News Clippings produced by Rafael.
     Use E to understand: correct ticker aliases (TEF-BZ not VIVT3, TIM not TIMS3,
     ACN/COG/INFY for peers), multi-ticker format (AMX/TEF-BZ/TIM, GLOB/CINT),
     Sell-side section structure, and materiality bar. Do NOT use E to predict future news.
  F. Corpus analysis — analytical view of the pipeline's own past outputs:
     ticker frequencies, sector mix, source quality, theme drift over time, AND
     critically the "promotion rate" (how often a curated ticker became a full
     note) and "curated but never noted" (potential noise OR potential blind
     spots). Use F to spot patterns the curator should learn from — e.g., if a
     ticker shows up 20x but never becomes a note, the materiality bar in A
     might be calibrated wrong for it.
  G. Claude Data reference docs — Rafael's source-of-truth files (TMT Online
     Observer Data, Conference Call Transcripts, Crowding Score Data, prompt
     templates, Anatel reports). LIVE-READ every cycle; updates Rafael makes
     to these files propagate automatically. Use G to cross-check coverage
     universe, quoted call commentary, positioning data, and the editorial
     prompt framework against what's currently in A.
  H. Observer published-notes ANALYSIS — STRUCTURED extraction of every note
     Rafael has actually published. Includes (i) ticker frequency: which names
     get notes most often (revealed materiality), (ii) directional signal usage
     (calibration of his Positive/Negative/Mixed vocabulary), and (iii) any
     blind-spot tickers Rafael writes about repeatedly that aren't in A. This
     is the STRONGEST signal in the set — it's literally what Rafael decided
     was worth writing about. If a ticker has 10+ Observer notes but no
     dedicated section in A, fix that.

Your task: find concrete refinements to ANALYST_CONTEXT that are clearly supported by C, D, E, F, G, and H.

Look for:
- Tickers, companies, or topics Rafael engages with repeatedly but aren't in the context
- Triage decisions: stories he consistently picks OR rejects — not yet codified as rules
- Read-across logic he uses repeatedly ("this story hits TOTVS because...")
- New "active running stories" that emerged in recent sessions
- Writing style feedback he gives frequently ("more concise", "don't restate", etc.)
- Triggers refined by what actually showed up as material vs. noise
- Clipping-format patterns: how are headlines grouped, which are "Other News" vs. full note

Rules:
- Preserve ALL existing content — only add or refine, never delete
- Only add things clearly evidenced in the sessions, not generic guesses
- 2–6 well-targeted additions beat 20 vague ones
- Don't change structure or section headers

OUTPUT: Return ONLY the updated ANALYST_CONTEXT as a plain string — everything that would
appear between the triple quotes. No Python syntax, no fences, no preamble.
Start directly with "## UBS LatAm TMT..." (the first line of the current content)."""


# ── Source 1: Full Obsidian wiki/ folder ──────────────────────────────────────
# Editorial pages we want to learn from (in priority order). Anything else in
# wiki/ is included opportunistically up to a total budget.
_WIKI_DIR              = os.path.join(_VAULT_ROOT, "wiki")
_WIKI_PRIORITY_PAGES   = [
    "NEWS_WRITER_CONTEXT.md",                      # master editorial framework
    "tmt-report-format.md",                        # exact format spec (critical)
    "news-writing-process.md",                     # full editorial workflow
    "news-writing-telecom-methodology.md",         # sector-specific guidance
    "news-writing-ai-methodology.md",              # AI/tech writing patterns
    "tmt-online-observer-prompt-framework.md",    # system prompt definition
    "latam-tmt-coverage-universe.md",              # coverage definition
    "latam-telecom-operators.md",                  # telecom operator detail
    "latam-it-services-companies.md",              # IT services detail
    "ai-disruption-saas-software.md",              # SaaS read-across logic
    "ai-disruption-enterprise-software.md",       # ERP read-across logic
    "anatel-portability-analysis.md",              # methodology
    "latam-tmt-crowding-scores.md",                # positioning context
    "tmt-online-observer.md",                      # main workflow doc
]
_MAX_WIKI_TOTAL_CHARS  = 18000   # total budget across all wiki pages
_MAX_WIKI_PAGE_CHARS   = 2400    # per-page cap


def load_news_writer_context() -> str:
    """
    Load the FULL editorial wiki — not just NEWS_WRITER_CONTEXT.md but every
    relevant methodology and format-spec page. This is the editorial ground
    truth for how the daily report is actually written.
    """
    if not os.path.isdir(_WIKI_DIR):
        return "(Obsidian wiki/ folder not found)"

    parts: list = []
    total_chars = 0

    # 1. Priority pages first (in defined order)
    seen: set = set()
    ordered = list(_WIKI_PRIORITY_PAGES)
    # 2. Then any other .md page in wiki/ (opportunistic)
    try:
        for fname in sorted(os.listdir(_WIKI_DIR)):
            if fname.endswith(".md") and fname not in ordered:
                ordered.append(fname)
    except OSError:
        pass

    for fname in ordered:
        if total_chars >= _MAX_WIKI_TOTAL_CHARS:
            break
        if fname in seen:
            continue
        seen.add(fname)
        fpath = os.path.join(_WIKI_DIR, fname)
        if not os.path.exists(fpath):
            continue
        try:
            with open(fpath, encoding="utf-8", errors="replace") as f:
                content = f.read()
        except OSError:
            continue
        excerpt = content[:_MAX_WIKI_PAGE_CHARS].strip()
        if len(content) > _MAX_WIKI_PAGE_CHARS:
            excerpt += f"\n…[truncated, {len(content):,} chars total]"
        parts.append(f"--- wiki/{fname} ---\n{excerpt}\n")
        total_chars += len(excerpt)

    if not parts:
        return "(no wiki pages readable)"

    header = (
        f"=== OBSIDIAN WIKI ({len(parts)} pages, {total_chars:,} chars) "
        f"— editorial methodology & format spec ===\n"
    )
    return header + "\n".join(parts)


# ── Source 2: Pipeline run log ─────────────────────────────────────────────────
def load_recent_log(days: int = DEFAULT_LOOKBACK_DAYS) -> list:
    if not os.path.exists(LEARNING_LOG_PATH):
        return []
    cutoff = (datetime.now(LOCAL_TZ) - timedelta(days=days)).strftime("%Y-%m-%d")
    entries = []
    with open(LEARNING_LOG_PATH, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                if entry.get("date", "") >= cutoff:
                    entries.append(entry)
            except json.JSONDecodeError:
                pass
    return entries


def _build_run_summary(entries: list) -> str:
    if not entries:
        return "(no pipeline run log entries yet — run the scraper first)"

    ticker_counts: Counter = Counter()
    sector_counts: Counter = Counter()
    source_counts: Counter = Counter()
    headlines_by_ticker: dict = defaultdict(list)
    notes_written = []

    for entry in entries:
        for item in entry.get("curated_items", []):
            t   = item.get("ticker", "?")
            s   = item.get("sector", "?")
            src = item.get("source", "")
            ticker_counts[t] += 1
            sector_counts[s] += 1
            if src:
                source_counts[src] += 1
            if len(headlines_by_ticker[t]) < 3:
                headlines_by_ticker[t].append(item.get("headline", ""))
        notes_written.extend(entry.get("notes_written", []))

    lines = [f"=== PIPELINE RUN LOG ({len(entries)} runs) ===\n"]
    lines.append("Top tickers curated:")
    for ticker, count in ticker_counts.most_common(20):
        samples = " | ".join(headlines_by_ticker[ticker][:2])
        lines.append(f"  {ticker}: {count}x — e.g. {samples}")
    lines.append("\nSector distribution:")
    for sector, count in sector_counts.most_common():
        lines.append(f"  {sector}: {count}")
    lines.append("\nTop sources:")
    for src, count in source_counts.most_common(10):
        lines.append(f"  {src}: {count}")
    if notes_written:
        lines.append(f"\nNotes written ({len(notes_written)} total, last 3):")
        for note in notes_written[-3:]:
            first = note.strip().splitlines()[0] if note.strip() else ""
            lines.append(f"  — {first[:100]}")
    return "\n".join(lines)


# ── Source 3: Obsidian vault conversations (News Writer sessions) ───────────────
def load_vault_conversations(days: int = DEFAULT_LOOKBACK_DAYS,
                             max_files: int = MAX_VAULT_CONV_FILES) -> str:
    """
    Read the most recent News Writer conversation files from the Obsidian vault.
    These are Rafael's real editorial sessions — triage decisions, note rewrites,
    feedback on what's material vs. noise.
    """
    if not os.path.isdir(VAULT_CONV_DIR):
        return "(Obsidian vault conversations directory not found)"

    cutoff_date = (datetime.now(LOCAL_TZ) - timedelta(days=days)).strftime("%Y-%m-%d")

    files = []
    for fname in os.listdir(VAULT_CONV_DIR):
        if not fname.endswith(".md"):
            continue
        date_prefix = fname[:10]
        if date_prefix >= cutoff_date:
            files.append((date_prefix, os.path.join(VAULT_CONV_DIR, fname)))

    files.sort(reverse=True)
    files = files[:max_files]

    if not files:
        # Fall back: take the most recent N files regardless of date cutoff
        all_files = sorted(
            [(f[:10], os.path.join(VAULT_CONV_DIR, f))
             for f in os.listdir(VAULT_CONV_DIR) if f.endswith(".md")],
            reverse=True
        )
        files = all_files[:max_files]

    excerpts = []
    chunk = MAX_CHARS_PER_CONV // 3   # split budget across 3 zones

    for date_str, fpath in files:
        try:
            with open(fpath, encoding="utf-8", errors="replace") as f:
                raw = f.read()
            # Sample from beginning (triage decisions), middle (writing feedback),
            # and end (final note / conclusions) to avoid missing editorial decisions.
            n = len(raw)
            if n <= MAX_CHARS_PER_CONV:
                excerpt = raw.strip()
            else:
                start  = raw[:chunk].strip()
                mid_s  = max(0, n // 2 - chunk // 2)
                middle = raw[mid_s: mid_s + chunk].strip()
                tail   = raw[max(0, n - chunk):].strip()
                excerpt = f"{start}\n…\n{middle}\n…\n{tail}"
            fname = os.path.basename(fpath)
            excerpts.append(f"--- {fname} ---\n{excerpt}\n")
        except OSError:
            pass

    if not excerpts:
        return "(could not read vault conversation files)"

    header = f"=== NEWS WRITER SESSIONS — Obsidian vault ({len(excerpts)} files) ===\n"
    return header + "\n".join(excerpts)


# ── Source 4: Claude Code conversation history ─────────────────────────────────
def _extract_text_from_entry(entry: dict) -> str:
    msg = entry.get("message", {})
    content = msg.get("content", "")
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                parts.append(block.get("text", "").strip())
        return " ".join(p for p in parts if p)
    return ""


def load_claude_conversations(days: int = DEFAULT_LOOKBACK_DAYS,
                              max_files: int = MAX_CLAUDE_CONV_FILES) -> str:
    """
    Read Claude Code session JSONL files from this project's conversation history.
    """
    cutoff = datetime.now(LOCAL_TZ) - timedelta(days=days)
    all_files = []

    for proj_dir in _PROJECT_DIRS:
        if not os.path.isdir(proj_dir):
            continue
        for fname in os.listdir(proj_dir):
            if not fname.endswith(".jsonl"):
                continue
            fpath = os.path.join(proj_dir, fname)
            try:
                mtime = datetime.fromtimestamp(os.path.getmtime(fpath), tz=LOCAL_TZ)
                if mtime >= cutoff:
                    all_files.append((mtime, fpath))
            except OSError:
                pass

    if not all_files:
        return "(no recent Claude Code session files found)"

    all_files.sort(key=lambda x: x[0], reverse=True)
    all_files = all_files[:max_files]

    excerpts = []
    for mtime_dt, fpath in all_files:
        try:
            with open(fpath, encoding="utf-8", errors="replace") as f:
                lines = [l.strip() for l in f if l.strip()]
        except OSError:
            continue

        dialogue_parts = []
        for line in lines:
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            etype = entry.get("type", "")
            if etype not in ("user", "assistant"):
                continue
            role = "USER" if etype == "user" else "CLAUDE"
            text = _extract_text_from_entry(entry).strip()
            if not text or len(text) < 10:
                continue
            if len(text) > 600:
                text = text[:600] + "…"
            dialogue_parts.append(f"{role}: {text}")

        if not dialogue_parts:
            continue

        dialogue = "\n".join(dialogue_parts)
        if len(dialogue) > MAX_CHARS_PER_CONV:
            dialogue = dialogue[:MAX_CHARS_PER_CONV] + "\n…[truncated]"

        date_str = mtime_dt.strftime("%Y-%m-%d")
        excerpts.append(f"--- {date_str} ({os.path.basename(fpath)[:8]}) ---\n{dialogue}\n")

    if not excerpts:
        return "(no readable Claude Code session content)"

    header = f"=== CLAUDE CODE SESSIONS ({len(excerpts)} files) ===\n"
    return header + "\n".join(excerpts)


# ── wiki_context.py helpers ────────────────────────────────────────────────────
def _read_current_context() -> str:
    with open(WIKI_CONTEXT_PATH, encoding="utf-8") as f:
        content = f.read()
    m = re.search(r'ANALYST_CONTEXT\s*=\s*"""([\s\S]*?)"""', content)
    if not m:
        raise ValueError("Could not find ANALYST_CONTEXT in wiki_context.py")
    return m.group(1)


_CONTEXT_ANCHOR = "## UBS LatAm TMT"

def _validate_new_context(new_context: str, current: str) -> str:
    """Guard the curator's brain (added 2026-07-02).

    The auto-learn loop has twice corrupted ANALYST_CONTEXT: once overwriting it
    with a literal '401 Failed to authenticate' error string, and twice leaking
    the model's own reasoning preamble ("I don't need to edit files...") into
    the string fed to the curator every run. This validator makes both
    impossible:
      1. auto-trims anything before the canonical anchor header;
      2. rejects error-message payloads;
      3. rejects suspicious shrinkage (>30% smaller than the current context).
    On rejection the learn cycle is skipped — the old context stays in place.
    """
    if _CONTEXT_ANCHOR not in new_context:
        raise RuntimeError(
            "learn: new ANALYST_CONTEXT rejected — anchor header "
            f"{_CONTEXT_ANCHOR!r} missing (likely an error string or junk)."
        )
    # Trim leaked preamble: keep from the anchor onwards.
    new_context = new_context[new_context.index(_CONTEXT_ANCHOR):]
    low = new_context[:2000].lower()
    if any(s in low for s in ("failed to authenticate", "api error", "401 ",
                              "invalid authentication")):
        raise RuntimeError(
            "learn: new ANALYST_CONTEXT rejected — contains an error message."
        )
    if current and len(new_context) < 0.7 * len(current):
        raise RuntimeError(
            f"learn: new ANALYST_CONTEXT rejected — shrank from "
            f"{len(current)} to {len(new_context)} chars (>30% loss)."
        )
    return new_context


def _apply_update(new_context: str) -> None:
    with open(WIKI_CONTEXT_PATH, encoding="utf-8") as f:
        original = f.read()

    # Validate + auto-clean before touching the file (see _validate_new_context).
    m = re.search(r'ANALYST_CONTEXT\s*=\s*"""([\s\S]*?)"""', original)
    new_context = _validate_new_context(new_context, m.group(1) if m else "")

    # Build updated content
    updated = re.sub(
        r'(ANALYST_CONTEXT\s*=\s*""")[\s\S]*?(""")',
        lambda m: m.group(1) + new_context + m.group(2),
        original, count=1,
    )
    if updated == original:
        raise RuntimeError("ANALYST_CONTEXT replacement had no effect")

    # Stamp the update date in the Source comment
    today = datetime.now(LOCAL_TZ).strftime("%Y-%m-%d")
    updated = re.sub(
        r"(#\s*Source:.*?)(\n)",
        lambda m: m.group(1) + f" — auto-updated {today}" + m.group(2),
        updated, count=1,
    )

    # Write a timestamped backup before overwriting
    backup_path = WIKI_CONTEXT_PATH.replace(".py", f"_backup_{today}.py")
    try:
        with open(backup_path, "w", encoding="utf-8") as f:
            f.write(original)
        print(f"  Backup saved: {os.path.basename(backup_path)}")
    except OSError as e:
        print(f"  [WARN] Could not write backup: {e}")

    with open(WIKI_CONTEXT_PATH, "w", encoding="utf-8") as f:
        f.write(updated)


def _show_diff(old: str, new: str) -> None:
    old_lines = set(old.splitlines())
    new_lines = set(new.splitlines())
    added   = new_lines - old_lines
    removed = old_lines - new_lines
    if not added and not removed:
        print("  No changes detected.")
        return
    if added:
        print(f"\n  Lines added ({len(added)}):")
        for line in sorted(added)[:25]:
            print(f"    + {line[:120]}")
    if removed:
        print(f"\n  Lines removed ({len(removed)}):")
        for line in sorted(removed)[:10]:
            print(f"    - {line[:120]}")


# ── Auto-watchlist extractor ──────────────────────────────────────────────────
_TOPIC_EXTRACTOR_SYSTEM = """You are extracting time-sensitive topics from a senior LatAm
TMT equity research analyst's recent News Writer sessions for a daily news scraper to flag.

Look for topics Rafael is actively discussing or analysing right now — regulatory
proceedings, pending deals, hot debates, sector themes, recurring concerns — that
are NOT already explicit in the curator's current ANALYST_CONTEXT.

Examples of useful topic types:
  - FISTEL (Brazilian telecom regulatory fee — affects cost structure for VIVT3/TIMS3)
  - 700 MHz auction outcome (affects multiple operators, ISPs entering mobile)
  - Specific pending court decisions that haven't reached a verdict yet
  - Specific ongoing M&A deals waiting for regulator approval
  - Sector themes Rafael keeps returning to but the scraper doesn't track yet

OUTPUT FORMAT — return ONLY 3–8 topics, one per line, no preamble:
- **TOPIC NAME** — why it matters, which covered tickers it affects, what to watch for.

Each topic should be one sentence, ~20-40 words. Do NOT replicate things already
in the current context. Do NOT include generic themes. ONLY surface topics with a
clear time-sensitivity (something is going to happen / be decided / develop)."""


def extract_auto_watchlist(vault_convs_text: str, current_context: str) -> str:
    """
    Mine recent News Writer vault conversations for time-sensitive topics
    that should be added to the watchlist. Returns formatted topic list, or
    empty string on failure.
    """
    if not vault_convs_text or "could not read" in vault_convs_text or "not found" in vault_convs_text:
        return ""

    user_msg = (
        f"=== CURRENT ANALYST_CONTEXT (do NOT duplicate these) ===\n\n"
        f"{current_context[:6000]}\n\n"
        f"=== RECENT NEWS WRITER SESSIONS ===\n\n"
        f"{vault_convs_text[:12000]}\n\n"
        "Extract 3–8 specific time-sensitive topics worth flagging in the daily clipping. "
        "Output the bullet list only — no preamble, no explanation."
    )

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    try:
        if api_key:
            resp = _call_claude_api(
                [{"role": "user", "content": user_msg}],
                _TOPIC_EXTRACTOR_SYSTEM, max_tokens=1200,
            )
            return _extract_text(resp).strip()
        else:
            return _call_claude_cli(
                user_msg, _TOPIC_EXTRACTOR_SYSTEM, timeout=180
            ).strip()
    except Exception as e:
        print(f"  [WARN] Auto-watchlist extraction failed: {e}")
        return ""


# ── Main ───────────────────────────────────────────────────────────────────────
def run_learn_cycle(auto: bool = False, dry_run: bool = False,
                    days: int = DEFAULT_LOOKBACK_DAYS) -> bool:
    """
    Run the full learning cycle. Returns True if wiki_context.py was updated.
    Called automatically from run_daily.py on milestone runs.
    """
    print(f"\n  Learning cycle — last {days} days")

    # Source 1: master editorial framework (always included)
    nw_context = load_news_writer_context()
    print(f"  NEWS_WRITER_CONTEXT.md: {'loaded' if 'not found' not in nw_context else 'MISSING'}")

    # Source 2: pipeline run log
    entries     = load_recent_log(days)
    run_summary = _build_run_summary(entries)
    print(f"  Pipeline runs: {len(entries)}")

    # Source 3: News Writer Obsidian vault conversations
    vault_convs = load_vault_conversations(days)
    n_vault     = vault_convs.count("--- 20")
    print(f"  News Writer vault sessions: {n_vault}")

    # Source 4: Claude Code conversation sessions
    code_convs = load_claude_conversations(days)
    n_code     = code_convs.count("--- 20")
    print(f"  Claude Code sessions: {n_code}")

    # Source 5: Real clipping examples (editorial ground truth from Rafael)
    clipping_examples = load_clipping_examples()
    has_examples = "not found" not in clipping_examples and "could not read" not in clipping_examples
    print(f"  Clipping examples: {'loaded' if has_examples else 'MISSING'}")

    # Source 6: Corpus analysis — analytical view of our own past curation
    corpus_summary = build_corpus_summary(days)
    has_corpus = "no past runs" not in corpus_summary
    print(f"  Corpus analysis: {'computed' if has_corpus else 'EMPTY (run pipeline first)'}")

    # Source 7: Claude Data reference docs (live-read every cycle, no upload)
    reference_docs = load_reference_docs()
    n_docs = reference_docs.count("--- ") if reference_docs else 0
    print(f"  Claude Data reference docs: {n_docs} live-read")

    # Source 8: Observer published-notes structured analysis (strongest signal)
    observer_stats = build_observer_stats_block()
    has_observer = "no Observer notes parsed" not in observer_stats
    n_obs = observer_stats.count("note(s)") if has_observer else 0
    print(f"  Observer notes corpus: {'parsed' if has_observer else 'EMPTY'} "
          f"({n_obs} ticker entries)")

    if not entries and n_vault == 0 and n_code == 0 and not has_examples:
        print("  Nothing to learn from yet.")
        return False

    try:
        current_context = _read_current_context()
    except (FileNotFoundError, ValueError) as e:
        print(f"  [ERROR] {e}")
        return False

    # Surface Observer blind-spots (frequently-noted tickers missing from context)
    blind_spots = find_underrepresented_tickers(min_notes=3, current_context=current_context)
    blind_spot_text = ""
    if blind_spots:
        blind_spot_text = (
            "\nBLIND SPOTS — tickers Rafael writes about (3+ notes) but missing from A:\n"
            + "\n".join(f"  - {t}: {n} Observer note(s)" for t, n in blind_spots)
        )

    user_message = (
        f"A. CURRENT ANALYST_CONTEXT:\n\n{current_context}\n\n"
        f"B. {run_summary}\n\n"
        f"C. {vault_convs}\n\n"
        f"D. {code_convs}\n\n"
        f"E. {clipping_examples}\n\n"
        f"F. {corpus_summary}\n\n"
        f"G. {reference_docs or '(no Claude Data .docx files found)'}\n\n"
        f"H. {observer_stats}{blind_spot_text}\n\n"
        f"Additional reference (do not replicate — use only to understand editorial style):\n"
        f"{nw_context}\n\n"
        "Based on B, C, D, E, F, G, H: propose refinements to A. "
        "E shows real clipping examples — use them to understand correct ticker aliases "
        "(TEF-BZ not VIVT3, TIM not TIMS3, ACN/COG/INFY for peers), multi-ticker format "
        "(AMX/TEF-BZ/TIM), and what editorial judgment was applied. "
        "F shows the curator's own behavior — promotion rates, themes that recur, sources "
        "that contribute material vs. noise. If F shows a ticker is curated repeatedly but "
        "never promoted to a note, either tighten the materiality bar for it OR add it to the "
        "active running stories so the note writer picks it up. "
        "G shows Rafael's reference docs (live-read this cycle). Use G to cross-check "
        "coverage universe, recent call commentary, positioning data, and editorial framework "
        "against A — surface anything in G that A is missing or contradicts. "
        "H is the STRONGEST signal — Rafael's actual published Observer notes. The ticker "
        "frequency reveals what he considers material. The signal vocabulary distribution "
        "shows his calibration (e.g., if 'Mixed read' is used 15x, the curator should "
        "flag situations that warrant that signal). Any blind-spot tickers listed above "
        "MUST be addressed — add a section for them in A. "
        "Do NOT replicate past news. Use E, F, G, H only to calibrate editorial logic. "
        "Preserve all existing content. Return the full updated ANALYST_CONTEXT string."
    )

    print("  Calling Claude to propose refinements...")
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    try:
        if api_key:
            resp = _call_claude_api(
                [{"role": "user", "content": user_message}],
                LEARN_SYSTEM, max_tokens=6000,
            )
            new_context = _extract_text(resp).strip()
        else:
            new_context = _call_claude_cli(
                user_message, LEARN_SYSTEM, timeout=600
            ).strip()
    except Exception as e:
        print(f"  [ERROR] Claude call failed: {e}")
        return False

    if not new_context:
        print("  Claude returned no suggestions.")
        return False

    # Strip whitespace for comparison — don't apply if nothing actually changed
    if new_context.strip() == current_context.strip():
        print("  No changes needed — ANALYST_CONTEXT is already up to date.")
        return False

    print("\n  Proposed changes:")
    _show_diff(current_context, new_context)

    if dry_run:
        print("  [--dry-run] No files modified.")
        return False

    if not auto:
        try:
            confirm = input(
                "\n  Apply update to wiki_context.py? [y/N]: "
            ).strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("  Skipped.")
            return False
        if confirm != "y":
            print("  Update skipped.")
            return False

    try:
        _apply_update(new_context)
        print("  wiki_context.py updated.")
    except Exception as e:
        print(f"  [ERROR] Failed to apply: {e}")
        return False

    # ── Refresh auto-suggested watchlist from recent News Writer activity ──
    # This runs at the same cadence as the learn cycle (every 10 runs by default).
    # Topics surface immediately on the next pipeline run via watchlist injection.
    print("\n  Extracting auto-suggested watch topics from News Writer sessions...")
    try:
        auto_topics = extract_auto_watchlist(vault_convs, new_context)
        if auto_topics:
            saved = save_auto_suggestions(auto_topics)
            if saved:
                line_count = sum(1 for ln in auto_topics.splitlines() if ln.strip().startswith("-"))
                print(f"  -> {line_count} topic(s) saved to: {os.path.basename(saved)}")
                print(f"     Promote any of these to vault/wiki/watchlist.md to lock them in.")
        else:
            print("  -> No new topics surfaced.")
    except Exception as e:
        print(f"  [WARN] Auto-watchlist refresh skipped: {e}")

    return True


def main():
    auto    = "--auto"    in sys.argv
    dry_run = "--dry-run" in sys.argv
    days    = DEFAULT_LOOKBACK_DAYS
    if "--days" in sys.argv:
        idx = sys.argv.index("--days")
        if idx + 1 < len(sys.argv):
            try:
                days = int(sys.argv[idx + 1])
            except ValueError:
                pass
    run_learn_cycle(auto=auto, dry_run=dry_run, days=days)


if __name__ == "__main__":
    main()
