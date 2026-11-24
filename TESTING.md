# CYBERTRACK — Testing

## Run the test suite

```bash
cd backend
python -m pytest tests/ -v
```

**46 tests** covering the full pipeline.

## Coverage

### Authentication & authorisation
- Login success / failure
- Unauthenticated requests rejected (401)
- Investigator cannot upload (403)
- Analyst can upload
- Investigator cannot view full audit log (403)
- Admin can view audit log

### CSV validation
- Missing required column → clear error
- Negative / non-numeric amounts → flagged
- Duplicate transaction IDs → flagged
- Missing/unparseable timestamps → flagged
- Empty file → error
- Valid CSV parses with correct counts

### Feature extraction
- Features computed for 1,000+ accounts
- Hub has high tx count, pass-through,
  counterparties
- Peak-hour velocity (not diluted average)

### Risk engine
- AC381 scores ≥ 70 (high)
- AC381 is the top-priority account
- Contributors are explainable (≥5 signals,
  pass-through ≥ 10 points)
- Detection method always reported

### Graph engine
- Graph built with 100+ nodes/edges
- Centrality identifies the hub
- Shortest path victim → hub (≤ 3 hops)
- No path → None (not an error)
- Neighbourhood extraction
- Cluster detection finds the fraud cluster
  (≥ 10 accounts, AC381 as intermediary)

### Trail engine
- Downstream trail: ≥ 4 hops, ≤ 30 min,
  ≥ 5 accounts
- Targeted trail: victim → hub in 3 hops
- Unknown source → clean error
- Disconnected graph → "no trail found"
- Temporal contiguity: every hop gap ≤ 60 min

### Alert engine
- Alerts generated, including rapid multi-hop

### API
- Dashboard populated
- Account detail + not-found (404)
- Ego network
- Trace + no-trail (clean error)
- Priority queue (AC381 first)
- Investigation lifecycle (create → view →
  escalate → invalid status rejected)
- False positive requires a reason (400)
- Account classification
- Audit log written
- Transaction filters
- CSV export
- CSV upload: invalid → 422 with message,
  valid → complete

## Manual acceptance test

The 25-point acceptance checklist from the
specification:

1. Open application → login page ✓
2. Login with `investigator` / `cybertrack-demo` ✓
3. Demo case auto-loads (or click Load
   Demonstration Case) ✓
4. Dashboard shows populated metrics ✓
5. Open Priority Accounts ✓
6. Select AC381 ✓
7. Risk score 90/100 appears ✓
8. Risk explanation (reasons + contributors) ✓
9. Network graph appears ✓
10. Suspicious connections highlighted (red) ✓
11. Click Trace Money ✓
12. Timeline appears ✓
13. Money trail is coherent (5 hops / 10 min) ✓
14. Cluster CLUSTER-01 identified ✓
15. Create investigation ✓
16. Investigation appears in workspace ✓
17. Audit event generated ✓
18. False-positive workflow requires reason ✓
19. CSV export works ✓
20. Refresh keeps session (localStorage) ✓
21. Invalid CSV → useful error ✓
22. Empty dataset → useful state ✓
23. No API secrets exposed ✓
24. No raw error messages ✓
25. Demo completes without DB edits ✓

## Known test characteristics

- Tests share a session-scoped SQLite database;
  upload tests run last by design.
- Test runtime ≈ 3 minutes (Isolation Forest
  on ~1,400 accounts dominates).
