# Health & alerts — how you'll know if the clipping breaks

The clipping silently degraded once (June 2026) because the **Claude CLI lost its
login**: the curator started returning nothing, but the email still went out as
covered-name filler — so the failure wasn't obvious; we only noticed the *quality*
dropped. This file documents the safeguards now in place so that can't happen
silently again.

## How a broken run notifies you NOW
When a run can't curate (almost always: the CLI login expired), the pipeline:

1. **Emails you an alert** — subject `[ACTION NEEDED] TMT clipping FAILED …`, sent to
   the addresses in `config.py → ALERT_EMAIL` (currently `rafael.oliveira@ubs.com`
   + `rafaelxoliver4@gmail.com`). It says exactly what happened and how to fix it.
2. **Writes a flag file** `CLIPPING_FAILED.txt` in this folder. If that file is
   present, the last run failed. It is deleted automatically on the next *successful*
   run, so its mere presence = "needs attention."
3. **Sends NO digest** (instead of shipping filler). So **"no clipping + an alert
   email" = action needed** — it will never quietly send you junk again.

## The fix (≈90% of the time): re-login the CLI
In a normal terminal (PowerShell — Win+R → `powershell`), run:
```
claude
```
then type **`/login`** and sign in with your **Max** account in the browser. The next
scheduled run works again.

Verify it took: the alert emails stop, `CLIPPING_FAILED.txt` disappears after the
next run, and clippings are full again. (You can also just wait for the next
scheduled run at 06:40 / 16:30 / 18:00.)

## Why it happens
The Max-plan CLI access token expires periodically. If its refresh token is missing
or also expired, it can't auto-renew and starts returning
`401 Invalid authentication credentials`. Re-logging in writes a fresh token to
`~/.claude/.credentials.json`.

## Cost
- **Free (default):** the Max-plan CLI — no `ANTHROPIC_API_KEY` in `.env`.
- **Paid bridge:** set `ANTHROPIC_API_KEY=sk-ant-…` in `.env` → the curator calls the
  API instead (~$0.15/run on Sonnet; per-run cost is printed as `[API cost] …`). Use
  ONLY as a temporary bridge if the CLI login can't be fixed right away; delete the
  line to return to free.

## Schedule
Windows Task Scheduler, weekdays BRT: **06:40 / 16:30 / 18:00**. The task definitions
are saved as XML in `scheduler/` (re-importable on a new PC — see `MIGRATION.md`).
