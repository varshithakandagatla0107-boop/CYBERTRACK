# CYBERTRACK — Verification Report

**Audit Date:** 2026-10-12
**Git Commit:** (to be filled after git init)
**Auditor:** Senior Staff Engineer (remediation)

---

## Phase 0: Baseline & Scaffolding

- [ ] `docs/AUDIT_BASELINE.md` created
- [ ] `docs/DECISIONS.md` created
- [ ] `docs/VERIFICATION_REPORT.md` created
- [ ] `.gitignore` covers all required patterns
- [ ] `.env.example` created
- [ ] `Makefile` with targets: setup, test, lint, build, run, demo, package, clean
- [ ] `requirements-dev.txt` with pytest, pytest-cov, httpx, ruff, mypy
- [ ] Git initialized and baseline committed

## Phase 1: Correctness

### 1.1 CSV Amount Misalignment
- [ ] Fix: validate all columns in one DataFrame before filtering
- [ ] Fix: carry stable `source_row` (1-based CSV row number) through validation
- [ ] Test: out-of-order timestamps with amounts 500, 100, 900
- [ ] Test: mixed valid/rejected rows interleaved
- [ ] Test: duplicate timestamps, stable ordering
- [ ] Property test: shuffle CSV 50 times, amounts invariant

### 1.2 Input Validation
- [ ] Reject & report per-row: missing ID, duplicate ID, missing sender/receiver, self-transfer, bad amount, bad timestamp, bounds
- [ ] Normalize timestamps to UTC; document naive=UTC assumption
- [ ] Ingestion summary: read/accepted/rejected counts, reasons, first N rejected rows
- [ ] CSV injection guard on export
- [ ] Oversized field guard

### 1.3 End-to-End Amount Integrity
- [ ] Integration test: upload → ingest → features → graph → scoring → trails → report; amounts match at every stage

## Phase 2: Deterministic Startup & Deployment

### 2.1 Frontend Static Serving
- [ ] Resolve paths with `pathlib.Path(__file__).resolve().parents[N]`
- [ ] Check `frontend/dist/index.html` exists; fail startup in prod if missing
- [ ] SPA fallback for non-API routes; `/api/*` excluded
- [ ] Test: CWD = repo root, `backend/`, `/tmp` → `GET /` works

### 2.2 Database Configuration
- [ ] SQLite only; parse `sqlite:///` URLs; reject `postgres://` with clear error
- [ ] Create parent directory if missing; validate writability
- [ ] Update deployment guide: remove PostgreSQL, add "Future work" section

### 2.3 Environment Variables
- [ ] Standardize `CYBERTRACK_JWT_EXPIRE_MINUTES`; deprecate `CYBERTRACK_JWT_EXPIRE`
- [ ] `.env` loading via python-dotenv + pydantic-settings; precedence: env > .env > defaults
- [ ] Single typed `Settings` class with validation
- [ ] Test: docs table vs Settings fields never drift

### 2.4 Health & Observability
- [ ] `GET /api/health` (liveness) and `GET /api/ready` (DB, schema, frontend, secret, analysis)
- [ ] Replace broad exception handlers with specific + logging
- [ ] Structured logging with request IDs; log level by env

## Phase 3: Security Hardening

### 3.1 Authentication & Secrets
- [ ] Production mode: refuse start if JWT_SECRET unset, <32 bytes, or equals fallback
- [ ] Demo mode: random per-process secret + banner
- [ ] Remove shared demo credentials from production; seed demo users only in `MODE=demo`
- [ ] CLI: `python -m app.cli create-user --role ...` with password prompt
- [ ] Argon2/bcrypt with sane cost; min length; constant-time compare
- [ ] JWT in HTTP-only, Secure, SameSite=Strict cookie + CSRF double-submit
- [ ] Short access token + refresh/sliding expiry
- [ ] Frontend API helper + CSV upload use cookie auth
- [ ] Logout clears cookie server-side
- [ ] RBAC test matrix: every endpoint × role (401/403 + audit)
- [ ] Rate limiting (slowapi) on login/upload; account lockout/backoff
- [ ] Security headers: CSP, X-Content-Type-Options, X-Frame-Options, Referrer-Policy, HSTS, strict CORS

### 3.2 Upload Safety
- [ ] Enforce size before loading: check Content-Length, stream in chunks to temp file, abort at limit
- [ ] Validate extension + content (CSV sniff, encoding, max rows/cols/cell)
- [ ] Document reverse-proxy limit for production
- [ ] Tests: oversize → 413, memory bounded, temp cleanup on failure

### 3.3 Audit Integrity
- [ ] Hash-chained audit records: `hash = SHA256(prev_hash || canonical_json(event))`
- [ ] `GET /api/audit/verify` walks chain, reports first break
- [ ] Fail closed on audit write failure for state-changing ops
- [ ] Document limits (DB-level, not external append-only)

### 3.4 Data Privacy
- [ ] Docs/UI: bundled dataset = synthetic; uploaded = user-provided
- [ ] Data retention note + "Reset data" (admin, audited)

## Phase 4: Data Layer Reliability

