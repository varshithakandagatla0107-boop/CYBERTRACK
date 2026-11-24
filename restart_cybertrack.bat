@echo off
REM CYBERTRACK - stop any running instance, then start fresh (detached).
cd /d "%~dp0"
python serve_forever.py stop
start "" /min pythonw serve_forever.py
echo CYBERTRACK restarting at http://localhost:8000
echo Logs: %~dp0logs\server.log
