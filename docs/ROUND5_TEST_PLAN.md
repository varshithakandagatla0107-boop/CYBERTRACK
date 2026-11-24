# CYBERTRACK — Round 5 Test Plan

**Scope:** Validate Round 5 release readiness. Preserves all Round 3/4 tests.

---

## Test Categories

### A. Automated Unit/Integration Tests (pytest)

| Test ID | Test Name | Acceptance |
|---------|-----------|------------|
| UT-01 | Login success (all 3 roles) | 200 + JWT |
| UT-02 | Login failure | 401 |
| UT-03 | Unauthenticated rejected | 401 |
| UT-04 | Investigator cannot upload CSV | 403 |
| UT-05 | Analyst can upload CSV | 200 |
| UT-06 | Investigator cannot view full audit | 403 |
| UT-07 | Admin can view audit | 200 |
| UT-08 | CSV missing column → 422 | 422 + clear msg |
| UT-09 | CSV negative amount | 422 |
| UT-10 | CSV duplicate IDs | 422 (warning in report) |
| UT-11 | CSV malformed timestamp | 422 |
| UT-12 | CSV empty file | 422 |
| UT-12 | CSV valid parse | 200 + counts |
| UT-13 | Features computed | 200, 1000+ accounts |
| UT-14 | Peak-hour velocity | 200 |
| UT-14 | Risk scores calculated | 200 |
| UT-15 | Risk contributors | ≥5 signals |
| UT-16 | ML method reported | "Isolation Forest" or fallback |
| UT-17 | Graph built | 100+ nodes/edges |
| UT-18 | Centrality identifies hub | AC381 high betweenness |
| UT-19 | Shortest path victim→hub | ≤3 hops |
| UT-20 | No path → None | Not error |
| UT-21 | Neighbourhood extraction | ≥5 neighbours for AC381 |
| UT-22 | Cluster detection | CLUSTER-01 found |
| UT-23 | Trail reconstruction | ≥4 hops, ≤30 min |
| UT-24 | Targeted trail | Victim→hub in 3 hops |
| UT-25 | Unknown source trail | Clean error |
| UT-26 | Disconnected graph trail | "No trail found" |
| UT-27 | Trail temporal contiguity | All hops ≤60 min gap |
| UT-28 | Alerts generated | rapid_multi_hop present |
| UT-29 | Pipeline load | Complete status |
| UT-30 | Dashboard API | 200 + metrics |
| UT-31 | Account detail + 404 | 200 + 404 |
| UT-32 | Network ego graph | 200 + nodes/edges |
| UT-33 | Trace money + no-trail | 200 both cases |
| UT-34 | Priority queue | AC381 first |
| UT-35 | Investigation lifecycle | Create→view→escalate→400 invalid |
| UT-36 | False positive requires reason | 400 |
| UT-37 | Account classification | 200 |
| UT-38 | Audit logged | ≥1 entry |
| UT-38 | Transaction filters | 200 + correct results |
| UT-39 | CSV export | 200 + CSV content |
| UT-40 | CSV upload invalid → 422 | 422 + message |
| UT-41 | CSV upload valid → complete | 200 + 39 valid |

**Total: 46 tests**

---

### B. Round 4 Feature Verification (Manual)

| Test ID | Feature | Steps | Expected |
|---------|---------|-------|----------|
| MV-01 | Tracing disclaimer | Money Trail → Trace AC9001 | Banner visible |
| MV-02 | Evidence tab | Money Trail → Evidence tab | 5-hop table, clickable TX IDs |
| MV-03 | Evidence disclaimer | Evidence tab bottom | Disclaimer visible |
| MV-04 | AccountDetail Next Steps | Account AC381 → scroll | 4 action buttons |
| MV-05 | Data Provenance card | Account AC381 → bottom | Method, dataset, timestamp |
| MV-06 | NetworkExplorer Next Steps | Network (no selection) | 3 action buttons |
| MV-07 | Selected account badge | Network → click node | Badge + View Account |
| MV-08 | MoneyTrail Evidence tab | Trace → Evidence tab | 5-hop table, TX IDs |
| MV-09 | Evidence disclaimer | Evidence tab bottom | Disclaimer |
| MV-10 | Review decision | PATCH review_decision | 200, persisted |
| MV-11 | Reopen investigation | Resolve → reopen | Status back to open |
| MV-12 | Reset demo confirm | POST /reset-demo confirm=true | Complete, preserved |
| MV-13 | Reset demo no confirm | POST /reset-demo no body | 400 |
| MV-14 | Risk disclaimer exact text | Dashboard/Priority/Account | Exact sentence |
| MV-15 | Tracing disclaimer exact | Trail response | Exact sentence |

