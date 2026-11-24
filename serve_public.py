"""CYBERTRACK public-access watchdog.

Keeps BOTH running, detached and auto-healing:
  1. FastAPI backend on 0.0.0.0:8000 (serves the built frontend)
  2. Cloudflare quick tunnel to that backend

The current public URL is always written to PUBLIC_URL.txt.
On tunnel expiry the watchdog starts a fresh tunnel and updates the URL.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BACKEND = ROOT / "backend"
LOG_DIR = ROOT / "logs"
LOG_DIR.mkdir(exist_ok=True)
TUNNEL_LOG = LOG_DIR / "tunnel.log"
APP_LOG = LOG_DIR / "server.log"
URL_FILE = ROOT / "PUBLIC_URL.txt"
CLOUDFLARED = ROOT / "cloudflared.exe"
PORT = "8000"
LOCAL = f"http://127.0.0.1:{PORT}"
DETACHED = 0x00000008 | 0x00000200


def log(msg: str) -> None:
    with open(LOG_DIR / "watchdog.log", "a", encoding="utf-8") as fh:
        fh.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} {msg}\n")


def healthy() -> bool:
    try:
        with urllib.request.urlopen(LOCAL + "/api/health", timeout=8) as r:
            return json.loads(r.read()).get("status") == "ok"
    except Exception:  # noqa: BLE001
        return False


def ensure_backend() -> None:
    if healthy():
        return
    log("backend down -> starting")
    with open(APP_LOG, "a", encoding="utf-8") as fh:
        subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "app.main:app",
             "--host", "0.0.0.0", "--port", PORT],
            cwd=str(BACKEND), stdout=fh, stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL, creationflags=DETACHED,
        )
    for _ in range(60):
        time.sleep(2)
        if healthy():
            log("backend up")
            return
    log("backend FAILED to come up")


def run_tunnel() -> None:
    if not CLOUDFLARED.exists():
        log("cloudflared.exe missing - cannot start tunnel")
        return
    start_offset = TUNNEL_LOG.stat().st_size if TUNNEL_LOG.exists() else 0
    with open(TUNNEL_LOG, "a", encoding="utf-8") as fh:
        fh.write(f"\n=== tunnel start {time.strftime('%Y-%m-%d %H:%M:%S')} ===\n")
        fh.flush()
        proc = subprocess.Popen(
            [str(CLOUDFLARED), "tunnel", "--no-autoupdate",
             "--url", LOCAL],
            cwd=str(ROOT), stdout=fh, stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL, creationflags=DETACHED,
        )
        log(f"tunnel pid={proc.pid}")
        url = None
        deadline = time.time() + 90
        while time.time() < deadline and proc.poll() is None:
            try:
                with open(TUNNEL_LOG, "r", encoding="utf-8", errors="ignore") as rf:
                    rf.seek(start_offset)
                    text = rf.read()
                found = re.findall(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com", text)
                if found:
                    url = found[-1]
                    break
            except OSError:
                pass
            time.sleep(1)
        if url:
            URL_FILE.write_text(url + "\n")
            log(f"public URL: {url}")
        else:
            log("no URL found before tunnel exited")


def main() -> None:
    log("=== watchdog started ===")
    while True:
        try:
            ensure_backend()
            run_tunnel()
            while True:
                if not healthy():
                    log("backend lost while tunnel running")
                    ensure_backend()
                chk = subprocess.run(
                    ["tasklist", "/FI", "IMAGENAME eq cloudflared.exe"],
                    capture_output=True, text=True,
                )
                if "cloudflared.exe" not in chk.stdout:
                    log("tunnel process gone")
                    break
                time.sleep(15)
        except Exception as exc:  # noqa: BLE001
            log(f"watchdog error: {exc}")
        time.sleep(5)


if __name__ == "__main__":
    main()
