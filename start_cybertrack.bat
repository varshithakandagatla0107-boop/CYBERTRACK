@echo off
REM CYBERTRACK - start the permanent server (detached, auto-restart)
cd /d "%~dp0"
start "" /min pythonw serve_forever.py
echo CYBERTRACK starting at http://localhost:8000
echo Logs: %~dp0logs\server.log
