"""CYBERTRACK permanent server launcher (detached + auto-restart).

Starts the FastAPI backend, which serves the built frontend at '/'.
The PID file stores THIS launcher's PID so `stop` kills the whole tree.
"""
from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BACKEND = ROOT / "backend"
LOG_DIR = ROOT / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "server.log"
PID_FILE = ROOT / ".server.pid"
HOST = os.environ.get("CYBERTRACK_HOST", "0.0.0.0")
PORT = os.environ.get("CYBERTRACK_PORT", "8000")


def stop() -> None:
    if PID_FILE.exists():
        try:
            pid = int(PID_FILE.read_text().strip())
            subprocess.run(["taskkill", "/PID", str(pid), "/F", "/T"],
                           capture_output=True)
            print(f"Stopped launcher tree PID {pid}")
        except Exception as exc:  # noqa: BLE001
            print(f"Could not stop: {exc}")
        PID_FILE.unlink(missing_ok=True)
    else:
        print("No PID file; nothing to stop.")


def main() -> None:
    if len(sys.argv) > 1 and sys.argv[1] == "stop":
        stop()
        return

    # Track OUR pid; taskkill /T then kills uvicorn too.
    PID_FILE.write_text(str(os.getpid()))

    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"

    log = open(LOG_FILE, "a", encoding="utf-8")
    log.write(f"\n=== launcher start {time.strftime('%Y-%m-%d %H:%M:%S')} ===\n")
    log.flush()

    DETACHED = 0x00000008 | 0x00000200  # DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP

    while True:
        proc = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "app.main:app",
             "--host", HOST, "--port", PORT],
            cwd=str(BACKEND), env=env,
            stdout=log, stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL, creationflags=DETACHED,
        )
        log.write(f"uvicorn started pid={proc.pid} on {HOST}:{PORT}\n")
        log.flush()
        print(f"CYBERTRACK running at http://127.0.0.1:{PORT}")
        code = proc.wait()
        log.write(f"uvicorn exited code={code}; restarting in 2s\n")
        log.flush()
        if PID_FILE.exists() and PID_FILE.read_text().strip() != str(os.getpid()):
            break  # a newer launcher took over
        time.sleep(2)


if __name__ == "__main__":
    main()
