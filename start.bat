@echo off
REM CYBERTRACK — one-command startup (Windows)
REM Starts the FastAPI backend, then the Vite frontend.
cd /d "%~dp0"
start "CYBERTRACK Backend" cmd /c "cd backend && python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 && pause"
timeout /t 3 /nobreak >nul
start "CYBERTRACK Frontend" cmd /c "cd frontend && npm run dev && pause"
echo.
echo CYBERTRACK starting...
echo Backend:  http://127.0.0.1:8000
echo Frontend: http://localhost:5173
echo Login: investigator / cybertrack-demo
