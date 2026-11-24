# CYBERTRACK — Audit Baseline

## Repository Overview

**Project:** CYBERTRACK — PS-35 Mule Account Tracing
**Stack:** FastAPI (Python 3.13) + React/Vite (TypeScript) + Cytoscape.js + SQLite
**Purpose:** Transform fragmented transaction data into an explainable money-flow network, detect suspicious mule/intermediary accounts, reconstruct money movement over time, and prioritize investigations.

## Current State (as of audit)

### What Works
- **Backend API** (FastAPI) with 15 routers: auth, data, dashboard, accounts, transactions, network, trails, priorities, clusters, alerts, investigations, audit, analytics, export, settings
- **CSV Ingestion** with validation (required columns, amounts, timestamps, duplicates, self-transfers)
- **Feature Extraction** per account (velocity, in/out amounts, counterparties, rapid pass-through, burst, temporal concentration, graph degree/centrality)
- **Graph Construction** (NetworkX DiGraph) with centrality, community detection, shortest paths
- **Risk Scoring** (weighted composite: pass-through, velocity, centrality, diversity, burst, temporal, ML anomaly)
- **Anomaly Detection** (Isolation Forest with analytical fallback)
- **Money Trail Reconstruction** (temporal DFS + greedy downstream)
- **Cluster Detection** (Louvain communities on undirected projection)
- **Alert Generation** (7 typologies: rapid pass-through, high connectivity, burst, structuring, multi-hop, convergence, divergence)
- **Investigation Workspace** (create, status, review_decision, reopen, attach entities, notes, audit log)
- **Authentication** (JWT HS256, PBKDF2 password hashing, 3 roles: investigator/analyst/admin)
- **Frontend** (React 18 + Vite, Cytoscape.js, Recharts, Leaflet)
- **Tests** (46 pytest tests passing)

### Known Issues (from audit)

| # | Issue | Severity |
|---|-------|----------|
| 1 | CSV amount misalignment (index mismatch after sorting) | High |
| 2 | Static file serving fails when CWD != repo root | High |
| 3 | DB config claims PostgreSQL support but doesn't work | High |
| 4 | Environment variable loading not explicit (.env not loaded) | Medium |
| 5 | Demo auth with shared password, fallback JWT secret, localStorage token | Security |
| 6 | Upload reads entire file into memory before size check | Security |
| 7 | Audit log lacks integrity (no hash chaining) | Security |
| 8 | Broad exception handlers hide failures | Reliability |
| 9 | DB concurrency/isolation/recovery untested | Reliability |
| 10 | Analytical claims unvalidated, trail/graph edge cases | Analytical |
| 11 | No frontend/e2e tests, accessibility unverified | Quality |
| 12 | Bloated release archive (6,102 entries) | Packaging |
| 13 | Docs inconsistent with code (DB, env, static, Postgres, synthetic claims) | Docs |

### Current Test Status
```
46 passed, 32 warnings in ~2.5 min
```

### How to Run (Current)
```bash
# Backend
cd backend
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000

# Frontend
cd frontend
npm install
npm run dev
```

### Demo Credentials
- `investigator` / `cybertrack-demo`
- `analyst` / `cybertrack-demo`
- `admin` / `cybertrack-demo`

---

## Decisions Log (DECISIONS.md will track these)

| Decision | Rationale |
|----------|-----------|
| SQLite only for this release | Simplifies deployment; PostgreSQL marked as future work |
| JWT in HTTP-only cookies with CSRF | Better security than localStorage |
| demo mode = random JWT secret per process | Avoids hardcoded secret in production |
| SQLite WAL mode + busy_timeout | Better concurrency |
| Timestamp parsing: naive = UTC | Documented assumption |
| Duplicate transaction ID = keep first | First record wins |

---