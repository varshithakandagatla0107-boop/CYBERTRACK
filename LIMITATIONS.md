# CYBERTRACK — Limitations (Round 5)

**CyberTrack is a hackathon prototype.**
The following limitations are intentional and
disclosed rather than hidden.

## Data

- The demonstration case is **entirely synthetic**.
  Patterns are deliberately planted so the pipeline
  has something to find. Real mule networks are
  noisier and more adaptive.
- The demo dataset (~3,200 transactions / ~1,400
  accounts) is sized for instant demo loading, not
  production volume. The pipeline is designed to
  handle 1,000+ accounts / 10,000+ transactions,
  but has not been stress-tested at bank scale.

## Model

- The risk score is a **weighted heuristic
  (prototype analytical scoring model)**, not a
  validated statistical model. Weights are
  configurable in `app/config.py` but are not
  calibrated against labelled fraud data.
- Isolation Forest (5% contamination) is an
  unsupervised anomaly detector — it flags
  *unusual* behaviour, which is not the same as
  fraud. Legitimate high-velocity accounts
  (e.g. payroll) can score elevated.
- If scikit-learn is unavailable, a deterministic
  analytical fallback (robust z-score composite)
  is used and clearly labelled as such.

## Trail reconstruction

- Trails follow the **largest-amount** path within
  a 30-minute temporal gap. When money branches
  (as it does at AC381), the trail follows one
  branch; the others require separate traces.
- Amount decay across hops is not modelled —
  each hop's amount is the actual transaction
  amount, so "tracked amount" reflects the
  branch followed, not the full original sum.
- **Trail reconstruction assumes temporal contiguity
  (30-min hop gap). Real-world laundering may use
  longer gaps to evade detection.**

## Map / geospatial

- Leaflet map integration is prepared, but the
  demo uses synthetic city labels and coordinates
  clearly marked as demonstration data. No real
  geospatial service is connected.

## Integrations

- Bank APIs, I4C workflows, real-time streams,
  and authorised institutional feeds are
  **Future Authorized Integrations** — adapter
  points exist in the UI, but nothing is connected.

## Security

- Authentication is a prototype (shared demo
  password, HMAC JWT). Not production-grade.
- SQLite is used for demo simplicity; PostgreSQL
  is the intended production target.
- No rate limiting, CSRF protection, or account
  lockout in the prototype.
- **JWT secret is 31 bytes (below RFC 7518 minimum
  of 32 for HS256). Demo only.**
- **Audit log is append-only but not tamper-evident
  (no hash chaining).**

## Frontend

- **Bundle size 1.06 MB (gzip 320 KB)** — may be
  slow on slow connections. No code-splitting yet.
- **No accessibility audit (WCAG) performed.**
- **No frontend unit tests (React Testing Library)
  or E2E browser tests (Playwright/Cypress).**

## Legal / process

- Risk scores **support prioritisation and do not
  establish guilt or fraud**. All classifications
  are made by a human investigator.
- Real-world deployment would require authorised
  institutional data, security controls,
  validation, compliance review, and integration.
- **Demo data is synthetic. No real financial data
  used anywhere in the prototype.**

## Testing gaps

- No frontend unit tests (React Testing Library)
- No E2E browser tests (Playwright/Cypress)
- No load/stress testing at production scale
- No penetration testing performed
- No accessibility audit (WCAG)

## Round 5 Status

All Round 5 acceptance criteria met:
- ✅ Core PS-35 pipeline verified end-to-end
- ✅ Evidence-linked money trails with disclaimers
- ✅ Investigator-first experience with contextual nav
- ✅ Full explainability and data provenance
- ✅ Reproducible demo with confirmation-required reset
- ✅ No regressions (46 automated + 16 manual + 13 E2E pass)
- ✅ Documentation complete (7 new Round 5 documents)

## What Would Need to Change for Production

1. Replace demo auth with OIDC/SAML; rotate JWT secret (≥32 bytes)
2. Migrate SQLite → PostgreSQL with connection pooling
3. Add rate limiting, CSRF protection, account lockout
4. Add audit log integrity (hash chaining)
5. Add monitoring (Prometheus/Grafana), alerting
6. Add CI/CD with security scanning (SAST/DAST)
7. Run penetration test and code audit
8. Validate risk model on real labelled fraud data
9. Connect authorised institutional data sources only
10. Legal/compliance review for jurisdiction
11. Accessibility audit (WCAG 2.1 AA)
12. Frontend code-splitting for bundle size
13. Frontend unit tests + Playwright E2E tests
