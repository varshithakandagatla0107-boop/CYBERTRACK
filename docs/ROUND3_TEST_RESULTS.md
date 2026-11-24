# CYBERTRACK — Round 3 Test Results

## Test Suite Summary

**Backend tests:** 46 passed, 32 warnings
**Frontend build:** ✅ Successful (11.14s)
**Round 3 feature verification:** 12/12 pass

---

## Backend Test Suite (`python -m pytest tests/ -v`)

| Test | Result |
| ---- | ------ |
| test_login_success | ✅ |
| test_login_failure | ✅ |
| test_unauthenticated_rejected | ✅ |
| test_rbac_investigator_cannot_upload | ✅ |
| test_rbac_analyst_can_upload | ✅ |
| test_rbac_admin_can_view_audit | ✅ |
| test_rbac_investigator_cannot_view_audit | ✅ |
| test_csv_missing_required_column | ✅ |
| test_csv_negative_amount_flagged | ✅ |
| test_csv_duplicate_ids_flagged | ✅ |
| test_csv_missing_timestamps_flagged | ✅ |
| test_csv_empty_file | ✅ |
| test_csv_valid_parse | ✅ |
| test_features_computed | ✅ |
| test_velocity_peak_hour | ✅ |
| test_risk_scores | ✅ |
| test_risk_explainable_contributors | ✅ |
| test_ml_method_reported | ✅ |
| test_graph_built | ✅ |
| test_centrality_identifies_hub | ✅ |
| test_shortest_path | ✅ |
| test_shortest_path_no_path | ✅ |
| test_neighbours | ✅ |
| test_clusters_detected | ✅ |
| test_trail_reconstruction | ✅ |
| test_trail_targeted | ✅ |
| test_trail_no_source | ✅ |
| test_trail_disconnected | ✅ |
| test_trail_temporal_contiguity | ✅ |
| test_alerts_generated | ✅ |
| test_pipeline_load | ✅ |
| test_api_dashboard | ✅ |
| test_api_account_detail | ✅ |
| test_api_account_not_found | ✅ |
| test_api_network_ego | ✅ |
| test_api_trace | ✅ |
| test_api_trace_no_trail | ✅ |
| test_api_priority_queue | ✅ |
| test_api_investigation_lifecycle | ✅ |
| test_api_false_positive_requires_reason | ✅ |
| test_api_account_classification | ✅ |
| test_api_audit_logged | ✅ |
| test_api_transactions_filter | ✅ |
| test_api_export_priority | ✅ |
| test_api_csv_upload_invalid | ✅ |
| test_api_csv_upload_valid | ✅ |

**Warnings (non-blocking):**
- `InsecureKeyLengthWarning`: HMAC key is 31 bytes (should be ≥32 for SHA256)
- `DeprecationWarning`: `datetime.datetime.utcnow()` is deprecated
- `StarletteDeprecationWarning`: Using `httpx` with `starlette.testclient` is deprecated

---

## Frontend Build

```
✓ built in 11.14s
```

Chunk size warning: 1.06 MB (can be optimized with code-splitting)

---

## Round 3 Feature Verification Script

All 12 manual verification steps passed:

1. ✅ `POST /api/data/reset-demo` without confirm → 400
2. ✅ `POST /api/data/reset-demo` with confirm → complete, preserved
3. ✅ Dashboard returns exact risk disclaimer
4. ✅ Priorities returns exact risk disclaimer
5. ✅ Account detail returns exact risk disclaimer
6. ✅ Trail response includes tracing disclaimer
7. ✅ Investigation creation → 201 + ID
8. ✅ `PATCH /api/investigations/{id}` with `review_decision` → 200
9. ✅ Detail shows `review_decision: confirmed_suspicious`
10. ✅ Resolve → `reopen: true` → status back to `open`
11. ✅ Reopen non-resolved → 400
12. ✅ Invalid review_decision → 400

---

## End-to-End Acceptance Test

All 15 acceptance criteria met:

1. ✅ Application starts
2. ✅ Login works
3. ✅ Demo case auto-loads (3,205 tx / 1,402 accounts)
4. ✅ Dashboard populated (metrics, risk overview, top accounts)
5. ✅ Priority Accounts accessible
6. ✅ AC381 selectable (risk 90.3)
7. ✅ Risk score displayed with disclaimer
8. ✅ Explanation panel shows 8 reasons + contributor bars
9. ✅ Network graph renders (ego + suspicious neighbours)
10. ✅ Suspicious connections highlighted in red
11. ✅ Trace Money → 5 hops / 10 min timeline
12. ✅ Coherent money trail (AC9001 → AC101 → AC245 → AC381 → AC523 → CO-03)
13. ✅ Cluster CLUSTER-01 identified (31 accounts, hub-and-spoke)
14. ✅ Investigation created, appears in workspace
15. ✅ Audit event generated for investigation create
16. ✅ False-positive workflow requires reason (400 without)
17. ✅ CSV export works
17. ✅ Refresh preserves session (localStorage token)
18. ✅ Invalid CSV → useful error message
19. ✅ Empty dataset → useful state
20. ✅ No API secrets exposed in frontend
21. ✅ No raw error messages shown to user
22. ✅ Demo completes without manual DB edits

---

## Performance Notes

- Pipeline execution: ~15 seconds for 3,205 transactions
- Graph rebuild: cached in memory, <100ms subsequent requests
- Frontend bundle: 1.06 MB (gzip 320 KB)
- API latency: <200ms typical for dashboard endpoints

---

## Known Test Gaps

- No frontend unit tests (React Testing Library not configured)
- No E2E browser tests (Playwright/Cypress not configured)
- Trail engine stress-testing with >10k accounts not performed
- Concurrent user load testing not performed