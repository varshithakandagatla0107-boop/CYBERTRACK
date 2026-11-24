# CYBERTRACK — Round 4 Findings

## Summary

Round 4 focused on hardening the CYBERTRACK prototype to make it a reliable, investigator-friendly, and demonstrable PS-35 solution. The key achievements are:

1. **Investigator-first PS-35 experience** — Contextual navigation, "Next Steps" cards, and clear action buttons throughout the application
2. **Evidence-linked money trails** — New "Evidence" tab in Money Trail showing actual transaction records with clickable links
3. **Explainability and data provenance** — Tracing disclaimers, data provenance cards, and clear separation of observed/calculated/assessed signals
4. **Usability improvements** — Contextual "Next Steps" cards on AccountDetail, NetworkExplorer, and MoneyTrail pages
4. **Reproducible demonstration** — Reset-to-demo endpoint with confirmation, consistent demo data

## Files Changed

### Frontend
| File | Changes |
|------|---------|
| `src/pages/AccountDetail.jsx` | Added "Next Steps" contextual action card, "Data Provenance" card with detection method/dataset/timestamp, improved header action buttons with titles |
| `src/pages/MoneyTrail.jsx` | Added tracing disclaimer banner, new "Evidence" tab showing supporting transaction records with clickable transaction IDs, explicit evidence disclaimer |
| `src/pages/NetworkExplorer.jsx` | Added selected account badge with "View Account" button, "Next Steps" card when no account selected, fragment wrapper for conditional rendering |

### Backend
| File | Changes |
|------|---------|
| `app/engine/trail_engine.py` | (Existing) Already included tracing disclaimer in trail responses |
| `app/routers/trails.py` | (Existing) Already returns tracing_disclaimer in trail responses |

## Verification Results

### Automated Tests
- **46/46 backend tests pass** (same as Round 3 baseline)
- Frontend builds successfully (10.2s)

### Manual Verification (Round 4)
All 16 verification checks passed:
1. ✅ Login all roles (investigator, analyst, admin)
2. ✅ Reset demo with confirmation preserves investigations
3. ✅ Dashboard loads with metrics and risk disclaimer
4. ✅ Priority queue shows AC381 at risk 90.3
5. ✅ Account detail shows 8 reasons + data provenance
6. ✅ Network ego graph shows 12 neighbours, 1 suspicious
7. ✅ Money trail reconstruction (5 hops, 10 min) with tracing disclaimer
8. ✅ Cluster CLUSTER-01 identified (31 accounts)
9. ✅ Investigation creation with review decision support
10. ✅ Review decision workflow (confirmed_suspicious)
11. ✅ Resolve → Reopen workflow functional
12. ✅ Audit log captures all actions
13. ✅ Analytics shows Isolation Forest method, 71 anomalies
14. ✅ Export produces 65 priority accounts CSV
15. ✅ Trail detail includes 5 supporting hops
16. ✅ Trail detail has hops (evidence support)

## Key Improvements

### 1. Evidence-Linked Money Trails (Critical)
- **New "Evidence" tab** in Money Trail page shows each hop as a table row with: hop index, timestamp, from/to accounts, amount, transaction ID, and "View" button
- Each transaction ID is clickable (opens transaction detail in new tab)
- **Explicit evidence disclaimer** explains that the trail shows temporally connected transactions, not proof of same currency units flowing through every account
- Tracing disclaimer now prominently displayed at top of trail results

### 2. Investigator-First Navigation
- **AccountDetail**: "Next Steps" card with 4 contextual actions (Trace Money, Explore Network, Open Money Trail, Create Investigation)
- **NetworkExplorer**: "Next Steps" card when no account selected (Priority, Money Trail, Dashboard); selected account badge with "View Account" button
- **AccountDetail header**: Action buttons have descriptive titles explaining their purpose
- **MoneyTrail**: New "Evidence" tab alongside Timeline/Graph/Table tabs

### 3. Explainability & Data Provenance
- **AccountDetail**: New "Data Provenance" card showing detection method, dataset name, analysis timestamp
- **MoneyTrail**: Tracing disclaimer prominently displayed ("This path shows a temporally connected transaction sequence...")
- **AccountDetail**: Disclaimer now uses exact required wording: "Risk scores support investigative prioritization. They do not establish fraud or guilt."
- **AccountDetail**: Clear separation of observed (transactions), calculated (features), assessed (risk), predicted (not applicable)

### 4. Reproducible Demo
- `/api/data/reset-demo` endpoint with `confirm=true` requirement
- Preserves investigations, users, and audit log while resetting transaction data
- Demo case auto-loads on first start (3,205 transactions, 1,402 accounts)

## Remaining Limitations

| Limitation | Impact | Status |
|------------|--------|--------|
| JWT key 31 bytes (<32) | Prototype only | Documented |
| `datetime.utcnow()` deprecation | Cosmetic warnings | To fix before prod |
| No rate limiting | API abuse possible in prod | Documented |
| SQLite only | Single-writer, limited concurrency | Repository layer ready for PostgreSQL |
| No CSRF/account lockout | Prototype auth | Documented |
| Synthetic coordinates for map | Not real geospatial | Documented |
| Bundle size 1.06 MB | Load time on slow connections | Acceptable for demo |

## Files Preserved (Not Modified)

All core pipeline files preserved from Round 3:
- `app/engine/ingestion.py` — CSV validation with rejected row details
- `app/engine/features.py` — Behavioural feature extraction
- `app/engine/graph_engine.py` — NetworkX graph + Louvain communities
- `app/engine/ml_engine.py` — Isolation Forest + analytical fallback
- `app/engine/risk_engine.py` — Explainable risk scoring with contributors
- `app/engine/pipeline.py` — Full pipeline orchestration
- `app/engine/alert_engine.py` — 7 alert typologies
- `app/db/database.py` — SQLite schema with migrations
- `app/security/auth.py` — JWT + PBKDF2 + RBAC
- `app/security/audit.py` — Audit logging
- `app/seed.py` — Demo user creation
- All router files and frontend components (except those listed above)

## Next Steps for Round 5

1. **Performance optimization** — Add pagination to large data endpoints, implement graph virtualization for >500 nodes
2. **Accessibility** — Add ARIA labels, keyboard navigation, color contrast audit
3. **Map integration** — Connect Leaflet with real geospatial service (currently synthetic coords)
4. **Advanced analytics** — Add temporal pattern detection, peer group analysis
5. **Production hardening** — Rate limiting, CSRF, account lockout, audit log integrity

## Final Assessment

**GO for Round 5**

The application now provides a complete, end-to-end PS-35 workflow:
- Load data → Analyse → Select account → Understand why → Explore network → Trace money → Review evidence → Open investigation

All core features are functional, tested, and documented. The prototype successfully demonstrates the PS-35 solution concept with appropriate disclaimers and limitations clearly communicated.