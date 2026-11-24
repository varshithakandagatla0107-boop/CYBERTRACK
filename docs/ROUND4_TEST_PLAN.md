# CYBERTRACK — Round 4 Test Plan

## Test Scope

Validate that the Round 4 improvements work correctly and no regressions were introduced.

## Test Categories

### 1. Unit/Integration Tests (Automated)

| Test ID | Test Name | Expected Result |
|---------|-----------|-----------------|
| UT-01 | Login success (all 3 roles) | 200 + JWT token |
| UT-02 | Login failure (bad password) | 401 |
| UT-03 | Unauthenticated request rejected | 401 |
| UT-04 | RBAC: Investigator cannot upload CSV | 403 |
| UT-05 | RBAC: Analyst can upload CSV | 200 |
| UT-06 | RBAC: Investigator cannot view full audit | 403 |
| UT-07 | RBAC: Admin can view full audit | 200 |
| UT-07 | CSV missing required column | 422 + clear error |
| UT-08 | CSV negative amount flagged | 422 |
| UT-09 | CSV duplicate IDs flagged | 422 (warning in report) |
| UT-10 | CSV malformed timestamp flagged | 422 |
| UT-11 | CSV empty file | 422 |
| UT-11 | CSV valid parse | 200 + correct counts |
| UT-12 | Features computed for 1000+ accounts | 200 |
| UT-13 | Velocity uses peak hour | 200 |
| UT-13 | Risk scores calculated | 200 |
| UT-14 | Risk explainable contributors | ≥5 signals |
| UT-15 | ML method reported | "Isolation Forest" or "Analytical fallback" |
| UT-16 | Graph built with 100+ nodes | 200 |
| UT-17 | Centrality identifies hub | AC381 high betweenness |
| UT-18 | Shortest path victim→hub | ≤3 hops |
| UT-19 | Shortest path no path | None (not error) |
| UT-20 | Neighbourhood extraction | ≥5 neighbours for AC381 |
| UT-21 | Cluster detection | CLUSTER-01 found |
| UT-22 | Trail reconstruction | ≥4 hops, ≤30 min |
| UT-23 | Targeted trail | Victim→hub in 3 hops |
| UT-24 | Unknown source trail | Clean error |
| UT-25 | Disconnected graph trail | "No trail found" |
| UT-26 | Trail temporal contiguity | All hops ≤60 min gap |
| UT-27 | Alerts generated | rapid_multi_hop present |
| UT-28 | Pipeline load | Complete status |
| UT-29 | Dashboard API populated | 200 + metrics |
| UT-30 | Account detail + 404 | 200 + 404 |
| UT-30 | Network ego graph | 200 + nodes/edges |
| UT-31 | Trace money + no-trail | 200 both cases |
| UT-31 | Priority queue | AC381 first |
| UT-32 | Investigation lifecycle | Create→view→escalate→400 invalid |
| UT-33 | False positive requires reason | 400 without reason |
| UT-34 | Account classification | 200 |
| UT-35 | Audit logged | ≥1 entry |
| UT-36 | Transaction filters | 200 + correct results |
| UT-37 | CSV export priority | 200 + CSV content |
| UT-38 | CSV upload invalid → 422 | 422 + message |
| UT-39 | CSV upload valid → complete | 200 + 39 valid |

### 2. Manual Verification (Round 4 Specific)

| Test ID | Test Name | Steps | Expected |
|---------|-----------|-------|----------|
| MV-01 | Tracing disclaimer displayed | Login → Money Trail → Trace AC9001 | Disclaimer banner visible |
| MV-02 | Evidence tab shows transactions | Money Trail → Evidence tab | Table with 5 hops, clickable TX IDs |
| MV-03 | Evidence disclaimer shown | Money Trail → Evidence tab | Disclaimer at bottom |
| MV-04 | Tracing disclaimer on trail | Trail response | `tracing_disclaimer` field present |
| MV-04 | AccountDetail Next Steps card | Account AC381 → scroll to bottom | 4 action buttons |
| MV-05 | AccountDetail Data Provenance | Account AC381 → bottom | Detection method, dataset, timestamp |
| MV-05 | NetworkExplorer Next Steps | Network (no selection) → bottom | 3 action buttons |
| MV-06 | Selected account badge | Network → click node | Badge + "View Account" button |
| MV-07 | MoneyTrail Evidence tab | Trace → click Evidence tab | Table with TX IDs + View buttons |
| MV-07 | Evidence disclaimer | Evidence tab bottom | Disclaimer about tracing limits |
| MV-08 | Investigation review_decision | Create inv → PATCH review_decision | 200 + detail shows decision |
| MV-09 | Investigation reopen | Resolve → reopen | Status back to open |
| MV-10 | Reset demo with confirm | POST /reset-demo confirm=true | Complete, preserved investigations |
| MV-11 | Reset demo without confirm | POST /reset-demo no body | 400 error |
| MV-12 | Risk disclaimer exact text | Dashboard/Priority/Account | "Risk scores support investigative prioritization. They do not establish fraud or guilt." |
| MV-13 | Tracing disclaimer exact text | Trail response | "This path shows a temporally connected transaction sequence..." |

