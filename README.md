# TMT News Clipping — Setup Guide

## What this does
Runs every morning and produces a PDF like:

    TMT News Clipping — 2/MAR
    ──────────────────────────────────────
    Telecom LatAm
    • AMX: OCDE recomienda descentralizar la CRT...  — El Economista
    • Sector: SpaceX could seek IPO valuation of $1.75T...  — Bloomberg

    Telecom Brazil
    • VIVT3/TIMS3: Starlink pede novas faixas e Anatel...  — Teletime
    ...
    ──────────────────────────────────────
    Next Results / Events
    • Grid Dynamics: Q4 2024 Earnings  — Mar-05
    • VTEX: VTEX Day 2025  — Apr-16

---

## File structure

```
tmt_news/
├── config.py              ← YOUR MAIN CONFIG — edit universe, keywords, sources here
├── gnews_scraper.py       ← Google News RSS scraper (PT/ES/EN)
├── url_scraper.py         ← Direct scraper for your 30+ mandatory sources
├── merge_and_clean.py     ← Dedup, cap, format for Claude
├── claude_reasoning.py    ← Claude API: categorise + find events
├── generate_report.py     ← Builds the PDF with reportlab
├── run_daily.py           ← Orchestrator — runs everything in sequence
├── setup_scheduler.bat    ← Register Windows Task Scheduler (run once as Admin)
└── output/                ← PDFs saved here (auto-created)
```

---

## Installation (one-time)

### 1. Python
Requires Python 3.9+. Download from https://python.org if needed.

### 2. Install dependencies
```bash
pip install reportlab tqdm
```

### 3. Set your Anthropic API key
In Windows, add an environment variable:
```
ANTHROPIC_API_KEY=sk-ant-...
```

Go to: **Control Panel → System → Advanced → Environment Variables**
Add a new User variable:
- Name:  `ANTHROPIC_API_KEY`
- Value: your key from https://console.anthropic.com

### 4. Test it works
```bash
cd tmt_news
python run_daily.py --test
```
This runs with sample data (no network needed). Should produce a PDF in `output/`.

### 5. Real run
```bash
python run_daily.py
```

### 6. Schedule daily (7 AM)
Right-click `setup_scheduler.bat` → **Run as administrator**
Edit `SET TASK_TIME=07:00` in the file first if you want a different time.

---

## Customisation

### Add/remove tickers
Edit `config.py` → `SECTORS` dict.
- `"covered"` = your tracked names (tagged with ticker in report)
- `"peers"`   = comps/context (tagged as "Sector")
- `"keywords"` = Google News search terms

### Add/remove news sources
Edit `config.py` → `DIRECT_SOURCES` list.

### Change how many headlines appear
Edit `config.py`:
```python
MAX_HEADLINES_PER_SECTOR = 15   # max per sector
MAX_TOTAL_HEADLINES      = 80   # hard cap total
```

### Change recency window
Edit `config.py`:
```python
GNEWS_WHEN = "1d"   # "1d" = today, "2d" = 2 days, "7d" = week
```

---

## Useful commands

```bash
# Test with sample data (no network)
python run_daily.py --test

# Use cached headlines from last run (skip scraping)
python run_daily.py --skip-scrape

# Print JSON only, no PDF (for debugging)
python run_daily.py --test --no-pdf

# Trigger the scheduled task manually
schtasks /run /tn "TMT_News_Clipping_Daily"
```

---

## Token usage estimate

| Step | Claude tokens |
|------|-------------|
| Headline categorisation | ~3,000–5,000 input + ~1,500 output |
| Events search (web) | ~500 input + ~500 output |
| **Daily total** | **~5,000–8,000 tokens** |

At Sonnet 4 pricing this is under $0.05 per day.

---

## Troubleshooting

**PDF not opening?**
Make sure `reportlab` is installed: `pip install reportlab`

**No headlines found?**
- Check your internet connection
- Run `python gnews_scraper.py` to test just the RSS scraper
- Try `GNEWS_INSECURE=1 python run_daily.py` if behind a corporate proxy

**Claude API error?**
- Verify `ANTHROPIC_API_KEY` env variable is set
- Check https://console.anthropic.com for quota/billing

**Behind a corporate proxy with TLS inspection?**
Set `GNEWS_INSECURE=1` as an environment variable (disables SSL cert verification).
