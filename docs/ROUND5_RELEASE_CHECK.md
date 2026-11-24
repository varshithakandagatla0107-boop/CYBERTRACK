# CYBERTRACK — Round 5 Release Check

**Verdict: GO — Showcase Ready**

## Evidence Summary

CYBERTRACK successfully demonstrates the complete PS-35 solution end-to-end:

- **Transaction ingestion → Network construction → Explainable risk scoring → Temporal money-trail reconstruction → Investigation workflow** all verified working
- 46/46 automated tests pass, 16/16 manual verification checks pass, 13/13 end-to-end demo steps verified
- No regressions from Round 4 (all 14 regression paths intact)
- Frontend production build succeeds, backend serves API on http://127.0.0.1:8000
- Frontend dev server runs on http://localhost:5173 with API proxy

## Actual Stack

| Layer | Technology | Version |
|-------|------------|---------|
| Backend | FastAPI | Python 3.13 |
| Frontend | React + Vite | 18 / 5 |
| Graph | NetworkX | 3.x |
| ML | scikit-learn Isolation Forest | with deterministic fallback |
| Database | SQLite (WAL) | file: `backend/data/cybertrack.db` |
| Tests | pytest | 46 tests |

## Deployment Target

- **Local development**: Backend on port 8000, Frontend on 5173 (Vite dev server with proxy)
- **Production build**: Frontend `npm run build` → `dist/` served by FastAPI static files
- **Database**: SQLite (WAL mode), PostgreSQL-ready repository layer

## Significant Changes in Round 5

| File | Purpose |
|------|---------|
| `docs/ROUND5_RELEASE_CHECK.md` | This file |
| `docs/ROUND5_DEMO_SCRIPT.md` | 5–7 minute timed demo script |
| `docs/ROUND5_JURY_QA.md` | Evidence-backed Q&A for reviewers |
| `docs/ROUND5_EVIDENCE_INDEX.md` | Links to evidence for each claim |
| `docs/ROUND5_SECURITY_REVIEW.md` | Security posture, gaps, remediation |
| `docs/ROUND5_DEPLOYMENT_GUIDE.md` | Exact startup/build/test/deploy commands |
| `docs/KNOWN_LIMITATIONS.md` | Updated with Round 5 status |

## Preserved Work (Rounds 3–4)

All core functionality preserved:
- Transaction ingestion with CSV validation and rejected-row reporting
- NetworkX graph with Louvain communities, centrality, shortest paths
- Explainable risk engine (weighted signals, Isolation Forest/fallback, contributor bars)
- Temporal trail engine (DFS + greedy downstream, temporal contiguity)
- Evidence tab in Money Trail with clickable transaction IDs
- Contextual "Next Steps" navigation on Account, Network, Trail pages
- Investigation workspace with review_decision, reopen, audit trail
- Reset-to-demo endpoint preserving investigations/audit
- Tracing disclaimer on all trail responses
- Exact risk disclaimer: "Risk scores support investigative prioritization. They do not establish fraud or guilt."

## Run Commands

```bash
# Backend (from backend/)
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000

# Frontend dev (from frontend/)
npm run dev

# Frontend production build (from frontend/)
npm run build

# Tests (from backend/)
python -m pytest tests/ -v

# One-command Windows
start.bat
```

## Test Results

| Suite | Result |
|-------|--------|
| Backend tests (pytest) | 46/46 PASS |
| Frontend build | ✅ PASS |
| Manual Round 5 verification | 16/16 PASS |
| End-to-end demo | 13/13 steps PASS |
| Regression (14 critical paths) | 14/14 PASS |

## Core Acceptance Gates

| Gate | Status | Evidence |
|------|--------|----------|
| Startup | PASS | `uvicorn app.main:app` starts cleanly |
| Build | PASS | `npm run build` succeeds |
| Auth | PASS | JWT + PBKDF2 + RBAC enforced |
| AuthZ | PASS | 403 on unauthorized actions |
| Import | PASS | CSV validation + rejected rows |
| Duplicates | PASS | Flagged in validation report |
| Graph | PASS | Directed edges, source refs |
| Node/edge select | PASS | Opens account/trail detail |
| Risk logic | PASS | 8 signals, contributor bars |
| Trail | PASS | 5 hops, 10 min, contiguity |
| Metrics | PASS | Counts match source records |
| Investigations | PASS | CRUD + reopen + audit |
| Audit | PASS | 100+ entries recorded |
| Error handling | PASS | No stack traces exposed |
| Routing | PASS | Direct/refresh works |
| Demo | PASS | 13-step journey verified |

## Outstanding Issues

| Issue | Severity | Status |
|-------|----------|--------|
| JWT key 31 bytes (<32) | Low | Documented in LIMITATIONS.md |
| `datetime.utcnow()` deprecation | Low | Documented |
| Frontend bundle >500KB | Low | Acceptable for demo |
| Leaflet map synthetic coords | Low | Documented |
| No rate limiting / CSRF / lockout | Medium | Documented for production |

## Demo Sequence (5–7 min)

1. **Login** → `investigator` / `cybertrack-demo`
2. **Dashboard** → "3,205 transactions reviewed. 65 high-priority accounts"
3. **Click "Reveal Hidden Network"** → AC381 hub cluster revealed
4. **Priority Accounts** → AC381 (90.3) → shows exact risk disclaimer
5. **Account Detail** → 8 reasons, contributor bars, data provenance
6. **Explore Network** → Ego graph with suspicious neighbours
7. **Trace Money** (AC9001) → 5 hops / 10 min / branching at AC381
8. **Evidence Tab** → 5-hop transaction table, clickable TX IDs
9. **Create Investigation** → review_decision → resolve → reopen
10. **Admin Audit Log** → All actions recorded

---

**Recommendation: GO for showcase.** All critical gates pass. The PS-35 solution is demonstrated end-to-end with genuine underlying data, explainable risk, evidence-linked trails, and human-in-the-loop investigation workflow.