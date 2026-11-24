# CYBERTRACK — Round 5 Demo Script (5–7 Minutes)

**Audience:** Smart India Hackathon Jury  
**Persona:** Authorized Financial-Crime Investigator  
**Dataset:** Synthetic (labelled on every screen)  
**Accounts:** 1,402 | **Transactions:** 3,205 | **Key Hub:** AC381 (Risk 90.3)

---

## 0. Pre-Show Checklist (30 sec before start)

- [ ] Backend running: `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000`
- [ ] Frontend running: `npm run dev` (or `npm run build && serve dist`)
- [ ] Open http://localhost:5173 in browser (incognito recommended)
- [ ] Reset demo data if needed: POST `/api/data/reset-demo` with `{"confirm": true}` as analyst
- [ ] Have credentials ready: `investigator` / `cybertrack-demo`

---

## 1. Login & Problem Statement (45 sec)

| Action | Script |
|--------|--------|
| Open http://localhost:5173 | "This is CYBERTRACK — a PS-35 prototype for tracing money through mule accounts." |
| Login: `investigator` / `cybertrack-demo` | "Every screen carries the disclaimer: **Prototype Environment — Synthetic Data**. Risk scores support prioritisation, not guilt determination." |
| Dashboard loads | "**3,205 transactions** reviewed. **1,402 accounts** analysed. **65 suspicious accounts** identified. **AC381** is the top priority at **90.3/100**." |

**Key message:** "Individually, each of these 3,205 transactions looks ordinary. The fraud is only visible when we connect them."

---

## 2. The Aha Moment — Reveal Hidden Network (45 sec)

| Action | Script |
|--------|--------|
| Click **"Reveal Hidden Network"** | "Watch what happens when we connect the transactions." |
| Graph animates | "Red nodes = high risk. Amber = medium. Blue = selected. **AC381** is the red hub in the center." |
| Point to cluster | "**31 accounts** form **CLUSTER-01**. Pattern: **Rapid multi-hop convergence and divergence (hub-and-spoke)**. AC381 is the main intermediary." |

**Key message:** "The network reveals what individual transactions hide."

---

## 3. Priority Queue → Account Deep-Dive (60 sec)

| Action | Script |
|--------|--------|
| Navigate → **Priority Accounts** | "Ranked by analytical priority. **AC381** is #1 at **90.3/100**." |
| Click **AC381** | "Account detail opens. **Risk: 90.3 HIGH**. **Priority: HIGH**." |
| Point to **Why Suspicious** | "8 evidence-based reasons: **94% of funds forwarded within 15 min**, **12 counterparties**, **4 transactions/hour peak**, **transaction burst**, **network centrality**." |
| Point to **Why This Score** | "Contributor bars: Pass-through +21, Velocity +18, Centrality +17, Diversity +14, Burst +7, Temporal +5, ML anomaly +4. Total = 90.3." |
| Point to **Data Provenance** | "Detection method: **Isolation Forest**. Dataset: **Demonstration Case**. Analysis timestamp shown. **Disclaimer: Risk scores support investigative prioritization. They do not establish fraud or guilt.**" |

**Key message:** "Every point of the score is explained. No black box."

---

## 4. Network Exploration (45 sec)

| Action | Script |
|--------|--------|
| Click **"Explore Network"** (or Network Explorer tab) | "Ego view centered on AC381. **12 neighbours**, **1 suspicious**." |
| Click suspicious neighbour | "Opens that account's detail. Seamless pivot." |
| Click **"View Account"** badge | "Back to full investigation." |
| Click **"Shortest money path"** → enter `CO-01` | "**AC381 → AC522 → CO-01** in 2 hops. Real path from transaction data." |

**Key message:** "Investigators can pivot from account → network → path in seconds."

---

## 5. Money Trail Reconstruction (90 sec)

| Action | Script |
|--------|--------|
| Navigate → **Money Trail** | "Reconstruct chronological money movement." |
| Source: `AC9001` → **Trace Money** | "5 hops in **10 minutes**. **AC9001 → AC101 → AC245 → AC381 → AC522 → CO-03**." |
| Click **Timeline tab** | "Chronological view: **10:42 → 10:44 → 10:46 → 10:48 → 10:52**. Every hop is a real transaction." |
| Click **Graph tab** | "Visual path highlighted in blue. Red edges = high-risk connections." |
| Click **Table tab** | "Hop-by-hop: from, to, amount, timestamp, transaction ID." |
| Click **Evidence tab** (NEW in Round 4) | "**Each row is a real transaction record.** Transaction IDs are clickable. **Disclaimer:** This shows temporal sequence, not proof that identical currency units flowed through every hop. Branching means only a portion follows this path." |

**Key message:** "Every hop is an actual transaction. The trail shows temporal connectivity, not proof of identical fund movement."

---

## 6. Investigation Workflow (60 sec)

| Action | Script |
|--------|--------|
| From Account AC381 → **Create Investigation** | "Auto-attaches account. Title: 'Suspicious activity — AC381'. Priority: HIGH." |
| Open **Investigations** → Open new INV-XXXX | "Status: OPEN. Assigned to investigator. Attached: AC381, trail TRAIL-0001." |
| Set **Review Decision** → `confirmed_suspicious` | "Human decision recorded. Not automated." |
| Add **Notes** | "Hub AC381 forwards 94% within 15 minutes. Priority for legal request." |
| **Save** → Status: UNDER_REVIEW | "Status tracked. History preserved." |
| **Resolve** → **Reopen** | "Status: RESOLVED → OPEN. Full history maintained." |

**Key message:** "Human decides. System supports. Full audit trail."

---

## 7. Trust, Limitations & Next Steps (45 sec)

| Action | Script |
|--------|--------|
| Navigate → **Analytics** | "Detection: **Isolation Forest** (71 anomalies). Features: 11 behavioural + network signals. Thresholds: 40/70. Weights configurable." |
| Point to disclaimer | "**Model output supports investigator prioritization and requires human verification.**" |
| Navigate → **Settings** | "Future integrations labelled: Bank APIs, I4C, real-time streams, geospatial — all **Future Authorized Integration**." |
| Security posture | "JWT auth, 3-role RBAC, PBKDF2 hashing, audit logging, parameterised SQL, synthetic data warnings." |

**Closing line:**  
> **"CyberTrack doesn't declare fraud. It connects transactions, explains risk, reconstructs trails, and prioritizes where a human investigator should look first."**  
>  
> **Trace the money. Expose the network. Prioritize the action.**

---

## Fallback Plan (If Live Demo Fails)

| Issue | Fallback |
|-------|----------|
| Frontend won't load | Use production build: `cd frontend && npm run build && npx serve dist` |
| Backend won't start | `cd backend && python -m uvicorn app.main:app --host 127.0.0.1 --port 8000` |
| DB corrupted | `cd backend && rm data/cybertrack.db* && python -m uvicorn app.main:app --host 127.0.0.1 --port 8000` (auto-loads demo) |
| Network issues | Screenshots/video in `docs/demo_screenshots/` (if prepared) |

**Tested fallback:** Yes — `start.bat` launches both servers; `docs/verify_final_round5.py` validates all endpoints.

---

## Post-Demo Reset (For Next Session)

```bash
# As analyst
POST /api/data/reset-demo {"confirm": true}
# Preserves: investigations, users, audit log
# Replaces: transactions, features, risk, clusters, alerts, trails
```