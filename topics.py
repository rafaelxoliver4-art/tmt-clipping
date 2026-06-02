# topics.py — Autonomous topic discovery, scoring, and decay
#
# THE LEARNING LOOP — runs entirely without manual intervention:
#
#   Every pipeline run:
#     1. After curation, record which active topics matched headlines (reinforce)
#     2. After note writing, record which topics became full notes (strong reinforce)
#     3. Apply gentle daily decay so unused topics fade
#     4. Inject top-scoring topics into curator + note writer prompts
#
#   Every N pipeline runs (default 3):
#     5. Refresh: read recent News Writer conversations + wiki edits
#     6. Ask Claude to extract current themes from that activity
#     7. Merge: new topics added, existing reinforced, scores updated
#     8. Prune topics with score below threshold (auto-decay drops dead topics)
#
# Result: the more the system runs, the more accurately it tracks what
# matters RIGHT NOW. Topics that keep appearing in vault activity AND in
# our own curation stay alive. Topics that lose relevance auto-decay.
# Zero user intervention.
#
# State lives in output/active_topics.json — durable across runs.

import json
import os
import re
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from config import LOCAL_TZ

# ── Paths & tuning ────────────────────────────────────────────────────────────
_HERE              = os.path.dirname(os.path.abspath(__file__))
TOPICS_PATH        = os.path.join(_HERE, "output", "active_topics.json")

# Refresh cadence — how often to mine vault activity for new topics.
# Every N pipeline runs. Default 3 = roughly twice a week if pipeline runs daily.
DEFAULT_REFRESH_EVERY_N_RUNS = 3

# Scoring tuning — weights are ordered by signal strength
HIT_VAULT_MENTION   = 1.0    # vault conversation mention (soft signal)
HIT_CLIPPING_MATCH  = 2.0    # appeared in our own curated clipping
HIT_NOTE_PROMOTION  = 5.0    # we wrote a note about it
HIT_OBSERVER_NOTE   = 10.0   # Rafael actually published a note (HIGHEST — ground truth)
DECAY_HALF_LIFE_DAYS = 21    # score halves every 21 days of inactivity
INJECT_THRESHOLD    = 0.8    # show in prompt above this (a fresh vault mention counts)
PRUNE_THRESHOLD     = 0.3    # drop from state when score falls below this (dead)
TOP_N_TO_INJECT     = 8      # max topics shown in the prompt injection


# ── State I/O ─────────────────────────────────────────────────────────────────
def _empty_state() -> Dict:
    return {
        "topics":              {},   # name → {description, score, dates, hit counts}
        "last_refreshed":      "",
        "refresh_count":       0,
        "runs_since_refresh":  0,
        # Track which Observer notes we've already credited so we don't
        # double-count when Rafael's file is unchanged
        "last_observer_position":  -1,
        "last_observer_signature": "",
    }


def _load_state() -> Dict:
    if not os.path.exists(TOPICS_PATH):
        return _empty_state()
    try:
        with open(TOPICS_PATH, encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict) or "topics" not in data:
            return _empty_state()
        # Backfill missing keys for forward-compat
        for k, v in _empty_state().items():
            data.setdefault(k, v)
        return data
    except (OSError, json.JSONDecodeError):
        return _empty_state()


