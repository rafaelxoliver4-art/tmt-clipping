# send_digest.py — Final email step of the TMT News Clipping pipeline.
#
# Reads a curated JSON file (produced by Claude Code in-session from the
# claude_input_YYYY-MM-DD.txt written by run_daily.py) and emails it.
#
# Expected JSON shape:
#   {
#     "report": {
#       "Telecom LatAm and World": [
#         {"ticker": "AMX", "headline": "...", "source": "...", "link": "..."},
#         ...
#       ],
#       "Software and AI": [...]
#     },
#     "events": [
#       {"date": "YYYY-MM-DD", "ticker_or_name": "...", "event": "..."}
#     ]
#   }
#
# Usage:
#   python send_digest.py output/curated_2026-04-21.json
#   python send_digest.py output/curated_2026-04-21.json --dry   # render preview, no send

import json
import os
import sys
from datetime import datetime

from config import LOCAL_TZ, EMAIL_RECIPIENTS, OUTPUT_DIR
from email_sender import render_html, run as email_run, _load_env


def _latest_curated() -> str:
    if not os.path.isdir(OUTPUT_DIR):
        return ""
    candidates = sorted(
        f for f in os.listdir(OUTPUT_DIR)
        if f.startswith("curated_") and f.endswith(".json")
    )
    return os.path.join(OUTPUT_DIR, candidates[-1]) if candidates else ""


def main() -> None:
    _load_env()
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    dry  = "--dry" in sys.argv

    if args:
        path = args[0]
    else:
        path = _latest_curated()
        if not path:
            print("No curated JSON file found. Pass a path or create one in output/")
            sys.exit(1)
        print(f"Using latest: {path}")

    if not os.path.exists(path):
        print(f"File not found: {path}")
        sys.exit(1)

    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    report = data.get("report", {})
    events = data.get("events", [])
    if not isinstance(report, dict):
        print("JSON must have a 'report' object keyed by sector name.")
        sys.exit(1)

    total = sum(len(v) for v in report.values() if isinstance(v, list))
    print(f"Loaded {total} curated items across {sum(1 for v in report.values() if v)} sectors")

    if dry:
        html = render_html(report, events)
        preview = os.path.join(OUTPUT_DIR, f"email_preview_{datetime.now(LOCAL_TZ):%Y-%m-%d}.html")
        with open(preview, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"Preview written: {os.path.abspath(preview)}")
        return

    print(f"Sending to: {', '.join(EMAIL_RECIPIENTS)}")
    sent = email_run(report, events)
    print(f"Sent {sent} items.")


if __name__ == "__main__":
    main()
