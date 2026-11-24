@echo off
REM CYBERTRACK - stop the permanent server
cd /d "%~dp0"
python serve_forever.py stop
echo CYBERTRACK stopped.