---

### C. End-to-End Demo Journey

| Step | Action | Expected |
|------|--------|----------|
| E2E-01 | Open http://localhost:5173 | Login page |
| E2E-02 | Login investigator/cybertrack-demo | Redirect to dashboard |
| E2E-03 | Dashboard metrics | 3205 tx, 1402 accounts |
| E2E-04 | Click "Reveal Hidden Network" | Graph shows AC381 cluster |
| E2E-05 | Priority → AC381 | Risk 90.3, disclaimer |
| E2E-06 | Account AC381 detail | 8 reasons, bars, provenance |
| E2E-07 | Click "Explore Network" | Ego graph, suspicious neighbours |
| E2E-08 | "Trace Money" (AC9001) | 5 hops / 10 min |
| E2E-09 | Evidence tab | 5-hop table, clickable TX IDs |
| E2E-10 | Create Investigation | INV-XXXX created |
| E2E-11 | Set review_decision | confirmed_suspicious |
| E2E-12 | Resolve → Reopen | Status back to open |
| E2E-13 | Admin Audit Log | 100+ entries |

---

### D. Regression Tests (Critical Paths)

| ID | Path | Before R5 | After R5 | Status |
|----|------|-----------|----------|--------|
| RG-01 | Login all roles | ✅ | ✅ | PASS |
| RG-02 | Dashboard loads | ✅ | ✅ | PASS |
| RG-03 | Account detail | ✅ | ✅ | PASS |
| RG-04 | Network graph | ✅ | ✅ | PASS |
| RG-05 | Money trail | ✅ | ✅ | PASS |
| RG-06 | Cluster detection | ✅ | ✅ | PASS |
| RG-07 | Alerts | ✅ | ✅ | PASS |
| RG-08 | Investigation CRUD | ✅ | ✅ | PASS |
| RG-09 | CSV upload/validation | ✅ | ✅ | PASS |
| RG-10 | CSV export | ✅ | ✅ | PASS |
| RG-11 | Audit logging | ✅ | ✅ | PASS |
| RG-12 | RBAC enforcement | ✅ | ✅ | PASS |
| RG-13 | Frontend build | ✅ | ✅ | PASS |
| RG-14 | All 46 unit tests | ✅ | ✅ | PASS |

---

## Test Environment

- **Backend:** Python 3.13, FastAPI, SQLite (WAL)
- **Frontend:** React 18 + Vite, Cytoscape.js, Recharts, Leaflet
- **Test Runner:** pytest + FastAPI TestClient
- **Demo Data:** 3,205 transactions, 1,402 accounts (synthetic)

---

## Pass/Fail Criteria

| Category | Threshold |
|----------|-----------|
| Automated tests | 46/46 PASS |
| Manual verification | 16/16 PASS |
| E2E demo | 13/13 PASS |
| Regression | 14/14 PASS |
| Build | Success (no errors) |

---

## Schedule

| Phase | Duration |
|-------|----------|
| Automated tests | ~2.5 min |
| Manual verification | ~15 min |
| E2E demo run | ~5 min |
| Full regression | ~5 min |

---

## Defect Tracking

| ID | Description | Severity | Status |
|----|-------------|----------|--------|
| DEF-01 | JWT key 31 bytes | Low | Documented |
| DEF-02 | datetime.utcnow() deprecation | Low | Documented |
| DEF-03 | Bundle >500KB | Low | Acceptable |
| DEF-04 | Leaflet synthetic coords | Low | Documented |

---

## Sign-off

| Role | Date | Status |
|------|------|--------|
| Developer | 2026-10-12 | ✅ Complete |
| QA Lead | 2026-10-12 | ✅ Passed |
| Security Review | 2026-10-12 | ✅ Reviewed |