# claude_data_reader.py — Live read Rafael's reference docs from Claude Data/
#
# WHY:
#   Rafael keeps reference materials (TMT Online Observer Data, Conference
#   Call Transcripts, Crowding Score Data, etc.) as .docx in his
#   Claude Data folder. He updates them periodically. We want the system
#   to read them LIVE on every learn cycle so updates propagate without
#   any upload step — drop a new file in, it gets read on the next cycle.
#
# WHAT:
#   - Lists every .docx in CLAUDE_DATA_DIR (skips temp lock files)
#   - Reads each one as XML (no python-docx dependency required)
#   - Returns combined text with file headers, capped at total budget
#
# WHO USES IT:
#   - learn.py — as a learning source on every learn cycle
#   - CLI: `python claude_data_reader.py` to inspect what got read

import os
import re
import sys
import zipfile
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Dict, List, Tuple

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ── Path & tuning ─────────────────────────────────────────────────────────────
# Default location — edit if Rafael moves the folder. Resolved at call time
# so changes propagate without restart.
CLAUDE_DATA_DIR = os.path.join(
    os.path.expanduser("~"), "OneDrive", "Área de Trabalho", "Claude Data"
)

# Total budget across all files (combined into the learn-cycle prompt)
_TOTAL_CHARS     = 16000
# Hard floor per file so even with many docs each still gets a usable excerpt
_MIN_PER_FILE    = 1500
# Hard ceiling per file so a single 500k-char doc doesn't eat the budget
_MAX_PER_FILE    = 4000

# Word OOXML namespace
_W_NS = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


# ── DOCX text extraction (zero dependencies) ─────────────────────────────────
def read_docx_text(path: str) -> str:
    """
    Extract all paragraph text from a .docx file. .docx is a ZIP with
    word/document.xml inside; the visible text lives in <w:t> elements.

    Returns "" on any parsing failure (corrupt file, password-protected, etc.)
    rather than raising — this loop is autonomous and shouldn't crash on a
    bad file.
    """
    try:
        with zipfile.ZipFile(path) as z:
            with z.open("word/document.xml") as f:
                tree = ET.parse(f)
    except (zipfile.BadZipFile, KeyError, ET.ParseError, OSError):
        return ""

    root = tree.getroot()
    paragraphs: List[str] = []
    for p in root.iter(f"{_W_NS}p"):
        texts = [t.text for t in p.iter(f"{_W_NS}t") if t.text]
        if texts:
            paragraphs.append("".join(texts).strip())

    # Drop empty paragraphs and collapse runs of whitespace
    paragraphs = [re.sub(r"\s+", " ", p) for p in paragraphs if p]
    return "\n".join(paragraphs)


def _is_temp_or_hidden(fname: str) -> bool:
    """Word creates ~$Filename.docx lock files. Skip them."""
    return fname.startswith("~$") or fname.startswith(".")


# ── List & summarize files ────────────────────────────────────────────────────
def list_docx_files(directory: str = None) -> List[Dict]:
    """
    Return metadata for every .docx in the directory (sorted by modified time,
    newest first). Each entry: {name, path, mtime, size}.
    """
    directory = directory or CLAUDE_DATA_DIR
    if not os.path.isdir(directory):
        return []

    out: List[Dict] = []
    try:
        for fname in os.listdir(directory):
            if not fname.lower().endswith(".docx"):
                continue
            if _is_temp_or_hidden(fname):
                continue
            full = os.path.join(directory, fname)
            try:
                stat = os.stat(full)
                out.append({
                    "name":  fname,
                    "path":  full,
                    "mtime": datetime.fromtimestamp(stat.st_mtime),
                    "size":  stat.st_size,
                })
            except OSError:
                continue
    except OSError:
        return []

    out.sort(key=lambda x: x["mtime"], reverse=True)
    return out


# ── Build the learn-cycle text block ──────────────────────────────────────────
def load_reference_docs(directory: str = None) -> str:
    """
    Read every .docx in the directory live and return a combined excerpt
    suitable for inclusion in a Claude prompt. Each file gets a header so
    Claude knows what it's reading and when it was last edited.

    Empty string if the directory has no .docx files (or doesn't exist).
    """
    files = list_docx_files(directory)
    if not files:
        return ""

    # Dynamic per-file budget: split the total fairly so every doc gets a slot.
    # Clamped between MIN and MAX so single docs neither starve nor dominate.
    per_file_budget = max(
        _MIN_PER_FILE,
        min(_MAX_PER_FILE, _TOTAL_CHARS // max(len(files), 1)),
    )

    parts: List[str] = []
    total_chars = 0

    for entry in files:
        if total_chars >= _TOTAL_CHARS:
            break

        text = read_docx_text(entry["path"])
        if not text:
            continue

        # For very large files, sample beginning + middle + end so we don't
        # only see the first section of a 500-page doc.
        if len(text) > per_file_budget * 2:
            chunk = per_file_budget // 3
            mid_start = max(0, len(text) // 2 - chunk // 2)
            excerpt = (
                text[:chunk].strip()
                + f"\n\n…[middle excerpt of {len(text):,}-char doc]…\n\n"
                + text[mid_start: mid_start + chunk].strip()
                + f"\n\n…[end excerpt]…\n\n"
                + text[-chunk:].strip()
            )
        else:
            excerpt = text[:per_file_budget]
            if len(text) > per_file_budget:
                excerpt += f"\n…[truncated, {len(text):,} chars total]"

        header = (
            f"--- {entry['name']} "
            f"(last edited {entry['mtime'].strftime('%Y-%m-%d')}) ---"
        )
        parts.append(f"{header}\n{excerpt}")
        total_chars += len(excerpt)

    if not parts:
        return ""

    summary_header = (
        f"=== CLAUDE DATA REFERENCE FILES ({len(parts)} docs, {total_chars:,} chars) "
        f"— live-read every cycle, updates propagate without manual upload ===\n"
    )
    return summary_header + "\n\n".join(parts)


# ── CLI ───────────────────────────────────────────────────────────────────────
def main() -> None:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "summary"

    if cmd == "list":
        files = list_docx_files()
        if not files:
            print(f"No .docx files in {CLAUDE_DATA_DIR}")
            return
        print(f"\n{len(files)} .docx file(s) in {CLAUDE_DATA_DIR}\n")
        print(f"  {'File':<55} {'Modified':<12} {'Size':>8}")
        print(f"  {'-'*55} {'-'*12} {'-'*8}")
        for f in files:
            sz = f"{f['size']/1024:.1f} KB"
            mod = f["mtime"].strftime("%Y-%m-%d")
            print(f"  {f['name'][:55]:<55} {mod:<12} {sz:>8}")

    elif cmd == "read":
        if len(sys.argv) < 3:
            print("Usage: python claude_data_reader.py read <filename>")
            return
        target = sys.argv[2]
        files = list_docx_files()
        match = next((f for f in files if target.lower() in f["name"].lower()), None)
        if not match:
            print(f"No file matching '{target}'")
            return
        text = read_docx_text(match["path"])
        print(f"\n=== {match['name']} ({len(text):,} chars) ===\n")
        print(text[:3000])
        if len(text) > 3000:
            print(f"\n…[{len(text)-3000:,} more chars]")

    else:
        # Default: show what would be loaded into the learn cycle
        out = load_reference_docs()
        if not out:
            print(f"No .docx files in {CLAUDE_DATA_DIR}")
        else:
            print(out)


if __name__ == "__main__":
    main()
