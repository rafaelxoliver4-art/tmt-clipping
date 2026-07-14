# TMT News Clipping — Project Context & Operating Manual

> **Read this first.** It's the onboarding doc for a fresh Claude Code chat or a
> new person: what this project is, how it works, what's been done, and the rules
> for changing it. This file is auto-loaded by Claude Code when working in this
> folder. Keep it up to date (see "Working conventions" below).

---

## 📍 Current status (2026-07-06) — read this first
- **#3 failure mode (FIXED 2026-07-02/06) — PC asleep / network not ready / run killed.**
  Layers now in place: **(a)** `run_daily.py` waits up to 10 min for the network before
  scraping (a wake-up run no longer dies on DNS) **(b)** a 0-headline scrape or failed
  email send **alerts loudly** (email + flag) **(c)** tasks auto-restart 3×/5 min on
  failure **(d)** a running pipeline **holds the PC awake** until it finishes
  (`SetThreadExecutionState`) **(e)** **DELIVERY WATCHDOG** — `watchdog.py` + 3 tasks
  (08:15 / 17:20 / 18:50 weekdays) check `output/last_delivery.json`; if a slot passed
  with no digest, the watchdog re-runs the pipeline itself (grace-waits 12 min first to
  avoid duplicating an in-flight catch-up run). **Every slot ends in a digest or an
  alert — never silence.** NOTE: `WakeToRun` was tried (07-02) and **REVERTED** (07-06):
  an unattended wake goes back to sleep ~2 min later and KILLED the 16:30 run mid-scrape
  (result 0x40010004, no alert possible). Missed slots are instead caught up on wake
  (`StartWhenAvailable`) + guaranteed by the watchdog. Do NOT re-enable WakeToRun.
- **Running FREE** on the Max-plan Claude CLI — there is **no `ANTHROPIC_API_KEY`**
  in `.env` (if one is present, the curator switches to the paid API at ~$0.15/run;
  remove it to go back to free).
