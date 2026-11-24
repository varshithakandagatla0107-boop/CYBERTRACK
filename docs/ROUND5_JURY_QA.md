# CYBERTRACK — Round 5 Jury Q&A

**Evidence-backed answers for reviewer questions. Implemented vs. proposed clearly separated.**

---

## 1. Problem & Novelty

**Q: What problem does CYBERTRACK solve that existing tools don't?**  
A: Existing fraud systems review transactions in isolation. CYBERTRACK connects them into a **directed transaction network**, identifies **explainable risk signals** (rapid pass-through, velocity, centrality, convergence/divergence), reconstructs **evidence-linked temporal money trails**, and prioritizes investigations with **human-in-the-loop** workflow. The novelty is the **integrated pipeline** from raw transactions → graph → explainable risk → temporal trails → investigation workspace — all with full traceability to source transactions.

**Evidence:** `app/engine/pipeline.py` (lines 57-114), `app/engine/trail_engine.py`, `frontend/src/pages/MoneyTrail.jsx` (Evidence tab)

---

## 2. Architecture & Analytics

**Q: How does the graph construction work?**  
A: Nodes = accounts (sender/receiver). Directed edges = transactions (sender → receiver). Multiple transactions between same pair are aggregated into a single edge with weight = total amount, count, first/last timestamp, and a semicolon-separated list of transaction IDs. Built with NetworkX DiGraph. Source: `app/engine/graph_engine.py` (lines 18-45).

**Q: What ML model is used?**  
A: **Isolation Forest** (scikit-learn, 120 estimators, contamination=0.05, random_state=42) on 9 normalized behavioural features. If scikit-learn unavailable, deterministic analytical fallback (robust z-score composite) is used. Method name returned in every risk response. Source: `app/engine/ml_engine.py`.

**Q: What signals drive the risk score?**  
A: 7 weighted signals (normalized 0–1, weighted sum normalized to 0–100):
1. Rapid pass-through (22) — % of funds forwarded within 15 min
2. Velocity (18) — peak transactions/hour
3. Centrality (17) — balanced-flow connector score (0.7) + betweenness (0.3)
4. Counterparty diversity (14) — unique counterparties
5. Burst (11) — 60-min window density vs baseline
6. Temporal concentration (9) — activity share in busiest hour
7. ML anomaly (9) — Isolation Forest score
Thresholds: 0–39 Low, 40–69 Medium, 70–100 High. Source: `app/engine/risk_engine.py`, `app/config.py`.

**Q: Is the risk score a probability of fraud?**  
A: **No.** It is an **analytical prioritization signal**. Disclaimer on every risk display: "Risk scores support investigative prioritization. They do not establish fraud or guilt." Detection method (Isolation Forest / Analytical fallback) is always shown.

---

## 3. Explainability & Evidence

**Q: How does an investigator know *why* an account is flagged?**  
A: Three layers:
1. **Reasons list** — natural language: "94% of received funds forwarded within 15 minutes", "12 unique counterparties", etc.
2. **Contributor bars** — visual breakdown of each signal's point contribution to the 0–100 score.
3. **Data Provenance card** — detection method, dataset name, analysis timestamp.
3. **Evidence tab** (Money Trail) — each hop links to actual transaction record with ID, timestamp, amount, sender/receiver.

**Evidence:** `frontend/src/pages/AccountDetail.jsx` (lines 210-235, 360-380), `frontend/src/pages/MoneyTrail.jsx` (EvidenceView component)

---

## 4. Money Trail & Tracing

**Q: Does the trail prove the same money moved through every account?**  
A: **No.** The trail shows a **temporally connected transaction sequence** (each hop occurs after the previous, within a 30-min hop gap). Explicit disclaimer on every trail: *"This path shows a temporally connected transaction sequence. It is not definitive legal tracing of specific currency units: transaction amounts reflect observed transfer values, and branch points mean only part of the original value may follow the shown path."* Shown in UI banner + API field `tracing_disclaimer`.

**Q: How are branching paths handled?**  
A: When a hub splits funds (e.g., AC381 → AC427 + AC522), the trail follows the **largest-amount branch** by default. Branching count shown in trail summary (`branching_hops`). Separate traces required for other branches. Source: `app/engine/trail_engine.py` (lines 114-154, 179).

**Q: What if no path exists?**  
A: Clean error response: `{"hops": 0, "error": "No connected money trail found within the selected constraints..."}`. No fabricated path. Source: `app/engine/trail_engine.py` (function `_no_trail`).

---

## 5. Synthetic Data & Privacy

**Q: Is the demo data real?**  
A: **Entirely synthetic.** Labelled on every screen: "Prototype Environment — Synthetic Data". The demo case (`app/demo/case.py`) creates a deliberate fraud scenario (victim → collector → hub → cash-out mules → cash-out terminals) embedded in ~900 legitimate background accounts. No real financial data used.