def _save_state(state: Dict) -> None:
    try:
        os.makedirs(os.path.dirname(TOPICS_PATH), exist_ok=True)
        with open(TOPICS_PATH, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
    except OSError as e:
        print(f"  [WARN] Could not save topics state: {e}")


# ── Decay & scoring ───────────────────────────────────────────────────────────
def _now_str() -> str:
    return datetime.now(LOCAL_TZ).isoformat()


def _today() -> str:
    return datetime.now(LOCAL_TZ).strftime("%Y-%m-%d")


def _days_since(iso_date_str: str) -> float:
    if not iso_date_str:
        return 9999
    try:
        d = datetime.fromisoformat(iso_date_str)
        if d.tzinfo is None:
            d = d.replace(tzinfo=LOCAL_TZ)
        return (datetime.now(LOCAL_TZ) - d).total_seconds() / 86400.0
    except ValueError:
        return 9999


def _apply_decay(score: float, days_since: float,
                 half_life: float = DECAY_HALF_LIFE_DAYS) -> float:
    """Exponential decay: score(t) = score(0) * 0.5 ** (t / half_life)."""
    if days_since <= 0:
        return score
    return score * (0.5 ** (days_since / half_life))


def _new_topic_record(name: str, description: str = "") -> Dict:
    today = _today()
    return {
        "name":             name,
        "description":      description,
        "first_seen":       today,
        "last_reinforced":  today,
        "vault_mentions":   0,
        "clipping_hits":    0,
        "note_promotions":  0,
        "score":            0.0,
    }


def _normalize_name(name: str) -> str:
    """Canonicalize a topic name so 'FISTEL' and 'Fistel' don't fork."""
    return name.strip().upper()


# ── Reinforcement (called from pipeline after curation + notes) ──────────────
def _topic_matches_text(topic_name: str, text: str) -> bool:
    if not topic_name or not text:
        return False
    pattern = rf"\b{re.escape(topic_name)}\b"
    return bool(re.search(pattern, text, re.IGNORECASE))


def record_clipping_hits(report: Dict) -> int:
    """
    For each topic, count how many curated headlines contain it.
    Increments clipping_hits and pushes score up. Returns total hits recorded.
    """
    state = _load_state()
    if not state["topics"]:
        return 0

    # Flatten all curated headlines from the report
    all_headlines: List[str] = []
    for sector_items in report.values():
        if not isinstance(sector_items, list):
            continue
        for item in sector_items:
            h = (item.get("headline") or "").strip()
            t = (item.get("ticker") or "").strip()
            if h:
                all_headlines.append(f"{t} {h}")

    total_hits = 0
    for topic_key, topic in state["topics"].items():
        # Match against the topic NAME (canonical) and the FIRST WORD of description
        # (so a description like "FISTEL — fee restructuring" matches "fee" too)
        hit_count = sum(1 for h in all_headlines if _topic_matches_text(topic_key, h))
        if hit_count > 0:
            topic["clipping_hits"] += hit_count
            topic["last_reinforced"] = _today()
            topic["score"] += hit_count * HIT_CLIPPING_MATCH
            total_hits += hit_count

    if total_hits:
        _save_state(state)
    return total_hits


def reinforce_from_observer() -> Tuple[int, int]:
    """
    Read Rafael's published Observer notes (from TMT Online Observer Data.docx)
    and apply HIT_OBSERVER_NOTE reinforcement to each note's ticker(s).

    Idempotent: tracks the last note position credited and only processes notes
    appended since last call. If the file hasn't changed, this is a no-op.

    Returns (n_notes_credited, n_topics_touched).
    """
    try:
        from observer_corpus import parse_observer_doc
    except ImportError:
        return (0, 0)

    data = parse_observer_doc()
    if data.get("total_notes", 0) == 0:
        return (0, 0)

    state = _load_state()
    last_pos = state.get("last_observer_position", -1)
    last_sig = state.get("last_observer_signature", "")
    cur_sig  = data.get("file_signature", "")

    # Same file as last time AND we've processed all positions → nothing new
    if cur_sig == last_sig and last_pos >= data["total_notes"] - 1:
        return (0, 0)

    new_notes = [n for n in data["notes"] if n["position"] > last_pos]
    if not new_notes:
        # File changed but no new positions (rare — maybe edits-in-place).
        # Still update the signature so we don't keep checking.
        state["last_observer_signature"] = cur_sig
        _save_state(state)
        return (0, 0)

    notes_credited  = 0
    topics_touched: set = set()

    for note in new_notes:
        for raw_ticker in note.get("tickers_split", []):
            key = _normalize_name(raw_ticker)
            if not key:
                continue
            if key not in state["topics"]:
                desc = note.get("headline", "")[:200]
                state["topics"][key] = _new_topic_record(key, desc)
            t = state["topics"][key]
            t["note_promotions"] += 1   # reuse this counter for "Rafael notes"
            t["last_reinforced"] = _today()
            t["score"] += HIT_OBSERVER_NOTE
            topics_touched.add(key)
        notes_credited += 1

    # Update tracking
    state["last_observer_position"]  = max(n["position"] for n in new_notes)
    state["last_observer_signature"] = cur_sig
    _save_state(state)

    return (notes_credited, len(topics_touched))


def record_note_promotions(notes: List[str]) -> int:
    """When a topic shows up in a written note, that's the strongest signal."""
    state = _load_state()
    if not state["topics"] or not notes:
        return 0

    note_texts = [n for n in notes if isinstance(n, str)]
    if not note_texts:
        return 0

    total_promos = 0
    for topic_key, topic in state["topics"].items():
        promos = sum(1 for n in note_texts if _topic_matches_text(topic_key, n))
        if promos > 0:
            topic["note_promotions"] += promos
            topic["last_reinforced"] = _today()
            topic["score"] += promos * HIT_NOTE_PROMOTION
            total_promos += promos

    if total_promos:
        _save_state(state)
    return total_promos


# ── Refresh (called every N runs to mine vault activity) ──────────────────────
def should_refresh(every_n: int = DEFAULT_REFRESH_EVERY_N_RUNS) -> bool:
    """Return True if it's time to mine vault activity for new topics."""
    state = _load_state()
    return state["runs_since_refresh"] >= every_n


def increment_run_counter() -> None:
    state = _load_state()
    state["runs_since_refresh"] = state.get("runs_since_refresh", 0) + 1
    _save_state(state)


def _decay_all_scores(state: Dict) -> None:
    """Apply time-based decay to every topic's score in place."""
    for topic in state["topics"].values():
        days = _days_since(topic.get("last_reinforced", ""))
        topic["score"] = round(_apply_decay(topic.get("score", 0.0), days), 3)


def _prune_low_scores(state: Dict, threshold: float = PRUNE_THRESHOLD) -> int:
    """Drop topics with score below threshold. Returns count pruned."""
    keep = {k: v for k, v in state["topics"].items() if v.get("score", 0) >= threshold}
    dropped = len(state["topics"]) - len(keep)
    state["topics"] = keep
    return dropped


def _parse_extracted_topics(text: str) -> List[Tuple[str, str]]:
    """
    Parse Claude's bullet list output into (name, description) pairs.
    Expected format:  "- **NAME** — description text"
    Falls back to simpler patterns.
    """
    out: List[Tuple[str, str]] = []
    if not text:
        return out
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith(("-", "•", "*")):
            continue
        # Strip ONE leading bullet marker plus whitespace — not greedy on `*`,
        # otherwise we'd eat the `**` of `**FISTEL**`.
        line = re.sub(r"^[-•*]\s*", "", line)
        # Pattern: **NAME** — description
        m = re.match(r"\*\*([^*]+)\*\*\s*[—–\-:]\s*(.+)", line)
        if m:
            name, desc = m.group(1).strip(), m.group(2).strip()
        else:
            # Fallback: NAME — description (no bold)
            m2 = re.match(r"([A-Z][A-Z0-9\s/\-\.&]{2,40}?)\s*[—–\-:]\s*(.+)", line)
            if m2:
                name, desc = m2.group(1).strip(), m2.group(2).strip()
            else:
                continue
        if name and len(name) <= 60:
            out.append((name, desc))
    return out


def merge_extracted_topics(extracted_text: str) -> Tuple[int, int]:
    """
    Merge a fresh batch of extracted topics into state.
    For each extracted topic: if new → add; if existing → reinforce.
    Returns (n_added, n_reinforced).
    """
    state = _load_state()
    pairs = _parse_extracted_topics(extracted_text)
    added = reinforced = 0

    for raw_name, desc in pairs:
        key = _normalize_name(raw_name)
        if key in state["topics"]:
            t = state["topics"][key]
            t["vault_mentions"] += 1
            t["last_reinforced"] = _today()
            t["score"] += HIT_VAULT_MENTION
            # Refresh description if Claude phrased it more sharply this time
            if desc and len(desc) > len(t.get("description", "")):
                t["description"] = desc
            reinforced += 1
        else:
            t = _new_topic_record(key, desc)
            t["vault_mentions"] = 1
            t["score"] = HIT_VAULT_MENTION
            state["topics"][key] = t
            added += 1

    state["last_refreshed"]     = _now_str()
    state["refresh_count"]     += 1
    state["runs_since_refresh"] = 0
    _save_state(state)
    return added, reinforced


def post_refresh_maintenance() -> Tuple[int, int]:
    """
    Apply decay and prune low-scoring topics. Run after every refresh.
    Returns (pruned_count, remaining_count).
    """
    state = _load_state()
    _decay_all_scores(state)
    pruned    = _prune_low_scores(state)
    remaining = len(state["topics"])
    _save_state(state)
    return pruned, remaining


# ── Prompt injection (called every pipeline run) ─────────────────────────────
def build_prompt_injection() -> str:
    """
    Build the topic block injected into CATEGORISE_SYSTEM and NOTE_SYSTEM.
    Returns "" if there's nothing yet (early days).
    """
    state = _load_state()
    if not state["topics"]:
        return ""

    # Apply decay at READ time too so stale topics don't fire just because we
    # didn't refresh today.
    decayed = []
    for k, t in state["topics"].items():
        days = _days_since(t.get("last_reinforced", ""))
        live_score = _apply_decay(t.get("score", 0.0), days)
        if live_score >= INJECT_THRESHOLD:
            decayed.append((k, t, live_score))

    if not decayed:
        return ""

    decayed.sort(key=lambda x: x[2], reverse=True)
    top = decayed[:TOP_N_TO_INJECT]

    parts = [
        "### CURRENT WATCH TOPICS (auto-discovered, scored, decayed)",
        "",
        "Topics below are auto-extracted from recent News Writer activity and",
        "reinforced when they appear in our own curation. If a headline matches",
        "any topic — even loosely — FLAG IT as material. Promote to a full note",
        "when the headline carries a concrete development (decision, ruling,",
        "deal, datapoint), not just commentary.",
        "",
    ]
    for name, t, score in top:
        desc = t.get("description", "").strip()
        line = f"- **{name}**"
        if desc:
            # First sentence only — keep injection compact
            first_sentence = re.split(r"(?<=[\.!?])\s+", desc)[0]
            line += f" — {first_sentence}"
        parts.append(line)

    return "\n".join(parts)


# ── Inspection helpers ────────────────────────────────────────────────────────
def status_text() -> str:
    """Human-readable status of the topic ecosystem."""
    state = _load_state()
    out = [
        f"Active topics: {len(state['topics'])}",
        f"Last refreshed: {state.get('last_refreshed', 'never')}",
        f"Refresh count: {state.get('refresh_count', 0)}",
        f"Runs since last refresh: {state.get('runs_since_refresh', 0)}",
        "",
    ]
    if not state["topics"]:
        out.append("(no topics yet — first refresh happens after a few pipeline runs)")
        return "\n".join(out)

    rows = []
    for k, t in state["topics"].items():
        days = _days_since(t.get("last_reinforced", ""))
        live_score = _apply_decay(t.get("score", 0.0), days)
        rows.append((k, live_score, t))
    rows.sort(key=lambda x: x[1], reverse=True)

    out.append(f"  {'Topic':<24} {'Score':>7} {'Vault':>6} {'Clip':>5} {'Note':>5} Last")
    out.append(f"  {'-'*24} {'-'*7} {'-'*6} {'-'*5} {'-'*5} {'-'*10}")
    for k, score, t in rows:
        out.append(
            f"  {k[:24]:<24} {score:>7.2f} "
            f"{t.get('vault_mentions',0):>6} "
            f"{t.get('clipping_hits',0):>5} "
            f"{t.get('note_promotions',0):>5} "
            f"{t.get('last_reinforced','-')}"
        )
    return "\n".join(out)


def main() -> None:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    if cmd == "status":
        print(status_text())
    elif cmd == "inject":
        text = build_prompt_injection()
        print(text or "(no injection — no active topics)")
    elif cmd == "reset":
        if os.path.exists(TOPICS_PATH):
            os.remove(TOPICS_PATH)
            print(f"Removed {TOPICS_PATH}")
        else:
            print("Already empty.")
    else:
        print("Usage: python topics.py [status|inject|reset]")


if __name__ == "__main__":
    main()
