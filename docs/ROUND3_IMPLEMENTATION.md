# CYBERTRACK — Round 3 Implementation

## 1. Files Changed

### Backend

| File | Purpose |
| ---- | ------- |
| `app/engine/ingestion.py` | Added `rejected_rows` to validation report with reason codes; added `_flag_reason()` helper |
| `app/engine/pipeline.py` | (already had reset logic) |
| `app/routers/data.py` | Added `ResetRequest` model + `/api/data/reset-demo` endpoint (preserves investigations/users/audit) |
| `app/routers/trails.py` | Added `tracing_disclaimer` to trail responses |
| `app/routers/accounts.py` | Updated disclaimer to exact required sentence |
| `app/routers/dashboard.py` | Added `risk_disclaimer` to dashboard response |
| `app/routers/priorities.py` | Added `risk_disclaimer` to priority queue response |
| `app/routers/investigations.py` | Added `review_decision` column (migration), `review_decision` field to update, explicit `reopen` boolean, validation |
| `app/db/database.py` | Added `review_decision` column to `investigations` table with migration |

### Frontend

| File | Change |
| ---- | ------ |
| `src/pages/Dashboard.jsx` | Displays `risk_disclaimer` from API |
| `src/pages/PriorityAccounts.jsx` | Displays `risk_disclaimer` from API |

### Documentation (created/updated)

- `docs/ROUND3_BASELINE.md`
- `docs/ROUND3_IMPLEMENTATION.md` (this file)
- `docs/ROUND3_TEST_RESULTS.md`
- `docs/KNOWN_LIMITATIONS.md`

## 2. Features Implemented / Repaired

| Feature | Status | Notes |
| ------- | ------ | ----- |
| Synthetic demo case auto-load | ✅ Working | Already existed, verified |
| CSV upload + validation | ✅ Working | Already existed, enhanced with rejected-row details |
| Rejected-row inspection | ✅ Added | Up to 200 rejected rows returned with reason |
| Reset to demo (confirm) | ✅ Added | `/api/data/reset-demo?confirm=true` preserves investigations |
| Account features & graph | ✅ Working | Already existed |
| Isolation Forest / fallback | ✅ Working | Already existed |
| Explainable risk (contributors) | ✅ Working | Already existed |
| Temporal money-trail tracing | ✅ Working | Already existed |
| Tracing disclaimer | ✅ Added | "This path shows a temporally connected transaction sequence..." |
| Risk disclaimer (exact) | ✅ Added | "Risk scores support investigative prioritization. They do not establish fraud or guilt." |
| Dashboard risk disclaimer | ✅ Added | Shown from API response |
| Priority queue risk disclaimer | ✅ Added | Shown from API response |
| Account detail disclaimer | ✅ Updated | Exact required sentence |
| Investigation `review_decision` | ✅ Added | `pending / confirmed_suspicious / false_positive / inconclusive` |
| Investigation reopen | ✅ Added | `reopen: true` transitions resolved/closed → open |
| Investigation validation | ✅ Added | 400 for invalid decision, 400 for reopen on non-resolved |

## 3. Run Commands

```bash
# Backend (from backend/)
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000

# Frontend (from frontend/)
npm run dev

# One-command (Windows)
start.bat

# Tests (from backend/)
python -m pytest tests/ -v
```

## 4. Test Commands & Results

```bash
# Unit / integration tests
cd backend && python -m pytest tests/ -v

# Result
46 passed, 32 warnings in 144.20s
```

Warnings (non-blocking):
- JWT key length (31 bytes vs recommended 32)
- `datetime.utcnow()` deprecation
- httpx/starlette test client deprecation

### Round 3 Backend Verification (12/12 pass)

| # | Feature | Expected | Actual |
| - | ------- | -------- | ------ |
| 1 | reset without confirm → 400 | 400 | 400 ✅ |
| 2 | reset with confirm | complete | complete ✅ |
| 3 | dashboard risk_disclaimer | exact sentence | exact ✅ |
| 4 | priorities risk_disclaimer | exact sentence | exact ✅ |
| 5 | account disclaimer | exact sentence | exact ✅ |
| 6 | trail tracing_disclaimer | present | present ✅ |
| 7 | create investigation | 200 + ID | OK ✅ |
| 8 | set review_decision | 200 updated | OK ✅ |
| 9 | detail shows review_decision | confirmed_suspicious | OK ✅ |
| 10 | reopen resolved → open | status=open | OK ✅ |
| 11 | reopen non-resolved → 400 | 400 | 400 ✅ |
| 12 | invalid review_decision → 400 | 400 | 400 ✅ |

## 5. Complete Demo Journey

1. **Open app** → http://localhost:5173
2. **Login** → `investigator` / `cybertrack-demo`
3. **Dashboard loads** → 3,205 tx, 1,402 accounts, AC381 at 90.3 risk
4. **Click "Reveal Hidden Network"** → graph transitions to show hub-and-spoke cluster
5. **Priority Accounts** → AC381 rank 1, risk 90.3, disclaimer shown
6. **Click AC381** → Account detail: risk 90.3, 8 reasons, contributor bars, disclaimer
7. **Network Position** → ego network with suspicious neighbours highlighted
8. **Trace Money** (source AC9001) → 5 hops / 10 min / branching at hub
9. **Create Investigation** → INV-2026-XXXX created
10. **Set review_decision** → confirmed_suspicious
11. **Resolve → Reopen** → status back to open
12. **Audit Log (admin)** → all actions recorded

## 6. Remaining Blockers / Limitations

| Limitation | Impact | Status |
| ---------- | ------ | ------ |
| JWT key < 32 bytes | Prototype only | Documented |
| `datetime.utcnow()` deprecation | Cosmetic | To fix before prod |
| No rate limiting | Prototype | Documented |
| No real bank/I4C APIs | By design | Labelled "Future Integration" |
| Leaflet map uses synthetic coords | Demo only | Documented |
| No CSRF / account lockout | Prototype | Documented |
| Frontend chunk size > 500KB | Bundle size | Acceptable for demo |

## 7. What Is Real vs Fallback vs Future

| Component | Status |
| --------- | ------ |
| CSV validation & ingestion | Real |
| Feature extraction | Real |
| NetworkX graph + centrality | Real |
| Louvain communities | Real |
| Isolation Forest (scikit-learn) | Real (fallback if unavailable) |
| Explainable risk scoring | Real (deterministic weights) |
| Temporal trail reconstruction | Real (DFS + greedy downstream) |
| Cash-out intelligence | Fallback (analytical estimate) |
| Investigation persistence | Real (SQLite) |
| RBAC + audit log | Real |
| Bank / I4C / geospatial APIs | Future (labelled) |