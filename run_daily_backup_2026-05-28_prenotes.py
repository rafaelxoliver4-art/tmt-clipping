# run_daily.py — TMT News Scraper: full end-to-end pipeline
#
# Usage:
#   python run_daily.py                # full run — scrape, curate, email
#   python run_daily.py --test         # sample data, no internet, no email
#   python run_daily.py --skip-scrape  # reuse last CSV, skip scraping
#   python run_daily.py --no-email     # print the JSON digest, don't send
#   python run_daily.py --no-events    # skip events fetch (faster)
#   python run_daily.py --dry-email    # render HTML preview file, don't send

import sys
import csv
import os
from datetime import datetime
from config import LOCAL_TZ, OUTPUT_DIR

# Force UTF-8 stdout/stderr so Portuguese error chars don't crash on Windows cp1252
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Load .env once at startup so ANTHROPIC_API_KEY, FROM_EMAIL, EMAIL_APP_PASSWORD
# are available to every downstream module via os.environ.
from email_sender import _load_env as _load_dotenv
_load_dotenv()

TEST_MODE    = "--test"        in sys.argv
SKIP_SCRAPE  = "--skip-scrape" in sys.argv
NO_EMAIL     = "--no-email"    in sys.argv
NO_EVENTS    = "--no-events"   in sys.argv
NO_NOTES     = "--no-notes"    in sys.argv   # skip note writing (faster debug runs)
DRY_EMAIL    = "--dry-email"   in sys.argv

def banner(msg):
    print(f"\n{'-'*60}")
    print(f"  {msg}")
    print(f"{'-'*60}")

def save_csv(rows, path):
    os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
    if not rows:
        print("  No rows to save.")
        return
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "title", "source", "link", "published_local",
            "keyword", "edition_lang", "edition_country", "source_type",
        ])
        writer.writeheader()
        for r in rows:
            writer.writerow({k: r.get(k, "") for k in writer.fieldnames})

def load_csv(path):
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(dict(row))
    return rows

