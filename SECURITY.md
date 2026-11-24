# CYBERTRACK — Security

## Implemented controls

| Control | Implementation |
| ------- | -------------- |
| Authentication | JWT bearer sessions (HS256), 8-hour expiry |
| Password storage | PBKDF2-HMAC-SHA256, 120k iterations, per-user salt |
| Role-based access | Investigator / Analyst / Admin permission matrix |
| Protected routes | Frontend guards + backend dependency enforcement |
| Input validation | Server-side CSV schema, amount, timestamp, duplicate checks |
| File validation | Extension allow-list (.csv), 25 MB size limit |
| Parameterised DB | All SQL uses bound parameters — no string interpolation |
| Session expiry | Expired tokens rejected with clear message |
| Audit logging | Who / what / when / result for key actions |
| Identifier masking | `mask_account()` helper available (XXXXXX381) |
| Error handling | Human-readable messages; no stack traces exposed |
| Secrets | JWT secret via `CYBERTRACK_JWT_SECRET` env var; never in source |

## Role matrix

| Capability | Investigator | Analyst | Admin |
| ---------- | :--: | :--: | :--: |
| View, trace, investigate, note, update status, export | ✓ | ✓ | ✓ |
| Upload datasets, run analysis, review models | — | ✓ | ✓ |
| Manage users, full audit log, configure | — | — | ✓ |

## Data privacy

- All data is **synthetic demonstration data**.
- The warning is displayed on login, in the
  sidebar, and on every major page.
- No real financial information is used anywhere.

## Demo credentials

All three roles share the password
`cybertrack-demo`. This is intentional for the
hackathon prototype and is documented on the
login screen. **Change before any non-demo use.**

## Deployment checklist (beyond prototype)

- [ ] Set `CYBERTRACK_JWT_SECRET` to a strong
      random value (≥ 32 bytes)
- [ ] Replace demo passwords with real identity
      provider integration
- [ ] Serve over HTTPS only
- [ ] Replace SQLite with PostgreSQL
- [ ] Add rate limiting middleware
- [ ] Add CSRF protection for cookie flows
- [ ] Log to a secured, append-only store
- [ ] Enable account lockout after failed attempts
- [ ] Connect authorised institutional data sources
      only (currently "Future Authorized Integration")

## What CyberTrack does NOT do

- It does not declare guilt or fraud.
- It does not make autonomous decisions.
- It does not connect to any real bank, police,
  government, or financial API.
- It does not store passwords in frontend code.
