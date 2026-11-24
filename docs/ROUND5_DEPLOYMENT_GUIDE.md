# CYBERTRACK — Round 5 Deployment Guide

**Status:** Local development verified. Production deployment not yet attempted.

---

## 1. Prerequisites

| Requirement | Version | Notes |
|-------------|---------|-------|
| Python | 3.11+ | 3.13 tested |
| Node.js | 18+ | 20+ recommended |
| npm | 9+ | Comes with Node |
| Git | Any | For version control |
| OS | Windows 10/11, Linux, macOS | Tested on Windows 11 |

---

## 2. Environment Variables

Create `.env` in `backend/` (copy from `.env.example`):

```bash
# backend/.env
CYBERTRACK_DB=sqlite:///./data/cybertrack.db
CYBERTRACK_JWT_SECRET=your-32-byte-secret-here-change-in-production
CYBERTRACK_JWT_EXPIRE_MINUTES=480
CYBERTRACK_DEMO=1
```

**Required variables:**
| Variable | Required | Description |
|----------|----------|-------------|
| `CYBERTRACK_DB` | Yes | SQLite path or PostgreSQL URL |
| `CYBERTRACK_JWT_SECRET` | Yes | **Must be ≥32 bytes** for production (current demo uses 31 bytes) |
| `CYBERTRACK_JWT_EXPIRE_MINUTES` | No | Default 480 (8 hours) |
| `CYBERTRACK_DEMO` | No | Set to `1` to auto-load demo case on startup |

---

## 3. Local Development Setup

### 3.1 Backend

```bash
cd backend

# Create virtual environment (recommended)
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run (auto-loads demo case on first start)
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

**Health check:** `curl http://127.0.0.1:8000/api/health` → `{"status":"ok","service":"cybertrack"}`

### 3.2 Frontend

```bash
cd frontend

# Install dependencies
npm install

# Development server (proxies /api → http://127.0.0.1:8000)
npm run dev
# Opens http://localhost:5173
```

### 3.3 One-Command Start (Windows)

```cmd
start.bat
```

---

## 4. Production Build

### 4.1 Frontend Production Build

```bash
cd frontend
npm run build
# Output: frontend/dist/
```

### 4.2 Serve Production Build

FastAPI serves `frontend/dist` as static files when mounted:

```python
# In backend/app/main.py (already present)
try:
    app.mount("/", StaticFiles(directory="frontend/dist", html=True), name="frontend")
except Exception:
    pass
```

Run backend only:
```bash
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
# Frontend available at http://<host>:8000
```

---

## 5. Database

### 5.1 SQLite (Development/Prototype)

- File: `backend/data/cybertrack.db`
- WAL mode enabled for concurrent reads
- Auto-created on first run via `init_db()`
- Schema in `backend/app/db/database.py` (SCHEMA constant)

### 5.2 PostgreSQL (Production Target)

Update `CYBERTRACK_DB`:
```bash
CYBERTRACK_DB=postgresql+asyncpg://user:pass@host:5432/cybertrack
```

Install asyncpg:
```bash
pip install asyncpg
```

**Migration:** Repository layer uses parameterised queries — swap connection implementation in `backend/app/db/database.py`. Schema is compatible with PostgreSQL.

### 5.3 Backup/Restore (SQLite)

```bash
# Backup
cp backend/data/cybertrack.db backend/data/cybertrack.db.backup

# Restore
cp backend/data/cybertrack.db.backup backend/data/cybertrack.db
```

**Note:** WAL files (`-wal`, `-shm`) must be copied together for consistent backup.

---

## 6. Running Tests

```bash
cd backend
python -m pytest tests/ -v
# 46 tests, ~2.5 minutes
```

---

## 7. Demo Data Management

### 7.1 Auto-Load on Startup

Backend auto-loads synthetic demo case on first start if no datasets exist:
```python
# backend/app/main.py lifespan
if existing_dataset is None:
    df = demo_case.generate_demo_case()
    load_dataset(df, ...)
```

