# TMT News Clipping — Project Context & Operating Manual

> **Read this first.** It's the onboarding doc for a fresh Claude Code chat or a
> new person: what this project is, how it works, what's been done, and the rules
> for changing it. This file is auto-loaded by Claude Code when working in this
> folder. Keep it up to date (see "Working conventions" below).

---

## ⚠️ Operating principles (do not violate)

1. **Never make the clipping worse.** Both clippings (this one and H&E) were
   already running *well* before recent changes. Every change must **improve or
   at least hold** output quality vs. before — never regress coverage, add noise,
   or break delivery. If a change *might* worsen things, test first and be ready
   to revert. If quality drops, **roll back and re-evaluate** (git history is the
   safety net).
2. **Test before trusting a risky change.** The owner (Rafael) spot-checks via a
   personal address **rafaelxoliver4@gmail.com**. To send a test there without
   hitting the UBS recipient, call `email_sender.send(report, events,
   recipients=["rafaelxoliver4@gmail.com"], notes=notes)`, or reuse the
   `_run_catchup.py` pattern (recipient override). Never test-send to the real
   `EMAIL_RECIPIENTS`.
3. **Keep this file and GitHub current** — see "Working conventions" at the
   bottom. Every change → update this doc → commit → push.

---

## What this is
An **automated daily news-clipping pipeline for UBS LatAm TMT (Telecom, Media,
Technology) equity research**. It scrapes the day's news, has Claude curate the
*material* items for the covered universe, and emails a formatted clipping to the
analyst team. Runs unattended via Windows Task Scheduler.

- **Owner:** Rafael Oliveira (UBS LatAm equity research).
- **Companion pipeline:** the H&E clipping (Healthcare & Education) — separate repo
  `he-clipping`, near-identical code, **no shared state**. Fixes usually belong in
  **both**; check consistency when changing shared logic.

## Goal
Every weekday, deliver a concise, **material-only** digest of news relevant to the
covered names and their sectors, so the analyst never misses anything important.
Quality over volume — the curator deliberately drops noise.

## Coverage universe (`config.py` → `SECTORS`)
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
1. **Scrape** — `gnews_scraper.py` (Google News RSS, smart keyword×edition routing)
   + `url_scraper.py` (direct sources, RSS-first then HTML fallback; cap 30/source).
2. **Merge/clean** — `merge_and_clean.py`: drop empty titles → **opinion filter**
   (`_is_opinion`) → cross-source + cross-run dedup (24h) → sector assignment →
   relevance scoring → cap 80/sector & 400 total.
3. **Curate** — `claude_reasoning.py` → Claude (Claude Code CLI on the Max plan,
   or the API if `ANTHROPIC_API_KEY` is set) categorises into sector buckets using
   the editorial rules in `wiki_context.py` (`ANALYST_CONTEXT`). **Notes/"UBS's
   take" are disabled** (`write_notes=False`).