def _latest_csv():
    """Return the most recent headlines CSV in OUTPUT_DIR, or None."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    files = [
        f for f in os.listdir(OUTPUT_DIR)
        if f.startswith("headlines_") and f.endswith(".csv")
    ]
    if not files:
        return None
    files.sort(reverse=True)
    return os.path.join(OUTPUT_DIR, files[0])


# ── Sample data for --test ────────────────────────────────────────────────────
SAMPLE_ROWS = [
    {"title": "TOTVS conclui aquisicao da Linx por R$7 bilhoes",
     "source": "Valor Economico", "link": "https://valor.globo.com", "keyword": "TOTVS",
     "published_local": datetime.now(LOCAL_TZ).strftime("%Y-%m-%d"),
     "edition_lang": "pt-BR", "edition_country": "BR", "source_type": "gnews"},
    {"title": "TCS is asking staff to use AI even if it hits revenues: CEO",
     "source": "Economic Times", "link": "", "keyword": "TCS",
     "published_local": datetime.now(LOCAL_TZ).strftime("%Y-%m-%d"),
     "edition_lang": "en", "edition_country": "US", "source_type": "gnews"},
    {"title": "AMX reporta caida de ingresos en Mexico en el 4T24",
     "source": "El Economista", "link": "", "keyword": "AMX",
     "published_local": datetime.now(LOCAL_TZ).strftime("%Y-%m-%d"),
     "edition_lang": "es-MX", "edition_country": "MX", "source_type": "gnews"},
    {"title": "Anatel aprova novos criterios para licitacao de espectro 5G",
     "source": "Teletime", "link": "", "keyword": "VIVT3",
     "published_local": datetime.now(LOCAL_TZ).strftime("%Y-%m-%d"),
     "edition_lang": "pt-BR", "edition_country": "BR", "source_type": "direct"},
    {"title": "Globant anuncia expansion de operaciones en Mexico",
     "source": "Expansion", "link": "", "keyword": "Globant",
     "published_local": datetime.now(LOCAL_TZ).strftime("%Y-%m-%d"),
     "edition_lang": "es-MX", "edition_country": "MX", "source_type": "direct"},
    {"title": "OpenAI raises $110B in one of the largest private rounds ever",
     "source": "The Information", "link": "", "keyword": "OpenAI",
     "published_local": datetime.now(LOCAL_TZ).strftime("%Y-%m-%d"),
     "edition_lang": "en", "edition_country": "US", "source_type": "direct"},
    {"title": "Netflix backs out of bid for Warner Bros. Discovery",
     "source": "Reuters", "link": "", "keyword": "Netflix",
     "published_local": datetime.now(LOCAL_TZ).strftime("%Y-%m-%d"),
     "edition_lang": "en", "edition_country": "US", "source_type": "direct"},
    {"title": "SAP unveils new AI-powered ERP features at Sapphire 2025",
     "source": "CIO", "link": "", "keyword": "SAP",
     "published_local": datetime.now(LOCAL_TZ).strftime("%Y-%m-%d"),
     "edition_lang": "en", "edition_country": "US", "source_type": "direct"},
    {"title": "Governo derruba alta de imposto para smartphones e eletronicos",
     "source": "Estadao", "link": "", "keyword": "POSI",
     "published_local": datetime.now(LOCAL_TZ).strftime("%Y-%m-%d"),
     "edition_lang": "pt-BR", "edition_country": "BR", "source_type": "direct"},
    {"title": "Mercado Libre reports record GMV in Q4 2024",
     "source": "Brazil Journal", "link": "", "keyword": "MELI",
     "published_local": datetime.now(LOCAL_TZ).strftime("%Y-%m-%d"),
     "edition_lang": "en", "edition_country": "US", "source_type": "direct"},
]


def main():
    start = datetime.now(LOCAL_TZ)

    # Lookback window — resolved automatically by config.current_max_age_hours()
    # at every filter call. 24h normally, 72h on Monday to catch Fri PM + weekend.
    from config import current_max_age_hours, current_gnews_when
    active_age = current_max_age_hours()
    active_when = current_gnews_when()

    banner(f"TMT News Scraper  —  {start.strftime('%Y-%m-%d %H:%M %Z')}")
    print(f"  Lookback window: {active_age}h  (Google News when: {active_when})"
          + ("   ← Monday extended to 72h" if active_age == 72 else ""))

    gnews_rows  = []
    direct_rows = []
    today_str   = start.strftime("%Y-%m-%d")
    csv_path    = os.path.join(OUTPUT_DIR, f"headlines_{today_str}.csv")

    # ── Step 1 & 2: Scraping ─────────────────────────────────────────────────
    if TEST_MODE:
        print("\n[TEST MODE] Using sample headlines — no internet needed\n")
        gnews_rows  = SAMPLE_ROWS[:5]
        direct_rows = SAMPLE_ROWS[5:]

    elif SKIP_SCRAPE:
        existing = _latest_csv()
        if not existing:
            print("  [ERROR] No cached CSV found. Run without --skip-scrape first.")
            sys.exit(1)
        print(f"\n[--skip-scrape] Loading headlines from: {existing}")
        all_cached = load_csv(existing)
        gnews_rows  = [r for r in all_cached if r.get("source_type") == "gnews"]
        direct_rows = [r for r in all_cached if r.get("source_type") == "direct"]
        print(f"  -> {len(gnews_rows)} gnews + {len(direct_rows)} direct = {len(all_cached)} total")

    else:
        print("\n[Step 1/2]  Scraping Google News RSS...")
        try:
            from gnews_scraper import run as gnews_run
            gnews_rows = gnews_run()
            print(f"  -> {len(gnews_rows)} headlines from Google News")
        except Exception as e:
            print(f"  [ERROR] Google News: {e}")

        print("\n[Step 2/2]  Scraping direct source URLs...")
        try:
            from url_scraper import run as url_run
            direct_rows = url_run(existing_headlines=gnews_rows)
            print(f"  -> {len(direct_rows)} headlines from direct sources")
        except Exception as e:
            print(f"  [ERROR] Direct scrape: {e}")

        all_rows = gnews_rows + direct_rows
        if not all_rows:
            print("\n  No headlines found. Try --test to verify setup.")
            sys.exit(1)

        save_csv(all_rows, csv_path)
        print(f"\n  CSV saved: {os.path.abspath(csv_path)}")

    all_rows = gnews_rows + direct_rows
    if not all_rows:
        print("\n  No headlines to process.")
        sys.exit(1)

    print(f"\n  Total raw headlines: {len(all_rows)}")

    # ── Step 3: Merge, dedup, assign sectors ─────────────────────────────────
    print("\n[Step 3/5]  Merging and cleaning headlines...")
    try:
        from merge_and_clean import run as merge_run
        # In TEST_MODE: skip cross-run dedup so sample headlines aren't dropped
        # by previous test runs and don't pollute the seen_headlines memory.
        merged_rows, claude_input = merge_run(
            gnews_rows, direct_rows,
            apply_cross_run_dedup=not TEST_MODE,
        )
        print(f"  -> {len(merged_rows)} headlines after dedup and capping")
    except Exception as e:
        print(f"  [ERROR] Merge: {e}")
        sys.exit(1)

    if not claude_input.strip():
        print("  Nothing to process after filtering. Exiting.")
        sys.exit(1)

    # ── Step 4: Claude reasoning ──────────────────────────────────────────────
    # Three modes:
    #   (a) ANTHROPIC_API_KEY set → call Claude API directly (billed per token)
    #   (b) No API key            → Claude Code CLI using Max plan subscription
    #   (c) --no-email flag       → write claude_input file and exit (manual curation)
    api_key  = os.environ.get("ANTHROPIC_API_KEY", "")
    ci_path  = os.path.join(OUTPUT_DIR, f"claude_input_{today_str}.txt")

    # Always write the input file so it can be inspected / replayed later
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(ci_path, "w", encoding="utf-8") as f:
        f.write(claude_input)
    print(f"\n  {len(merged_rows)} headlines written to:\n    {os.path.abspath(ci_path)}")

    print("\n[Step 4/5]  Running Claude reasoning...")
    try:
        from claude_reasoning import run as claude_run
        write_notes = not (NO_NOTES or NO_EMAIL)  # skip notes for fast/debug runs
        if NO_EVENTS:
            from claude_reasoning import categorise_headlines, log_run
            report = categorise_headlines(claude_input)
            events = []
            notes  = []
            print("  Events skipped (--no-events)")
            if write_notes:
                from claude_reasoning import write_top_notes
                print("  Claude: writing top analytical notes...", end="", flush=True)
                notes = write_top_notes(report)
                print(f" done ({len(notes)} note{'s' if len(notes) != 1 else ''})")
            log_run(report, notes)
        else:
            report, events, notes = claude_run(claude_input, write_notes=write_notes)
    except Exception as e:
        print(f"  [ERROR] Claude: {e}")
        sys.exit(1)

    # Re-attach links (and source_url) to curator output by headline match.
    # Claude only returns {ticker, headline, source, date} — code owns links.
    try:
        from merge_and_clean import reattach_links, enforce_ext_cap
        rc = reattach_links(report, merged_rows)
        total = rc["matched"] + rc["headline_only"] + rc["unmatched"]
        if total:
            print(f"  Link re-attach: {rc['matched']} exact, "
                  f"{rc['headline_only']} headline-only, "
                  f"{rc['unmatched']} unmatched (of {total} items)")
        # Enforce the "max 5 EXT items" rule as a safety net in case the
        # curator overshoots the prompt directive.
        ec = enforce_ext_cap(report, merged_rows, max_ext=2)
        print(f"  Source mix: {ec['direct_kept']} DIRECT, "
              f"{ec['ext_kept']} EXT kept, "
              f"{ec['ext_dropped']} EXT dropped (cap=2)")
    except Exception as e:
        print(f"  [WARN] link re-attach / ext cap failed: {e}")

    # Server-side safety net: force-include any DIRECT-source row whose title
    # contains a covered ticker/company name and was missed by the curator.
    try:
        from merge_and_clean import enforce_covered_inclusion
        ci = enforce_covered_inclusion(report, merged_rows, max_add=20)
        if ci["added"] or ci["already_present"]:
            print(f"  Covered-name guarantee: {ci['added']} force-added, "
                  f"{ci['already_present']} already present")
    except Exception as e:
        print(f"  [WARN] covered-name guarantee failed: {e}")

    # Freshness verification + article-time enrichment (2026-05-28):
    # Fetch each curated item's article page to (a) correct the displayed time
    # to the precise value and (b) DROP items whose real pubdate is older than
    # the lookback window. Fixes the stale-leak bug where Google News served
    # weeks-old articles with a fresh-looking RSS pubDate (e.g. a 2-month-old
    # Estadão piece dated "today"). Google News links are resolved to the real
    # publisher URL first, so the check can actually read the article's date.
    try:
        import article_time_enricher
        from config import current_max_age_hours
        all_items = [it for sec, items in report.items()
                     if sec != "_raw" and isinstance(items, list)
                     for it in items]
        if all_items:
            # Resolve Google News redirect URLs to the real publisher URL FIRST,
            # so the freshness check can fetch the actual article page and read
            # its true publish date. Without this, gnews items keep their
            # news.google.com link and verify_freshness skips them. Cached, so
            # the later email-stage resolve is a no-op cache hit.
            try:
                import link_resolver
                link_resolver.resolve_items(all_items)
            except Exception as e:
                print(f"  [WARN] pre-freshness link resolution failed: {e}")
            vf = article_time_enricher.verify_freshness(
                all_items, current_max_age_hours())
            stale = set(t for t in vf["stale_titles"] if t)
            if stale:
                for sec in list(report.keys()):
                    if sec == "_raw" or not isinstance(report[sec], list):
                        continue
                    report[sec] = [it for it in report[sec]
                                   if it.get("headline", "") not in stale]
                    if not report[sec]:
                        del report[sec]
            print(f"  Freshness check: {vf['corrected']} times corrected, "
                  f"{len(stale)} stale dropped (of {vf['checked']} checked)")
    except Exception as e:
        print(f"  [WARN] freshness verification failed: {e}")

    if NO_EMAIL:
        import json
        print("\n── JSON Report ──────────────────────────────────────────")
        print(json.dumps(report, indent=2, ensure_ascii=False))
        if events:
            print("\n── Events ───────────────────────────────────────────────")
            print(json.dumps(events, indent=2))
        if notes:
            print(f"\n── Notes ({len(notes)}) ──────────────────────────────────────")
            for i, n in enumerate(notes, 1):
                print(f"\n--- Note {i} ---\n{n[:500]}...")
        elapsed = (datetime.now(LOCAL_TZ) - start).total_seconds()
        banner(f"Done in {elapsed:.0f}s  (--no-email, nothing sent)")
        return

    # ── Step 5: Send email ────────────────────────────────────────────────────
    if DRY_EMAIL:
        print("\n[Step 5/5]  Rendering email preview (dry run — no send)...")
        try:
            from email_sender import render_html
            html = render_html(report, events, notes=notes)
            preview_path = os.path.join(OUTPUT_DIR, f"email_preview_{today_str}.html")
            os.makedirs(OUTPUT_DIR, exist_ok=True)
            with open(preview_path, "w", encoding="utf-8") as f:
                f.write(html)
            print(f"  -> HTML preview: {os.path.abspath(preview_path)}")
            if notes:
                print(f"  -> {len(notes)} analytical note(s) included")
        except Exception as e:
            print(f"  [ERROR] Email preview: {e}")
            sys.exit(1)
    else:
        print("\n[Step 5/5]  Sending email...")
        try:
            from email_sender import run as email_run
            from config import EMAIL_RECIPIENTS
            count = email_run(report, events, notes=notes)
            print(f"  -> Sent {count} items + {len(notes)} note(s) to: {', '.join(EMAIL_RECIPIENTS)}")
        except Exception as e:
            print(f"  [ERROR] Email send: {e}")
            sys.exit(1)

        # ── Closing the loop: save clipping to Obsidian vault as markdown ──
        # The News Writer project consumes this directly to draft the daily.
        try:
            from email_sender import save_to_vault
            path = save_to_vault(report, events, notes=notes)
            if path:
                print(f"  -> Vault: {path}")
        except Exception as e:
            print(f"  [WARN] Vault write skipped: {e}")

    # ── Autonomous topic learning ────────────────────────────────────────────
    # Reinforce topics that matched today's clipping/notes; refresh from vault
    # activity every N runs. Runs entirely without user intervention.
    if not TEST_MODE:
        try:
            import topics
            hits  = topics.record_clipping_hits(report)
            promo = topics.record_note_promotions(notes or [])
            topics.increment_run_counter()
            if hits or promo:
                print(f"\n[Topics] Reinforced — {hits} clipping hit(s), {promo} note promotion(s)")

            # Highest-weight signal: Rafael's actual published notes from the
            # Observer file. Only credits notes appended since last run.
            obs_credited, obs_topics = topics.reinforce_from_observer()
            if obs_credited:
                print(f"[Topics] Observer reinforcement — {obs_credited} new published "
                      f"note(s) credited to {obs_topics} topic(s) (+10 each)")

            if topics.should_refresh():
                print(f"[Topics] Refreshing from News Writer vault activity...")
                from learn import (load_vault_conversations, extract_auto_watchlist,
                                   _read_current_context)
                vault_convs = load_vault_conversations(days=30)
                current_ctx = _read_current_context()
                extracted   = extract_auto_watchlist(vault_convs, current_ctx)
                if extracted:
                    added, reinforced = topics.merge_extracted_topics(extracted)
                    pruned, remaining = topics.post_refresh_maintenance()
                    print(f"  -> +{added} new, {reinforced} reinforced, "
                          f"{pruned} decayed out, {remaining} active")
                else:
                    print(f"  -> No new topics extracted this cycle")
        except Exception as e:
            print(f"  [WARN] Topic learning skipped: {e}")

    # ── Done ──────────────────────────────────────────────────────────────────
    elapsed = (datetime.now(LOCAL_TZ) - start).total_seconds()
    banner(f"Done in {elapsed:.0f}s")

    sector_counts = {k: len(v) for k, v in report.items() if isinstance(v, list)}
    total_items = sum(sector_counts.values())
    print(f"\n  Digest: {total_items} items across {sum(1 for c in sector_counts.values() if c)} sectors")
    for sec, count in sector_counts.items():
        if count:
            print(f"    {sec:<30} {count} headlines")
    if not SKIP_SCRAPE and not TEST_MODE:
        print(f"\n  CSV:  {os.path.abspath(csv_path)}")

    # ── Auto-learn every 10th run ─────────────────────────────────────────────
    # Every time the pipeline hits a 10-run milestone it reads the full
    # editorial context (NEWS_WRITER_CONTEXT.md, Obsidian vault conversations,
    # Claude Code sessions, run log) and proposes refinements to wiki_context.py.
    # Skipped in test/no-email modes to keep fast debug cycles clean.
    if not TEST_MODE and not NO_EMAIL:
        try:
            from claude_reasoning import _count_log_runs
            run_count = _count_log_runs()
            if run_count > 0 and run_count % 10 == 0:
                print(f"\n[Auto-learn] Run #{run_count} — milestone reached, improving ANALYST_CONTEXT...")
                from learn import run_learn_cycle
                updated = run_learn_cycle(auto=True)
                if updated:
                    print("  -> ANALYST_CONTEXT updated ✓")
                else:
                    print("  -> No changes needed.")
        except Exception as e:
            print(f"  [WARN] Auto-learn skipped: {e}")

    print()


if __name__ == "__main__":
    main()