### 7.2 Manual Reset (Preserves Investigations)

```bash
# As analyst role
curl -X POST http://127.0.0.1:8000/api/data/reset-demo \
  -H "Authorization: Bearer <analyst_token>" \
  -H "Content-Type: application/json" \
  -d '{"confirm": true}'
```

**Preserves:** investigations, users, audit log  
**Replaces:** transactions, features, risk, clusters, alerts, trails

### 7.3 Upload Custom CSV

```bash
curl -X POST http://127.0.0.1:8000/api/data/upload \
  -H "Authorization: Bearer <analyst_token>" \
  -F "file=@transactions.csv"
```

**Required columns:** `transaction_id, sender_account, receiver_account, amount, timestamp, transaction_type, channel, sender_location, receiver_location`

---

## 8. Common Failures & Recovery

| Error | Cause | Fix |
|-------|-------|-----|
| `Address already in use` (port 8000) | Previous uvicorn still running | `Get-Process -Name python | Where-Object {$_.CommandLine -like '*uvicorn*'} \| Stop-Process -Force` |
| `ModuleNotFoundError` | Dependencies not installed | `pip install -r requirements.txt` |
| `npm run dev` fails | Node modules missing | `cd frontend && rm -rf node_modules package-lock.json && npm install` |
| `sqlite3.OperationalError: database is locked` | WAL files inconsistent | Delete `cybertrack.db-wal` and `cybertrack.db-shm` |
| Frontend shows "Network Error" | Backend not running / CORS | Start backend first; check CORS in `main.py` |
| JWT `InvalidKeyLength` warning | Secret < 32 bytes | Set `CYBERTRACK_JWT_SECRET` to 32+ byte random string |

---

## 9. Health Checks & Monitoring

| Endpoint | Expected Response |
|----------|-------------------|
| `GET /api/health` | `{"status":"ok","service":"cybertrack"}` |
| `GET /api/dashboard` (auth) | 200 + metrics JSON |
| `GET /api/audit/my` (auth) | 200 + audit entries |

**Prometheus metrics:** Not yet implemented. Add `prometheus-fastapi-instrumentator` if needed.

---

## 10. Rollback Procedure

### SQLite
```bash
# Stop backend
# Restore DB
cp backend/data/cybertrack.db.backup backend/data/cybertrack.db
# Remove WAL files
rm -f backend/data/cybertrack.db-wal backend/data/cybertrack.db-shm
# Restart backend
```

### Frontend
```bash
# Redeploy previous dist/ or rebuild from known-good commit
git checkout <known-good-commit> -- frontend/
cd frontend && npm run build
```

---

## 11. Production Deployment Checklist (Not Yet Done)

- [ ] Set `CYBERTRACK_JWT_SECRET` ≥32 bytes in secure vault
- [ ] Configure PostgreSQL + connection pooling
- [ ] Enable HTTPS (reverse proxy: nginx + certbot)
- [ ] Configure CORS for production domain
- [ ] Set secure cookies (HttpOnly, Secure, SameSite)
- [ ] Add rate limiting middleware
- [ ] Add CSRF protection for cookie-based flows
- [ ] Add account lockout after failed logins
- [ ] Add audit log integrity (hash chaining)
- [ ] Configure log aggregation (ELK/Loki)
- [ ] Add monitoring (Prometheus + Grafana)
- [ ] Add CI/CD pipeline with security scanning
- [ ] Run penetration test
- [ ] Legal/compliance review for jurisdiction

---

## 11. Support & Escalation

| Issue | Contact |
|-------|---------|
| Backend API errors | Check `uvicorn` logs |
| Frontend build errors | Check `npm run build` output |
| Database issues | Check SQLite file permissions |
| Auth issues | Verify JWT secret, token expiry |
| Demo data issues | Run `/api/data/reset-demo` with confirm=true |

---

**Note:** This guide covers the current prototype state. Production deployment requires completing the checklist in Section 11.