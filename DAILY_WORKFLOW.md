# TMT News Clipping — Daily Workflow

## Automated (no action needed from Rafael)

Windows Task Scheduler fires 3×/day, weekdays only, local BRT:

| Task name | Time (BRT) | What it does |
|---|---|---|
| `TMT News Clipping 06-00 BRT` | 06:00 | Scrapes Google News + direct RSS, writes `output/claude_input_YYYY-MM-DD.txt` |
| `TMT News Clipping 16-30 BRT` | 16:30 | Same |
| `TMT News Clipping 18-00 BRT` | 18:00 | Same |

**Requirement:** your laptop must be on and logged in at those times. If it's asleep or off, the task is skipped (next run at the next scheduled time). Task Scheduler has `StartWhenAvailable=true`, so a missed run will fire as soon as the laptop wakes up.

Each run appends to `output/scheduled_runs.log`. Debug by opening that file.

## Daily curation + email (Rafael, 90 seconds)

When you want the digest sent (typically after one of the scheduled scrapes), open a Claude Code session in this project folder and say:

> **run the clipping**

Claude Code will:
1. Read the freshest `output/claude_input_YYYY-MM-DD.txt`
2. Curate the top ~50 most material items using the editorial rules from the Obsidian wiki
3. Write `output/curated_YYYY-MM-DD.json`
4. Run `python send_digest.py output/curated_YYYY-MM-DD.json` to email both addresses

Total time: ~90 seconds.

## Local setup

- `run_clipping.bat` — scheduler wrapper around `python run_daily.py`
- `send_digest.py` — reads curated JSON, emails via iCloud SMTP
- `.env` — credentials (FROM_EMAIL + EMAIL_APP_PASSWORD; gitignored)
- Recipients hardcoded in `config.py` EMAIL_RECIPIENTS
- Output: `output/` (CSVs, claude_input, curated, scheduled_runs.log)

## Managing scheduled tasks

From PowerShell:
```powershell
# View all 3
Get-ScheduledTask -TaskName "TMT News Clipping*" | Select TaskName, State, @{N='Next';E={(Get-ScheduledTaskInfo $_).NextRunTime}}

# Run one now (manual trigger)
Start-ScheduledTask -TaskName "TMT News Clipping 06-00 BRT"

# Disable temporarily
Disable-ScheduledTask -TaskName "TMT News Clipping 06-00 BRT"

# Re-enable
Enable-ScheduledTask -TaskName "TMT News Clipping 06-00 BRT"

# Delete entirely
Unregister-ScheduledTask -TaskName "TMT News Clipping 06-00 BRT" -Confirm:$false
```

## Cloud scheduled agents — disabled, not in use

Three triggers exist at https://claude.ai/code/scheduled but are disabled. The platform accepted the config but never actually executed runs (0 webhook hits across multiple tests, no sessions in the web UI). Kept as dormant config in case support enables the feature later. If they start executing, we can re-enable and remove the local Task Scheduler entries.

- `trig_01NWFbj9mRWSfkq5WGN7JDEh` (06:00 BRT)
- `trig_01DvYGwVBa71C32E898QocWf` (16:30 BRT)
- `trig_014a2ufvvFtpN9nDcu4U6nEu` (18:00 BRT)

## Troubleshooting

**Scheduled task shows "Queued" and never runs.** This was the initial issue with `schtasks /Create`. The fix was to use PowerShell `Register-ScheduledTask` with explicit `-Principal` (Interactive logon, Limited run level). If this regresses, re-register with the `Register-ScheduledTask` approach (see the commit that added this file for the exact call).

**No email arrives after "run the clipping"**: check `.env` exists with `FROM_EMAIL` + `EMAIL_APP_PASSWORD`. The iCloud app password was rotated on [date TBD by Rafael]. If expired, generate a new one at https://account.apple.com → Sign-In & Security → App-Specific Passwords.

**Task log shows Python errors**: see `output/scheduled_runs.log`. Most likely cause: `requirements.txt` deps missing after Python upgrade. Run `pip install reportlab` (only needed if you re-enable PDF generation).
