@echo off
REM TMT News Clipping — fully automated pipeline.
REM Scrapes, curates via Claude Code CLI (Max plan), and emails the digest.
REM Uses Anaconda Python (non-Store) so subprocess can reach claude.exe.
REM
REM Logs to output/scheduled_runs.log.

setlocal
set "PROJECT=%~dp0"
set "PYTHON=C:\Users\Rafael\anaconda3\python.exe"
cd /d "%PROJECT%"

if not exist "%PROJECT%output" mkdir "%PROJECT%output"

echo. >> "%PROJECT%output\scheduled_runs.log"
echo ============================================================ >> "%PROJECT%output\scheduled_runs.log"
echo [%date% %time%] Scheduled run starting >> "%PROJECT%output\scheduled_runs.log"
echo ============================================================ >> "%PROJECT%output\scheduled_runs.log"

"%PYTHON%" -u "%PROJECT%run_daily.py" >> "%PROJECT%output\scheduled_runs.log" 2>&1

echo [%date% %time%] Scheduled run finished with exit %ERRORLEVEL% >> "%PROJECT%output\scheduled_runs.log"

endlocal
