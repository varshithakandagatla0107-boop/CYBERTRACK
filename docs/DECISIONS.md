# CYBERTRACK — Engineering Decisions Log

| Date | Decision | Context | Alternatives Considered | Status |
|------|----------|---------|------------------------|--------|
| 2026-10-12 | SQLite only for this release | Simplifies deployment; PostgreSQL support was claimed but not working | PostgreSQL, SQLite only | ✅ Accepted |
| 2026-10-12 | JWT in HTTP-only cookies with CSRF | localStorage is vulnerable to XSS; cookie with SameSite=Strict is more secure | localStorage, HttpOnly cookie, Authorization header | ✅ Accepted |
| 2026-10-12 | Demo mode = random JWT secret per process | Avoids hardcoded secret in production; demo mode is explicitly insecure | Fixed secret, env var only | ✅ Accepted |
| 2026-10-12 | SQLite WAL mode + busy_timeout | Better concurrency for prototype | Default rollback journal | ✅ Accepted |
| 2026-10-12 | Timestamp parsing: naive = UTC | Consistent timezone handling; IST would be India-specific | IST, local timezone | ✅ Accepted |
| 2026-10-12 | Duplicate transaction ID = keep first | First record wins; simple deterministic rule | Keep last, reject all | ✅ Accepted |
| 2026-10-12 | Single-writer SQLite with WAL | Simpler than connection pooling for prototype | Connection pool, multiple writers | ✅ Accepted |
| 2026-10-12 | CSV amount misalignment fix: use stable source_row_id | Amount was misaligned after sorting due to index mismatch | Keep original buggy code, add test only | ✅ Accepted |
| 2026-10-12 | Static file serving uses project-root-relative path | Fixes CWD issues when running from backend/ or elsewhere | Absolute path from config | ✅ Accepted |
| 2026-10-12 | Environment loading via python-dotenv + pydantic-settings | Explicit .env loading with precedence rules | os.environ only | ✅ Accepted |
| 2026-10-12 | SQLite only for this release; PostgreSQL = future work | Claimed Postgres support was broken; removes false claim | Full Postgres support now | ✅ Accepted |
| 2026-10-12 | JWT in HTTP-only cookies with CSRF double-submit | localStorage vulnerable to XSS | localStorage, header-based | ✅ Accepted |
| 2026-10-12 | Demo mode = random JWT secret per process | Production must provide real secret; demo gets ephemeral | Fixed fallback secret | ✅ Accepted |
| 2026-10-12 | Upload: stream to temp file, check size during stream | Current code reads entire file into memory before limit check | Read all then check | ✅ Accepted |
| 2026-10-12 | Audit log hash chaining | Each event stores prev_hash and hash = SHA256(prev || canonical_json) | No integrity protection | ✅ Accepted |
| 2026-10-12 | Audit write failure = fail closed for state-changing ops | Production requires audit trail integrity | Fire-and-forget | ✅ Accepted |
| 2026-10-12 | Analysis state marker (analysis_run_id) | Prevents showing stale results after upload/reset | No state tracking | ✅ Accepted |
| 2026-10-12 | Lock for conflicting operations (single-writer) | Prevents concurrent upload+reset from corrupting state | No locking | ✅ Accepted |
| 2026-10-12 | Evidence taxonomy: Observed / Analytical / Decision | Clear separation in API and UI | No taxonomy | ✅ Accepted |
| 2026-10-12 | Cash-out intelligence = synthetic/illustrative with provenance | Never present as real-world prediction | Could be presented as real | ✅ Accepted |
| 2026-10-12 | Scoring evaluation on synthetic benchmark with fixed seed | No real-world accuracy claim; weight sensitivity analysis | No evaluation, or claim real accuracy | ✅ Accepted |
| 2026-10-12 | Frontend: HTTP-only cookie + CSRF double-submit | Replace localStorage JWT | Keep localStorage | ✅ Accepted |
| 2026-10-12 | Accessibility: WCAG AA target, axe in CI | Legal requirement in many jurisdictions | No accessibility work | ✅ Accepted |
| 2026-10-12 | Docker: multi-stage, non-root user, healthcheck | Production-ready container | No container | ✅ Accepted |
| 2026-10-12 | Lockfiles committed (requirements.txt, package-lock.json) | Reproducible builds | Loose versions | ✅ Accepted |
| 2026-10-12 | PS-35 as canonical problem ID | Repo says PS-35 throughout; earlier context had PS-26184 | Keep PS-35, document in OPEN_QUESTIONS.md | ✅ Accepted |

---