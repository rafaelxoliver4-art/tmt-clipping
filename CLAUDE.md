# TMT News Clipping — Project Context

> Onboarding doc for a fresh chat or a new person. This file is auto-loaded by
> Claude Code when working in this folder. Read it first.

## What this is
An **automated daily news-clipping pipeline for UBS LatAm TMT (Telecom, Media,
Technology) equity research**. It scrapes the day's news, has Claude curate the
*material* items for the covered universe, and emails a formatted clipping to
the analyst team. Runs unattended via Windows Task Scheduler.

- **Owner:** Rafael Oliveira (UBS LatAm equity research).
- **Companion pipeline:** the H&E clipping (Healthcare & Education) — separate
  repo `he-clipping`, near-identical code, **no shared state**.

## Goal
Every weekday, deliver a concise, **material-only** digest of news relevant to
the covered names and their sectors, so the analyst never misses anything
important. Quality over volume — the curator deliberately drops noise.

## Coverage universe (see `config.py` → `SECTORS`)
| Sector | Covered tickers |
|---|---|
| Telecom LatAm & World | AMX, TIGO, TEO, Televisa (+ peers) |
| Telecom Brazil | TEF-BZ (VIVT3), TIM (TIMS3), BRISANET, DESK |
| IT Services | GLOB (Globant), CINT, INTB, CI&T (+ ACN/COG/INFY/TCS…) |
| Software & AI | TOTVS, LWSA, VTEX (+ OpenAI/Anthropic/SAP…) |
| Ecommerce | VTEX, LWSA, MLAS |
| Hardware | POSI, **INTB (Intelbras)**, MLAS |
| Streaming | (context only — Netflix/Disney/Spotify) |

## How it works — `run_daily.py` orchestrates 5 steps
1. **Scrape** — `gnews_scraper.py` (Google News RSS, ~270 keyword×edition
   queries) + `url_scraper.py` (~70 direct sources, RSS-first, HTML fallback).
2. **Merge/clean** — `merge_and_clean.py`: cross-source + cross-run dedup (24h),
   sector assignment, relevance scoring, cap 80/sector & 400 total.
3. **Curate** — `claude_reasoning.py` → Claude (Claude Code CLI on the Max plan,
   or the API if `ANTHROPIC_API_KEY` is set) categorises into sector buckets
   using the editorial rules in `wiki_context.py` (`ANALYST_CONTEXT`).
4. **Safety nets** — `reattach_links`, `enforce_ext_cap` (≤2 Google-News items),
   `enforce_covered_inclusion` (force-include any covered-name story from ANY
   source, ≤2/ticker), then link-resolve + `verify_freshness` (drops stale items
   by reading each article's *real* publish date).
5. **Deliver** — `email_sender.py` (Gmail SMTP) + writes markdown to the Obsidian
   vault `raw/clippings/`.

**Self-learning:** `topics.py` (scores/decays watch topics) and `learn.py`
(every 10 runs, refines `ANALYST_CONTEXT` from Rafael's published notes + vault).

## Run it
From **inside this folder** (cwd matters — `OUTPUT_DIR` is relative):
```
python run_daily.py            # full run + send to team
python run_daily.py --test     # sample data, no internet, no email
python run_daily.py --skip-scrape   # reuse last CSV
python run_daily.py --no-email      # print JSON, don't send
python run_daily.py --dry-email     # render HTML preview, don't send
```

## Schedule (Windows Task Scheduler, weekdays Mon–Fri, BRT)
**06:40, 16:30, 18:00.** `StartWhenAvailable=true` (a missed run fires when the
PC next powers on). The laptop must be awake at run time. Task names:
"TMT News Clipping 07-00 / 16-30 / 18-00 BRT" (the "07-00" task now fires 06:40).

## Secrets & config
- **`.env` (gitignored — NOT in this repo):** `FROM_EMAIL=ibotatom@gmail.com`,
  `EMAIL_APP_PASSWORD=<Gmail app password>`. **Recreate this file to run.**
- `EMAIL_RECIPIENTS` in `config.py`.
- Editorial rules / coverage memory: `wiki_context.py` → `ANALYST_CONTEXT`.

## State & recent changes (as of 2026-06-02)
- Analytical "UBS's take" notes **disabled** (`write_notes = False` in run_daily).
- **Stale-date fix:** reads the real publish date (`data_publicacao` / JSON-LD
  `datePublished`) before the freshness gate; drops Google-News-misdated old items.
- **Covered-name force-include extended to all sources** (incl. Google News), ≤2/ticker.
- **Valor feeds repointed** to the live `valor.globo.com/rss/valor` + added
  "Valor Impresso" (print) — the old `arc/outboundfeeds` RSS now 404s.
- **Intelbras (INTB) segment keywords added** — security/CFTV, networking/ISP,
  solar energy, comms (it was only matched by name before).

## Known fragilities (no auto-recovery yet — candidates for hardening)
- **Email send has no retry** — a transient Gmail "connection closed" loses the
  whole run. Fix: retry-with-backoff in `email_sender.send()`.
- **Claude CLI categorisation can time out** (1500s) and kill the run; recovers
  on a manual re-run.
- **Sends even an empty (0-item) digest.** Fix: skip send when 0 items.
- **Morning runs (Tue–Fri) are just the overnight delta** (cross-run dedup), so
  they can be thin/empty on quiet nights. Mondays use a 72h weekend look-back.

## Gotchas
- OneDrive paths have spaces/accents — always run scripts **from this folder**.
- No `ANTHROPIC_API_KEY` → uses the Claude Code CLI (`claude.exe`).
- `*_backup_2026-*.py` are pre-git manual backups; **git history is now the
  source of truth** for rollbacks.

## Backup / version control
Private GitHub repo: **https://github.com/rafaelxoliver4-art/tmt-clipping**
Save changes with:
```
git add -A && git commit -m "what changed" && git push
```
