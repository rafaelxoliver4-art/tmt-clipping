# _run_catchup.py — catch-up send for the TMT clipping whose 16:30 scheduled
# run aborted (Claude CLI categorisation timed out at Step 4, before send).
# Reuses this morning/afternoon's scrape, SKIPS cross-run dedup (today's items
# were already marked seen), runs the full chain (notes off), sends to the
# configured recipients + writes vault.
import os, sys, csv, glob
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from email_sender import _load_env
_load_env()
from merge_and_clean import (run as merge_run, reattach_links,
                             enforce_ext_cap, enforce_covered_inclusion)
import claude_reasoning, article_time_enricher, link_resolver
from email_sender import send, save_to_vault
from config import current_max_age_hours, EMAIL_RECIPIENTS

CSV = sorted(glob.glob("output/headlines_*.csv"))[-1]
print("Using CSV:", CSV)
rows = []
with open(CSV, newline="", encoding="utf-8") as f:
    for r in csv.DictReader(f):
        rows.append(dict(r))
gnews  = [r for r in rows if r.get("source_type") == "gnews"]
direct = [r for r in rows if r.get("source_type") == "direct"]
print(f"{len(gnews)} gnews + {len(direct)} direct")

merged, claude_input = merge_run(gnews, direct, apply_cross_run_dedup=False)
print(f"merged {len(merged)}; categorising...")
report, events, notes = claude_reasoning.run(claude_input, write_notes=False)
print("categorise done")

reattach_links(report, merged)
enforce_ext_cap(report, merged, max_ext=2)
enforce_covered_inclusion(report, merged, max_add=20)

all_items = [it for sec, items in report.items()
             if sec != "_raw" and isinstance(items, list) for it in items]
if all_items:
    try:
        link_resolver.resolve_items(all_items)
    except Exception as e:
        print("resolve warn:", e)
    vf = article_time_enricher.verify_freshness(all_items, current_max_age_hours())
    stale = set(t for t in vf["stale_titles"] if t)
    if stale:
        for sec in list(report.keys()):
            if sec == "_raw" or not isinstance(report[sec], list):
                continue
            report[sec] = [it for it in report[sec]
                           if it.get("headline", "") not in stale]
            if not report[sec]:
                del report[sec]
    print(f"freshness: {vf['corrected']} corrected, {len(stale)} stale dropped")

total = sum(len(v) for v in report.values() if isinstance(v, list))
print(f"SENDING {total} items to: {', '.join(EMAIL_RECIPIENTS)}")
n = send(report, events, recipients=EMAIL_RECIPIENTS, notes=notes)
path = save_to_vault(report, events, notes=notes)
print(f"SENT {n} items. Vault: {path}")