- [ ] Explicit transactions with rollback for multi-step ops
- [ ] Analysis-state marker (`analysis_run_id`, status, started/finished, dataset hash)
- [ ] Mark results stale on new upload/reset
- [ ] Lock conflicting operations (single-writer analysis job)
- [ ] SQLite: WAL, busy_timeout, foreign_keys=ON
- [ ] Tests: concurrent upload+reset; interrupted analysis → "failed" status; recovery on restart

## Phase 5: Analytical Credibility

- [ ] Edge-case graph/trail tests: self-loops, parallel edges, cycles, fan-out/in, ambiguous paths, hop limits, large candidates (cap + report truncation)
- [ ] Feature extraction tests: time zones, duplicate records, zero-variance, single account, large datasets (no NaN/div-zero)
- [ ] Anomaly method transparency: API/UI states method + params, fixed random_state
- [ ] Evidence taxonomy: Observed / Analytical / Decision labels in API + UI
- [ ] Cash-out intelligence = synthetic/illustrative with provenance + confidence range
- [ ] Scoring evaluation: `backend/tools/evaluate_scoring.py` on labelled synthetic benchmark (fixed seed) → precision/recall/F1/PR-AUC, top-K hit rate, weight sensitivity → `docs/SCORING_EVALUATION.md`
- [ ] Performance benchmarks: `backend/tools/benchmark.py` at 10k/100k/500k txns

## Phase 6: Frontend Quality

- [ ] Show dataset id / analysis run / timestamp; "stale results" banner
- [ ] Error handling: login fail, session expiry, 401/403/413/429/500, empty dataset, upload errors, graph 0/1/large nodes, trail no-results
- [ ] Role-restricted controls hidden + API enforced
- [ ] Accessibility: semantic landmarks, labels, focus order/visible rings, keyboard graph controls, contrast ≥ AA, prefers-reduced-motion, chart data tables
- [ ] `eslint-plugin-jsx-a11y` + axe in tests
- [ ] Responsive: 360, 768, 1024, 1440 px; table scroll containers
- [ ] Vitest + RTL (unit/component); Playwright (e2e): login, expiry, upload failure, empty data, graph, trail, role restrictions, investigation, full demo script
- [ ] `test`, `test:e2e`, `lint`, `typecheck` scripts
- [ ] Production build: zero TS/ESLint errors; lazy-load heavy views

## Phase 7: Packaging & Deployment

- [ ] Multi-stage Dockerfile (frontend build → slim Python, non-root, HEALTHCHECK)
- [ ] `docker-compose.yml` with named volume for SQLite, env-file, restart policy
- [ ] Caddy/nginx example with TLS + upload limits
- [ ] Pinned deps: `requirements.txt` exact, `package-lock.json` committed
- [ ] `pip-audit` + `npm audit` in `make audit`
- [ ] Deploy examples: Docker, VM (systemd + reverse proxy), PaaS (Render/Railway/Fly) — tested or marked untested
- [ ] CI: `.github/workflows/ci.yml` (lint, backend tests+cov, frontend tests, build, Docker build, smoke test)
- [ ] `make package` → `cybertrack-release.zip` (source, lockfiles, assets, tests, docs only; exclude node_modules, dist, __pycache__, .pyc, .env, *.db)
- [ ] Clean-machine test: fresh clone → clone → login screen (fix all steps)

## Phase 8: Documentation Reconciliation

- [ ] Demo counts/scores from `backend/tools/generate_demo_facts.py` (seeded)
- [ ] Rewrite README: what/quickstart/env-table/roles/demo/tests/deploy/limitations/security
- [ ] Fix all doc/code mismatches (DB, env, static, Postgres, synthetic claims, "all checks passed")
- [ ] PS-35 vs PS-26184 → `docs/OPEN_QUESTIONS.md`, single `PROBLEM_STATEMENT_ID` constant
- [ ] `KNOWN_LIMITATIONS.md`, `SECURITY.md` (threat model, controls, remaining)
- [ ] `VERIFICATION_REPORT.md`: commit hash, date, exact commands + real outputs

## Phase 9: Release Gate

- [ ] All findings closed with test/verification
- [ ] Backend + frontend tests pass; coverage on engine/, security/, routers/ reported
- [ ] `make audit` no high/critical unaddressed
- [ ] App starts from repo root, backend/, Docker; `/api/ready` green
- [ ] Production mode refuses weak/missing secrets
- [ ] Jury demo script runs end-to-end (Playwright)
- [ ] Release archive lean + reproducible from lockfiles
- [ ] Docs contain no unverifiable claims

---

## Verification Results Log

| Check | Status | Evidence | Date |
|-------|--------|----------|------|
| Baseline tests (46) | PASS | pytest output | 2026-10-12 |
| Frontend build | PASS | npm run build | 2026-10-12 |
| Manual verification (16 checks) | PASS | verify_final_round5.py | 2026-10-12 |
| E2E demo (13 steps) | PASS | ROUND5_DEMO_SCRIPT.md | 2026-10-12 |
| Regression (14 paths) | PASS | ROUND5_TEST_RESULTS.md | 2026-10-12 |

---

*Last updated: 2026-10-12*