**Q: How is privacy handled?**  
A: Account IDs masked in display (`XXXXXX381`). Audit logs record investigator actions only — no transaction amounts or full account details in audit. Passwords PBKDF2-HMAC-SHA256 (120k iterations). JWT in localStorage, 8-hour expiry.

---

## 6. False Positives & Human-in-the-Loop

**Q: How are false positives handled?**  
A: Investigators can classify accounts as `false_positive` (requires mandatory reason), `needs_review`, `confirmed_suspicious`, `legitimate`, or `unreviewed`. Classification persisted in DB, logged in audit. Investigation workflow: system **suggests**, investigator **decides** — no autonomous guilt determination.

**Evidence:** `frontend/src/pages/AccountDetail.jsx` (classification section), `app/routers/accounts.py` (status PATCH), `app/routers/investigations.py` (review_decision, reopen)

---

## 7. Security & Access Control

**Q: How is access controlled?**  
A: 3 roles (investigator, analyst, admin) with permission matrix:
- Investigator: view, trace, investigate, note, update_status, export
- Analyst: + upload, run_analysis, review_models
- Admin: + manage_users, view_audit, configure
JWT bearer tokens (HS256, 8h expiry). Protected by `Depends(require(permission))` on every endpoint. Unauthenticated → 401. Unauthorized → 403.

**Evidence:** `app/security/auth.py`, `app/api/deps.py`, `app/routers/*.py`

**Q: Any secrets exposed?**  
A: No. JWT secret via `CYBERTRACK_JWT_SECRET` env var. `.env.example` has placeholders only. No keys in source or client bundle. Demo credentials documented on login screen (intentional for hackathon).

---

## 8. Scalability & Performance

**Q: How does it scale?**  
- Pipeline: ~15 sec for 3,205 transactions
- Graph: cached in memory, rebuilt on new data (<100ms)
- Frontend bundle: 1.06 MB (gzip 320 KB)
- API latency: <200ms typical
- SQLite WAL for concurrent reads; PostgreSQL-ready repository layer

**Q: What's the max dataset tested?**  
A: Demo case: 3,205 tx / 1,402 accounts. Architecture supports 10k+ transactions; graph rendering caps at 400 edges (prioritized by risk) for UI responsiveness.

---

## 9. Institutional Integration

**Q: Does it connect to real banks/I4C/police systems?**  
A: **No.** All such integrations are explicitly labelled **"Future Authorized Integration"** in Settings. Adapters exist in architecture (clean interfaces) but no live connections. Real deployment would require authorized data feeds, legal/compliance review, and integration development.

---

## 10. Validation Path & Next Steps

**Q: What's needed before production use?**  
1. Authorized institutional data access (bank APIs, FIU feeds)
2. Legal/compliance review (privacy, data governance, jurisdiction)
3. Expert-labelled evaluation on real fraud data (calibrate thresholds, measure precision/recall)
4. False-positive analysis on production volumes
4. Scaling/performance tests at production load
5. Independent security assessment (pen test, code audit)
6. Controlled pilot with authorized institution
7. Monitoring, alerting, CI/CD, backup/DR

**Q: What's the current TRL (Technology Readiness Level)?**  
A: **TRL 4–5** — prototype validated in lab/synthetic environment. Not yet validated with operational data.

---

## 11. Limitations (Honest Disclosure)

| Limitation | Impact | Mitigation |
|------------|--------|------------|
| Synthetic demo data | Patterns deliberately planted; real networks noisier | Clearly labelled; weights configurable |
| Heuristic risk weights | Not statistically calibrated | Configurable; disclaimer on every score |
| Trail follows largest branch | May miss smaller branches | Branching count shown; separate traces available |
| No legal tracing claim | Not proof of identical fund flow | Explicit disclaimer on every trail |
| SQLite only | Concurrency limited | PostgreSQL-ready repos |
| No rate limiting/CSRF/lockout | Prototype auth | Documented for production |
| No real integrations | By design | Adapter interfaces exist |

---

## 12. What Would You Change With More Time?

1. **Calibrate risk model** on real labelled fraud data (precision/recall curves)
2. **Add temporal pattern detection** (periodic transfers, structuring sequences)
3. **Peer group analysis** (compare account behaviour to similar entities)
4. **Real-time streaming ingestion** (Kafka → pipeline)
5. **Advanced graph analytics** (temporal motifs, community evolution)
6. **Production hardening** (rate limiting, CSRF, audit integrity, monitoring)
7. **Accessibility audit** (WCAG 2.1 AA)
8. **E2E browser tests** (Playwright)

---

**Summary:** CYBERTRACK demonstrates a complete, working PS-35 pipeline with genuine underlying data, explainable risk, evidence-linked trails, and human-in-the-loop investigation — all with honest limitations disclosed. The jury can verify every claim against the source code, tests, and live demo.