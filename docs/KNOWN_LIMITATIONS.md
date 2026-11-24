# CYBERTRACK — Known Limitations

> **CyberTrack is a Smart India Hackathon prototype.** The following
> limitations are intentional and disclosed rather than hidden.

---

## Data & Model

| Limitation | Impact | Mitigation |
| ---------- | ------ | ---------- |
| Synthetic demo data only | Patterns are deliberately planted; real mule networks are noisier | Clearly labelled "Prototype Environment — Synthetic Data" on every page |
| Risk weights are heuristic | Not calibrated against labelled fraud data | Weights configurable in `app/config.py`; disclaimer shown |
| Isolation Forest (5% contamination) | Unsupervised anomaly detection — flags unusual, not necessarily fraud | Labelled "Isolation Forest" or "Analytical fallback" on every score |
| Deterministic fallback | Used if scikit-learn unavailable | Explicitly reported as "Analytical fallback" |
| Trail follows largest-amount branch | When money splits, only one branch is shown | Branching count shown; separate traces required for other branches |
| Amount decay not modelled | Tracked amount = branch amount, not full original sum | `amount_difference` and `passed_forward_pct` shown |

---

## Trail Reconstruction

| Limitation | Impact | Mitigation |
| ---------- | ------ | ---------- |
| Temporal contiguity enforced (30 min hop gap) | May miss legitimate long-gap transfers | Configurable via `hop_gap_minutes` |
| DFS depth limited to 10 hops | Very long chains may be truncated | Max hops parameter exposed |
| Greedy downstream walk (no destination) | Follows largest amounts; may not find true terminal | Explicit destination parameter available |
| No legal tracing claim | Path = temporal sequence, not proof of fund flow | **Disclaimer shown on every trail response** |

---

## Technical / Infrastructure

| Limitation | Impact | Status |
| ---------- | ------ | ------ |
| SQLite (WAL) only | Single-writer, limited concurrency | Repository layer ready for PostgreSQL |
| JWT secret 31 bytes (<32) | Below RFC 7518 minimum | Documented; change before production |
| `datetime.utcnow()` deprecation | Cosmetic warnings | To fix before production |
| No rate limiting | API abuse possible in prod | Documented |
| No CSRF protection | Cookie-based flows vulnerable | JWT in localStorage only |
| No account lockout | Brute-force possible | Documented |
| No audit log integrity (hash chaining) | Log tampering not detected | Documented |
| No PII masking in audit log | Investigator IDs logged | Minimal data stored |

---

## Frontend / UX

| Limitation | Impact | Status |
| ---------- | ------ | ------ |
| No React unit tests | Regression risk on UI changes | Acceptable for hackathon |
| No E2E browser tests | End-to-end regression risk | Acceptable for hackathon |
| Bundle size 1.06 MB | Slow initial load on slow connections | Code-splitting could help |
| Leaflet map uses synthetic coords | Not real geospatial intelligence | Clearly labelled "Synthetic demonstration location" |
| No mobile/tablet optimisation | Desktop-first | Acceptable for investigator console |
| No accessibility audit (WCAG) | Potential a11y gaps | Acceptable for prototype |

---

## Integrations (Future Scope)

| Integration | Status | Notes |
| ----------- | ------ | ------ |
| Bank transaction APIs | Future | Labelled "Future Authorized Integration" |
| I4C workflow | Future | Adapter interface exists |
| Real-time transaction streams | Future | Pipeline can be streamed |
| Geospatial intelligence service | Future | Leaflet prepared |
| Advanced graph/sequence models | Future | Architecture supports pluggable models |

---

## Legal / Process

| Limitation | Mitigation |
| ---------- | ---------- |
| Risk scores ≠ fraud determination | Disclaimer on every risk display |
| No autonomous decisions | Human-in-the-loop enforced |
| No real institutional data | Synthetic data warning everywhere |
| Prototype not production-ready | `LIMITATIONS.md`, `SECURITY.md`, `README.md` all state this |

---

## What Would Need to Change for Production

1. Replace demo credentials with real IdP (OIDC/SAML)
2. Rotate JWT secret to ≥32 bytes, store in vault
3. Migrate SQLite → PostgreSQL with connection pooling
4. Add rate limiting (Redis + middleware)
5. Add CSRF for any cookie flows
6. Add account lockout after failed logins
7. Add audit log integrity (Merkle tree / hash chain)
8. Add PII masking in audit export
9. Add React unit tests + Playwright E2E
10. Add monitoring (Prometheus/Grafana), alerting
11. Add CI/CD with security scanning
12. Run penetration test and code audit
13. Validate risk model against real labelled data
14. Connect authorised institutional data sources only
15. Obtain legal/compliance review for jurisdiction