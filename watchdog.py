"""Delivery watchdog — a missed clipping slot is either delivered or alerted, never silent.

Why this exists: on 2026-07-06 the 16:30 run was killed mid-scrape (PC slept /
process terminated). A dead process can't email an alert, Task Scheduler's
restart-on-failure doesn't fire for terminated tasks, and the slot passed
silently. This watchdog closes that hole from the OUTSIDE of the run.

How it works: run_daily.py writes output/last_delivery.json after every
successful send. A separate scheduled task runs this script ~45-50 min after
each digest slot; if no delivery happened since the slot opened, it re-runs
the pipeline itself. If that recovery run also fails, run_daily.py's own
[ACTION NEEDED] alert + CLIPPING_FAILED.txt flag fire. Either way: digest or
alert — never nothing.

Usage:  python watchdog.py --since HH:MM
  Requires a delivery at/after HH:MM local time TODAY; otherwise recovers.

Race safety: if a catch-up run is in flight when the watchdog fires (e.g. the
PC was just turned on and Task Scheduler is running the missed slot), the
fresh stamp appears within minutes — so before recovering, the watchdog polls
for a fresh stamp for up to 12 minutes instead of starting a duplicate run.

Weekdays only (exits silently on weekends).
"""
import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime

from config import LOCAL_TZ

HERE  = os.path.dirname(os.path.abspath(__file__))
STAMP = os.path.join(HERE, "output", "last_delivery.json")

GRACE_POLLS   = 12   # how many times to re-check for a concurrent run's stamp
GRACE_SLEEP_S = 60   # seconds between checks


def _log(msg: str) -> None:
    print(f"[watchdog {datetime.now(LOCAL_TZ):%Y-%m-%d %H:%M:%S}] {msg}", flush=True)


def _read_sent_at():
    try:
        with open(STAMP, encoding="utf-8") as f:
            return datetime.fromisoformat(json.load(f)["sent_at"])
    except Exception:
        return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", required=True, metavar="HH:MM",
                    help="require a delivery at/after this local time today")
    args = ap.parse_args()

    now = datetime.now(LOCAL_TZ)
    if now.weekday() >= 5:
        _log("weekend — nothing to check")
        return 0

    hh, mm = map(int, args.since.split(":"))
    threshold = now.replace(hour=hh, minute=mm, second=0, microsecond=0)
    if now < threshold:
        _log(f"fired before {args.since} — nothing to judge yet")
        return 0

    sent_at = _read_sent_at()
    if sent_at and sent_at >= threshold:
        _log(f"OK — digest delivered {sent_at:%H:%M} (>= {args.since})")
        return 0

    # Grace window: a catch-up run may be mid-flight right now (PC just woke).
    _log(f"no delivery since {args.since} — grace-waiting up to "
         f"{GRACE_POLLS * GRACE_SLEEP_S // 60} min for an in-flight run...")
    for _ in range(GRACE_POLLS):
        time.sleep(GRACE_SLEEP_S)
        sent_at = _read_sent_at()
        if sent_at and sent_at >= threshold:
            _log(f"OK — in-flight run delivered {sent_at:%H:%M}")
            return 0

    last = f"{sent_at:%Y-%m-%d %H:%M}" if sent_at else "never"
    _log(f"MISSED — slot since {args.since} not delivered (last: {last}). "
         f"Launching recovery run...")
    r = subprocess.run([sys.executable, os.path.join(HERE, "run_daily.py")],
                       cwd=HERE)
    _log(f"recovery run finished with exit={r.returncode}")
    return r.returncode


if __name__ == "__main__":
    sys.exit(main())
