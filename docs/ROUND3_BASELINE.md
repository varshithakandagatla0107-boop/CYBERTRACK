# CYBERTRACK — Round 3 Baseline

Inspection performed before Round 3 changes.

## 1. Repository stack discovered

| Layer | Technology | Version |
| ----- | ---------- | ------- |
| Backend | FastAPI (Python) | 3.13.6 |
| Frontend | React 18 + Vite 5 | JSX |
| Graph | NetworkX | via Python |
| Graph UI | Cytoscape.js | 3.x |
| Charts | Recharts | 2.x |
| Maps | Leaflet | 1.9.4 (prepared) |
| ML | scikit-learn Isolation Forest | with deterministic fallback |
| Database | SQLite (WAL mode) | file: `backend/data/cybertrack.db` |
| Tests | pytest + FastAPI TestClient | 46 tests |

Entry points:
- Backend: `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000`
- Frontend: `npm run dev` (Vite dev server, port 5173, proxies `/api` → 8000)
- One-command: `start.bat` (Windows)

## 2. Feature inventory (before Round 3)

### Working (verified)
- JWT login, 3-role RBAC (investigator/analyst/admin), PBKDF2 password hashing
- Synthetic demo case auto-load on first start (3,205 tx / 1,402 accounts)
- CSV upload with server-side validation (required columns, amounts,
  timestamps, duplicates, self-transfers)
- Full pipeline: ingestion → features → graph → Isolation Forest →
  explainable risk → clusters → alerts
- Dashboard with metrics, risk overview, top accounts, recent suspicious
  activity, alerts, "Reveal Hidden Network" aha moment
- Priority queue ranked by risk score
- Account detail: risk score, "why suspicious" reasons, contributor bars,
  behavioural features, ego network, timeline, classification
  (false positive requires reason)
- Network Explorer: Cytoscape graph, high-risk/amount filters, ego
  "Investigation View", shortest money path
- Money Trail: time-contiguous reconstruction (DFS + greedy downstream
  walk), timeline/graph/table views, cash-out intelligence (extension)
- Investigations: create, attach entities, status transitions, notes,
  printable report
- Audit log (admin full / investigator own)
- Analytics & model transparency page
- CSV export (transactions, priority accounts, alerts)
- Settings with future-integration labels

### Partially working / gaps found
- **Reset-to-demo**: "Load Demonstration Case" reloads data but there is
  no explicit reset action with confirmation, and no guarantee unrelated
  investigations are preserved.
- **Rejected-row inspection**: ingestion flags invalid rows in the report
  counts, but the API response does not return the actual rejected rows
  for inspection.
- **Money-trail disclaimer**: the UI does not yet explicitly state that a
  reconstructed path is a temporally connected transaction sequence, not
  definitive legal tracing of specific currency units.
- **Risk disclaimer wording**: the exact required sentence "Risk scores
  support investigative prioritization. They do not establish fraud or
  guilt." is not displayed verbatim.
- **Investigation review decision**: status transitions exist, but there is
  no explicit "review decision" field (confirmed suspicious / false
  positive / inconclusive) recorded on the investigation.
- **Reopen investigation**: no explicit reopen-from-resolved path.

### Not present (by design — future scope)
- Real bank/I4C/geospatial integrations (labelled "Future Authorized
  Integration")
- Real map tiles (Leaflet prepared; synthetic coordinates only)

## 3. Main demonstration account

- **AC381** — primary mule hub, risk 90.3/100 (high).
- Chain: AC9001 (victim) → AC101 → AC245 → **AC381** → AC427/AC522/AC610
  → CO-01/02/03 (cash-out).
- 94% of received value forwarded within 15 minutes; 12 counterparties;
  4 transactions/hour peak; hub-and-spoke cluster (CLUSTER-01, 31 accounts).

## 4. Baseline test results

```
46 passed, 32 warnings in 140.07s
```

Warnings are non-blocking (JWT key length, `datetime.utcnow()`
deprecation, httpx/starlette deprecation notice).

## 5. Baseline server status at inspection

Both servers were stopped at inspection time (previous session ended).
They start cleanly with the documented commands; the demo case
auto-loads on first start into an empty database.