- **Scheduled** weekdays BRT **06:40 / 16:30 / 18:00** (Windows Task Scheduler, enabled).
- **⚠️ #1 failure mode — the CLI login expires.** Every few days the Max-plan token can
  lapse → the curator gets `401 Invalid authentication credentials` → the run **aborts,
  emails an `[ACTION NEEDED]` alert (to `config.py → ALERT_EMAIL`), writes
  `CLIPPING_FAILED.txt`, and sends NO digest** (never filler). **Fix: open a terminal,
  run `claude`, type `/login`, sign in with the Max account.** Full guide in
  **`ALERTS_AND_HEALTH.md`**. (This is what caused the June 2026 "almost no important
  news" clippings — it was a silent auth expiry, now made loud.)
- **#2 failure mode (FIXED 2026-06-26) — curator loaded `CLAUDE.md` and editorialised.**
  `claude.exe` ran in this folder and auto-loaded this very file as memory, so the model
  began commenting on the payload (*"...the silent-failure pattern your CLAUDE.md warns
  about"*) instead of returning JSON → curation crashed (and the alert fired correctly).
  **Fix:** the curator CLI now runs with **`--safe-mode`** (disables CLAUDE.md / skills /
  plugins / hooks / MCP, but keeps free Max OAuth — unlike `--simple`, which would force
  `ANTHROPIC_API_KEY`) in `claude_reasoning.py → _call_claude_cli`. **Do not remove that flag.**
- **Recipients (rule, 2026-06-26):** PRODUCTION emails → **work address only**
  (`rafael.oliveira@ubs.com`); TEST emails → **personal gmail only**
  (`rafaelxoliver4@gmail.com`); **never both in one list.** Applies to `EMAIL_RECIPIENTS`
  AND `ALERT_EMAIL` here (and to the H&E + Anatel pipelines).
- **Hardened:** curation failure now fails LOUDLY (alert + no email) instead of silently
  shipping covered-name filler; **transient curator errors** (e.g. `API Error: Stream idle
  timeout`) are now **retried up to 4× with backoff** and only a genuine AUTH error aborts
  the run (2026-06-26 — a transient stall used to abort because the message contained "api
  error"); cross-run dedup commits "seen" only after a successful send.
- **Optional TODO** (quality polish, not blocking): tighten cross-run dedup key matching;
  the broader coverage fixes from the 2026-06-24 pipeline audit (see change log).
- **Backed up:** GitHub `tmt-clipping` + Google Drive `Clipping-Pipelines-Backup`.
- **Quality benchmark:** `benchmarks/reference_clippings.md` (analyst-approved digests to
  cross-check automated runs against).

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
- **2026-07-14** — **Benchmark cross-check (4 analyst clippings, 07/07–14/07) → funnel
  + curator + query fixes.** A 5-agent audit matched 85 analyst-picked items against
  the pipeline's 3 layers: 36 delivered, 16 not scraped, 20 lost in MERGE, 12 curator
  skips. Fixes, all additive: **(a) cap_per_sector rebuilt** — per-source cap
  (12/source/sector, kills Ookla-boilerplate monopolies), guaranteed 12 EXT (gnews)
  slots per sector + ≥60 globally (EXT starvation was the #1 loss: direct rows filled
  sector caps before covered-ticker gnews stories were even considered), 2-pass
  backfill so no slot is wasted; **(b) Monday-aware caps** — 72h-lookback runs now get
  600 total / 100 per sector (13 of the 20 merge losses were Mondays;
  `config.current_max_total()/current_max_per_sector()`); **(c) new queries** —
  Paraguay (Conatel/5G), ClaroVTR (+AMX alias), CFE Internet, Osiptel, Fitch Millicom,
  5G Advanced, India IT workforce beat (hiring/headcount/salary/GCC), operadora Oi,
  Brasil TecPar, Amazon Now Brasil — with _ES/_PT marker routing so they hit the right
  Google News edition; **(d) curator materiality additions** — frontier-AI vendor
  PRODUCT/PRICING/DISTRIBUTION moves; regulator/research DATA releases (max 1-2/digest);
  spectrum implementation + competitor capacity grants; credit-rating actions; plus
  rules 10-11: sector tags are heuristics (re-file mis-bucketed items), dedupe by EVENT
  not company. Validated on 07-14's cached scrape: previously-missed TOTVS/Exame and
  TV 3.0 stories now reach the curator; Anthropic-India pricing now picked. Benchmarks
  appended to `benchmarks/reference_clippings.md`. EXT≤5 digest cap and
  MAX_DIGEST_ITEMS=60 unchanged. **(e) force-add reverted to DIRECT-only** — with
  gnews now guaranteed curator slots, the 2026-05-28 all-sources force-add became a
  junk injector (alias collisions: TASE:AMX=Automax, "Posi Metallic" brake pads,
  Globant eSports, CINT price-action spam force-added straight into the digest,
  bypassing curator judgment AND the EXT cap). Validation v2 caught it; v3 confirmed
  clean (force-adds 16→5, junk gone). **(f)** ALWAYS OMIT additions: price-action/
  technical-analysis listicles; routine "fora do ar" status-tracker blurbs.
- **2026-07-06** — **DELIVERY WATCHDOG + WakeToRun reverted.** The 16:30 run was
  KILLED mid-scrape (0x40010004): WakeToRun woke the sleeping PC at 16:30, the
  unattended-wake policy put it back to sleep ~2 min later, and the frozen process
  was terminated — no digest, and no alert possible from a dead process (the 07:00
  slot that day was fine: caught up at 07:10 on user wake and delivered). Changes:
  (a) WakeToRun REVERTED on all 3 tasks — catch-up-on-wake (`StartWhenAvailable`)
  is the model, as before; (b) `run_daily.py` holds the PC awake while running
  (`SetThreadExecutionState ES_SYSTEM_REQUIRED`); (c) after every successful send it
  writes `output/last_delivery.json`; (d) NEW `watchdog.py` + 3 tasks (08:15/17:20/
  18:50 weekdays, `--since 06:30/16:20/17:50`): if a slot passed with no delivery
  stamp, grace-wait 12 min (in-flight catch-up run), then re-run the pipeline —
  recovery failure triggers run_daily's own alert; (e) email-send failure now also
  fires `_alert_failure`. Guarantee: every slot → digest or [ACTION NEEDED] alert.
  Scheduler XMLs re-exported (incl. the 3 watchdogs).
- **2026-07-02** — **PC-wake hardening + curator BRAIN repair.** (a) The 06:40 run
  fired as the PC woke, DNS wasn't up → all 284 sources `getaddrinfo failed` → 0
  headlines, digest lost, no alert. Fixes: `run_daily.py` waits up to 10 min for the
  network before scraping; a 0-headline scrape now alerts + flags (was silent); the
  3 tasks got `WakeToRun` (AC wake timers confirmed on) + auto-restart 3×/5 min;
  `scheduler/` XMLs re-exported. PC must be plugged in + asleep (not shut down).
  User chose to stay on the free local setup (cloud options declined). (b) Discovered
  `wiki_context.py`'s ANALYST_CONTEXT had been overwritten with a literal 401 error
  string during the June auth outage (committed at 2ce6f50) and self-recovered on
  07-01 with a leaked reasoning preamble. Cleaned it (starts at the `## UBS LatAm TMT`
  anchor; all learned content preserved, 60k chars) and added `learn._validate_new_context`:
  auto-trims preambles, rejects error strings and >30% shrinkage — corruption of the
  curator's context can no longer be written to disk.
- **2026-06-26** — **Curator ran with `--safe-mode`; retry split auth vs transient;
  recipients rule.** (a) NEW failure mode: `claude.exe` auto-loaded this very CLAUDE.md
  as memory and editorialised about the payload instead of returning JSON → curation
  crashed (alert fired correctly). Fix: `_call_claude_cli` passes `--safe-mode`
  (disables CLAUDE.md/skills/plugins/hooks/MCP but keeps free Max OAuth — do NOT use
  `--simple`, it forces an API key). Verified on the real failed input: 25 items, valid
  JSON. (b) `categorise_headlines` retries transient API/stream errors (4 attempts,
  5/10/15s backoff) and aborts fast only on real auth failures — a "Stream idle
  timeout" no longer kills a run. (c) RECIPIENTS RULE: production → work address only;
  tests → personal gmail only; NEVER both in one list (`EMAIL_RECIPIENTS` + `ALERT_EMAIL`
  here, and the H&E + Anatel pipelines).
- **2026-06-25** — **Failure ALERTS so a broken run is never silent.** When curation
  can't run (almost always: the Claude CLI login expired → 401), the pipeline now
  (a) emails an `[ACTION NEEDED]` alert to `config.py → ALERT_EMAIL`, (b) writes a
  `CLIPPING_FAILED.txt` flag in the project root (auto-deleted on next success), and
  (c) sends NO digest (never filler). New `email_sender.send_alert()`; `run_daily`
  `_alert_failure()` / `_clear_failure_flag()`. See `ALERTS_AND_HEALTH.md`. Also:
  re-authenticated the CLI (`claude /login`) and removed the temporary
  `ANTHROPIC_API_KEY` from `.env` → back on the **free Max-plan CLI**. Per-run API
  cost logging (`[API cost] …`) added earlier remains for if the paid bridge is ever
  used again.
- **2026-06-24 (pm)** — **Deferred cross-run dedup commit (audit rank #6) + full
  pipeline audit.** The "seen" set was persisted during MERGE (before curation /
  delivery), so any run that failed, aborted, or emptied still marked news as seen
  and suppressed it for 24h — made acute by the new auth-abort path (every failed
  auth run was eating the next run's news). Fix: `_cross_run_dedupe` is now
  READ-ONLY (filter only); new `commit_delivered_seen(report)` persists ONLY items
  that actually shipped, called from `run_daily.py` after a successful send (so
  --no-email/--dry-email/empty/aborted runs no longer pollute). Unit-tested. Reset
  the polluted seen cache so the first re-authenticated run is full. A 43-agent
  pipeline audit found 33 issues; the dominant theme is "silently degrade + WARN +
  exit 0" with no delivery gate. Remaining high-value fixes still TODO: cap_per_sector
  relevance ordering (covered gnews items capped out pre-curation), finish source_type
  / strict direct match + regulator EXT exemption, materiality-ordered EXT cap,
  scrape-failure delivery gate, freshness timezone-offset handling.
- **2026-06-24** — **ROOT CAUSE of "almost no important news" clippings: the Claude
  CLI lost authentication.** `claude.exe` (the VS Code extension binary the curator
  spawns) was returning `401 Invalid authentication credentials`; the curator silently
  turned that non-JSON reply into an EMPTY report, so digests fell back to
  covered-name-only force-include = junk. **Fix #1 (user):** re-authenticate —
  `claude login` (or `/login` in the `claude` REPL); refreshes `~/.claude/.credentials.json`.
  **Fix #2 (code, `claude_reasoning.py` `categorise_headlines`):** retry once, then
  **FAIL LOUDLY** (raise → run aborts, sends NO email) instead of shipping a junk
  clipping. Added `benchmarks/reference_clippings.md` (analyst-approved digests) as the
  quality bar to cross-check every run against. ⚠️ If clippings ever go thin/junk again,
  FIRST check `claude.exe` auth (run the curator diagnostic / `claude login`).
- **2026-06-23/24** — **DIRECT-first source mix + fix for direct news being dropped.**
  (1) Raised the EXT (non-direct/Google-News) cap from **2 → 5**: `run_daily.py`
  `enforce_ext_cap(max_ext=5)` + curator prompt in `claude_reasoning.py` ("AT MOST 5
  <EXT>"). (2) **Root-cause fix:** `source_type` ("direct"/"gnews") was discarded
  before curation, so `enforce_ext_cap` re-guessed direct-vs-EXT by string-matching
  the curator's free-text source label against `DIRECT_SOURCES` — any direct item
  whose label didn't match (abbrev/translation/added words) was mislabelled EXT and
  dropped by the low cap. Fix: `reattach_links` now stamps the matched raw row's
  `source_type` back onto each curated item (high-confidence tiers only), and
  `enforce_ext_cap` reads it instead of forcing `""`. So genuine DIRECT items are
  never misclassified/dropped. Change is provably additive (can't drop a direct item;
  admits ≤3 more EXT). Verified on real CSV: direct item w/ mangled label rescued,
  EXT capped at 5. (Diagnosed via 5-agent workflow.)
- **2026-06-10** — Added **Canaltech** as a direct source (sector `Hardware`) to widen
  **Intelbras (INTB)** coverage — Brazilian consumer/hardware tech (cameras, routers,
  solar, gadgets). RSS = the FeedBurner feed `feeds2.feedburner.com/canaltechbr`
  (the site's `/rss/` paths 404; found via the homepage `<link>` tag). Feed is broad,
  so noise is contained by the covered-name safety net + curator. Touched `config.py`.
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