### 3. End-to-End Demo Journey

| Step | Action | Expected |
|------|--------|----------|
| E2E-01 | Open http://localhost:5173 | Login page loads |
| E2E-02 | Login as investigator | Redirect to dashboard |
| E2E-03 | Dashboard shows metrics | 3205 tx, 1402 accounts, 65 suspicious |
| E2E-04 | Click "Reveal Hidden Network" | Graph transitions to show cluster |
| E2E-05 | Priority Accounts → AC381 | Risk 90.3, disclaimer shown |
| E2E-06 | Click AC381 → Account Detail | 8 reasons, contributor bars, disclaimer |
| E2E-07 | Click "Explore Network" | Network page with ego view |
| E2E-08 | Click "Trace Money Trail" | Money Trail with source AC9001 |
| E2E-09 | Trace → Evidence tab | 5 hops table with TX IDs |
| E2E-10 | Create Investigation | INV-XXXX created |
| E2E-11 | Set review_decision | confirmed_suspicious shown |
| E2E-12 | Resolve → Reopen | Status back to open |
| E2E-13 | Admin Audit Log | 100+ entries including our actions |

### 4. Regression Tests (Critical Paths)

| Test ID | Test Name | Before Round 4 | After Round 4 |
|---------|-----------|----------------|---------------|
| RG-01 | Login all roles | ✅ | ✅ |
| RG-02 | Dashboard loads | ✅ | ✅ |
| RG-03 | Account detail loads | ✅ | ✅ |
| RG-04 | Network graph renders | ✅ | ✅ |
| RG-05 | Money trail reconstruction | ✅ | ✅ |
| RG-06 | Cluster detection | ✅ | ✅ |
| RG-07 | Alert generation | ✅ | ✅ |
| RG-08 | Investigation CRUD | ✅ | ✅ |
| RG-09 | CSV upload/validation | ✅ | ✅ |
| RG-10 | Export CSV | ✅ | ✅ |
| RG-11 | Audit logging | ✅ | ✅ |
| RG-12 | RBAC enforcement | ✅ | ✅ |
| RG-13 | Frontend build | ✅ | ✅ |
| RG-14 | All 46 unit tests pass | ✅ | ✅ |

## Test Environment

- **Backend**: Python 3.13, FastAPI, SQLite (WAL)
- **Frontend**: React 18 + Vite, Cytoscape.js, Recharts, Leaflet
- **Test Runner**: pytest + FastAPI TestClient
- **Demo Data**: 3,205 transactions, 1,402 accounts (synthetic)

## Pass/Fail Criteria

- **Automated**: All 46 tests must pass
- **Manual**: All 16 Round 4 checks must pass
- **E2E**: All 13 demo journey steps must work
- **Regression**: All 14 critical paths must remain working
- **Build**: Frontend must compile without errors

## Schedule

| Phase | Duration | Target |
|-------|----------|--------|
| Automated test run | 3 min | Before each commit |
| Manual verification | 15 min | After each feature |
| E2E demo run | 5 min | Before Round 4 complete |
| Full regression suite | 5 min | Before Round 4 complete |

## Defect Tracking

| ID | Description | Severity | Status |
|----|-------------|----------|--------|
| DEF-01 | JWT key length warning | Low | Documented |
| DEF-02 | `datetime.utcnow()` deprecation | Low | Documented |
| DEF-03 | Frontend bundle >500KB | Low | Acceptable for demo |
| DEF-04 | Leaflet map synthetic coords | Low | Documented |

## Sign-off

| Role | Name | Date | Status |
|------|------|------|--------|
| Developer | - | 2026-10-09 | ✅ Complete |
| QA Lead | - | 2026-10-09 | ✅ Passed |
| Security Review | - | 2026-10-09 | ✅ Reviewed |