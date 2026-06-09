# Migrating the TMT Clipping to a new PC

This pipeline runs unattended on a Windows PC via Task Scheduler. Use this guide
to rebuild it on another machine. (H&E is a separate repo — repeat there too.)

> You can move gradually: set the new PC up, smoke-test it, and only **disable the
> old PC's tasks once the new PC is delivering reliably.** Don't run both at the
> same time long-term or the team gets duplicate emails.

## 1. Prerequisites on the new PC
- **Windows 10/11**, signed into the **same OneDrive account** (so the project
  folder syncs to the same path), or plan to `git clone` to a local folder.
- **Python 3.13** — install from the Microsoft Store or python.org. Verify:
  `python --version`.
- **Claude Code CLI (`claude.exe`)** installed and **logged in** (Max plan).
  Curation calls the CLI when no `ANTHROPIC_API_KEY` is set. Verify: `claude --version`
  runs and does **not** prompt for login.
- **Git** (optional, for pulling updates).

## 2. Get the code
- **Option A — OneDrive sync:** let OneDrive sync
  `...\OneDrive\Área de Trabalho\Python\News Scraper Claude\` to the new PC.
- **Option B — git clone:**
  ```
  git clone https://github.com/rafaelxoliver4-art/tmt-clipping.git
  ```

## 3. Install Python dependencies
From inside the project folder:
```
pip install -r requirements.txt
```
(Only `reportlab` + `tzdata`; everything else is stdlib.)

## 4. Recreate the secret `.env` (NEVER in git)
Create a file named `.env` in the project folder with:
```
FROM_EMAIL=ibotatom@gmail.com
EMAIL_APP_PASSWORD=<the Gmail app password>
```
Copy the app password from the **old PC's `.env`** (it is gitignored, so it is never
in the repo). Without this, email sending fails.

## 5. Import the scheduled tasks
Task definitions are saved in `scheduler\*.xml` — **3 clipping tasks + 2 Anatel
Monitor tasks**. Import each (PowerShell, same user):
```powershell
Register-ScheduledTask -TaskName "TMT News Clipping 07-00 BRT" `
  -Xml (Get-Content "scheduler\TMT News Clipping 07-00 BRT.xml" -Raw)
Register-ScheduledTask -TaskName "TMT News Clipping 16-30 BRT" `
  -Xml (Get-Content "scheduler\TMT News Clipping 16-30 BRT.xml" -Raw)
Register-ScheduledTask -TaskName "TMT News Clipping 18-00 BRT" `
  -Xml (Get-Content "scheduler\TMT News Clipping 18-00 BRT.xml" -Raw)
Register-ScheduledTask -TaskName "Anatel Monitor 09-00 BRT" `
  -Xml (Get-Content "scheduler\Anatel Monitor 09-00 BRT.xml" -Raw)
Register-ScheduledTask -TaskName "Anatel Monitor 18-00 BRT" `
  -Xml (Get-Content "scheduler\Anatel Monitor 18-00 BRT.xml" -Raw)
```

**IMPORTANT — fix paths if they differ.** The XML hardcodes the old PC's username
and Python path. If the new PC differs, open each XML in a text editor and update:
- `<Command>` / `<Arguments>` — the `cd /d "<project folder>"`, the `python.exe`
  path, the target script path, and the `>> "<log path>"` redirect.
- `<WorkingDirectory>`.
- `<Principal><UserId>` — set to the new PC's user (or just recreate the task in the
  Task Scheduler GUI using the same trigger times and the command from the XML).

The morning task **name** says "07-00" but its real trigger is **06:40** — that's
intentional, leave it.

After import, confirm each task shows **Ready** with the right triggers
(**06:40** morning, **16:30** + **18:00** afternoon, Mon–Fri).

> Note: the **Anatel Monitor** tasks belong to this TMT project too. Skip them only
> if you don't use the Anatel monitor.

## 6. Smoke-test before trusting it
From inside the project folder (does NOT email the team):
```
python run_daily.py --dry-email     # renders an HTML preview, sends nothing
```
To test a real send to yourself only, temporarily set the recipient to
`rafaelxoliver4@gmail.com` (see `CLAUDE.md` → Operating principles), then revert.

## 7. Power settings (so the 06:40 run fires on time)
Morning runs only fire if the PC is awake at 06:40. Options:
- Keep the PC on/awake, **or**
- On each morning task: enable **"Wake the computer to run this task"** + allow wake
  timers in the power plan. (Works from **sleep**, not a full shutdown — a powered-off
  laptop can't wake itself.)
`StartWhenAvailable=true` is already set, so a missed run catches up on next power-on.

## 8. Decommission the old PC (last)
Once the new PC has delivered correctly for a couple of days, **disable** (don't just
ignore) the old PC's tasks so the team never gets duplicates:
```powershell
Disable-ScheduledTask -TaskName "TMT News Clipping 07-00 BRT"
Disable-ScheduledTask -TaskName "TMT News Clipping 16-30 BRT"
Disable-ScheduledTask -TaskName "TMT News Clipping 18-00 BRT"
```