4. **Safety nets** — `reattach_links`, `enforce_ext_cap` (≤2 Google-News items),
   `enforce_covered_inclusion` (force-include any covered-name story from ANY
   source, ≤2/ticker, **skipping the company's own website**), then link-resolve →
   `verify_freshness` (reads each article's *real* publish date, drops stale).
   **Empty digests are NOT sent** (skip-empty guard).
5. **Deliver** — `email_sender.py` (Gmail SMTP) + markdown to vault `raw/clippings/`.

**Self-learning:** `topics.py` (scores/decays watch topics); `learn.py` (every 10
runs, refines `ANALYST_CONTEXT` — note: this **modifies `wiki_context.py`** on its
own; commit it so the backup stays current).

## Run it (from INSIDE this folder — `OUTPUT_DIR` is relative)
```
python run_daily.py            # full run + send
python run_daily.py --test     # sample data, no internet, no email
python run_daily.py --skip-scrape   # reuse last CSV
python run_daily.py --no-email      # print JSON, don't send
python run_daily.py --dry-email     # render HTML preview, don't send
```

## Schedule (Windows Task Scheduler, weekdays Mon–Fri, BRT)
**06:40, 16:30, 18:00** (3 runs/day). `StartWhenAvailable=true` (a missed run fires
when the PC next powers on — so the laptop should be on by ~06:40). Task names still
read "07-00"/"16-30"/"18-00 BRT" but the morning one fires **06:40**.

## Secrets & config
- **`.env` (gitignored — NOT in the repo):** `FROM_EMAIL=ibotatom@gmail.com`,
  `EMAIL_APP_PASSWORD=<Gmail app password>`. **Recreate this file to run.**
- `EMAIL_RECIPIENTS` in `config.py`.
- Editorial rules: `wiki_context.py` → `ANALYST_CONTEXT`.

## Change log (most recent first — APPEND here on every change)
- **2026-06-03 (pm)** — **Force-included covered-name items now land in their PROPER
  sector** (e.g. a covered-name story shows under its theme) instead of a catch-all
  "Forced inclusion (covered name)" section that made themes look empty. Mirrors the
  same fix on the H&E pipeline. Touched `merge_and_clean.py`
  (`enforce_covered_inclusion` → `sec_name = _guess_sector(row)`).
- **2026-06-03** — Audit fixes: skip empty-digest send; block company-own-site
  force-include (e.g. "Globant Newsroom" marketing); repointed **Valor Tech** to
  its dedicated pox section feed (de-redundified vs Geral/Tele); committed the
  auto-learn `wiki_context.py`; gitignored stray probe/backup files.
- **2026-06-02** — GitHub backup created (private repo) + this CLAUDE.md. Added
  **opinion filter** (drops "Opinião"/`/colunas/`). Added **fiber-cost keywords**
  to Telecom Brazil (`custo da fibra óptica`, `compartilhamento de postes`, Aneel
  pole access, etc.).
- **2026-06-01** — Valor section feeds 404'd → repointed + added **Valor Impresso**
  (print). Added **Intelbras (INTB) segment keywords** to Hardware (security/CFTV,
  networking/ISP, solar energy, comms — was only matched by name before).
- **2026-05-28** — Stale-date fix (read real `data_publicacao`/JSON-LD
  `datePublished`, fetch window 220 KB, resolve gnews links before freshness; TMT
  also gained the `verify_freshness` stale-drop it lacked). Notes/"UBS's take"
  disabled. Force-include extended to all sources + per-ticker cap (2). Morning
  run moved to **06:40**.

## Known issues / fragilities
- **Email send has no retry** — a transient Gmail "connection closed" loses the
  run. *Candidate fix: retry-with-backoff in `email_sender.send()`.*
- **Claude CLI categorisation can time out** (1500s) and kill the run (happened
  once); recovers on a manual re-run (`_run_catchup.py`).
- **Morning runs are the overnight delta** (cross-run dedup) → can be thin on quiet
  nights. Monday uses a 72h weekend look-back.
- **Minor:** "Valor Tele" + "Valor Geral" still both point at the general feed
  (telecom section feed errored when checked); Intelbras/fiber keywords are broad
  by design — watch for noise.
- **Auto-learn rewrites `wiki_context.py`** periodically — remember to commit it.
- **Consistency note:** TMT skips cross-run dedup only in `--test`; H&E also skips
  it in `--no-email`/`--dry-email`. Align if a TMT preview run pollutes dedup memory.

## Gotchas
- OneDrive paths have spaces/accents/& — always run scripts **from this folder**;
  in tooling, prefer the Read tool with full paths (Glob/Bash globbing fails here).
- No `ANTHROPIC_API_KEY` → uses the Claude Code CLI (`claude.exe`).
- `git history is the source of truth` for rollbacks (`*_backup_*.py` are gitignored).

## 🔁 Working conventions (KEEP THESE)
**After ANY change to this pipeline, ALWAYS:**
1. **Update this `CLAUDE.md`** — add a dated line to the Change log and update any
   section that's now stale (sources, schedule, known issues, etc.).
2. **Commit + push to GitHub** so the backup and context stay current:
   ```
   git add -A && git commit -m "what changed" && git push
   ```
3. Verify it still **compiles** and (for risky changes) **test-send to
   rafaelxoliver4@gmail.com** before trusting it.

This self-maintenance rule is itself part of the doc — do not drop it.

## Backup / version control
Private GitHub repo: **https://github.com/rafaelxoliver4-art/tmt-clipping** (branch `master`).

**Moving to a new PC?** See **`MIGRATION.md`** — step-by-step rebuild (Python, deps,
`.env`, importing the scheduled tasks). The Windows task definitions are saved as XML
in **`scheduler/`** (3 clipping + 2 Anatel), dependencies in **`requirements.txt`**.
The only secret (`.env`, Gmail app password) is gitignored — copy it from the old PC
by hand.
