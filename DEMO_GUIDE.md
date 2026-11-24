# CYBERTRACK — Demo Guide

**5–7 minute jury demonstration script**

## Setup (30 seconds)

```bash
# Terminal 1 — backend
cd backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000

# Terminal 2 — frontend
cd frontend
npm run dev
```

Open http://localhost:5173

> The backend automatically loads the synthetic
> demonstration case on first start, so the
> dashboard is populated immediately.

## Credentials

- Investigator: `investigator` / `cybertrack-demo`
- Analyst: `analyst` / `cybertrack-demo`
- Admin: `admin` / `cybertrack-demo`

## The story (follow the script)

### Step 1 — Login (15s)
Log in as `investigator`. Note:
*"Prototype Environment — Synthetic Data."*

### Step 2 — The problem (30s)
The dashboard shows:
**"3,205 transactions reviewed. 65 high-priority
accounts identified."**

Say: *"Individually, each of these 3,205
transactions looks ordinary. A fraudster moving
money through mule accounts is invisible at the
transaction level."*

### Step 3 — The aha moment (30s)
Click **"Reveal Hidden Network"**.

The graph transitions from nothing to a connected
network. Red nodes cluster around the hub.

Say: *"Once connected, the hidden network becomes
visible. Three ordinary-looking transfers form part
of the same high-risk money trail."*

### Step 4 — Priority (30s)
Open **Priority Accounts**. AC381 is rank 1,
risk 90/100.

Say: *"CyberTrack ranks where to look first.
Investigate AC381 first."*

### Step 5 — Explanation (60s)
Click **AC381**. Show:
- Risk 90/100, HIGH priority
- **Why suspicious**: 94% of funds forwarded
  within 15 minutes, 12 counterparties,
  4 transactions/hour peak, network centrality
- **Why this score**: contributor bars
  (pass-through +20, velocity +18, centrality
  +17, diversity +14…)

Say: *"No black box. Every point is explained."*

### Step 6 — The network (45s)
The Network Position panel shows the ego network:
victims → AC101 → AC245 → **AC381** → AC427 /
AC522 / AC610 → cash-out.

Click a neighbour to hop. Click
**"Open full investigation"**.

### Step 7 — Trace the money (60s)
Click **"Trace Money"** (or open Money Trail,
source `AC9001`).

Show the timeline:
```
10:42  AC9001 → AC101   ₹50,000
10:44  AC101  → AC245   ₹48,000
10:46  AC245  → AC381   ₹46,080
10:48  AC381  → AC523   ₹21,658
10:52  AC523  → CO-03   ₹21,224
```

Show: **5 hops in 10 minutes.** Money split at
the hub (branching). Cash-out intelligence:
likely cash-out location POS/Jaipur
(analytical estimate).

### Step 8 — Investigate (45s)
Click **"+ Create Investigation"**. It appears in
Investigations with ID `INV-2026-XXXX`.

Change status to "Under Review", add a note,
save. Open **Audit Log** (admin) to show the
action was recorded.

### Step 9 — Human control (30s)
Open any account → **Investigator Classification**.
Mark "False Positive" — note the reason is
*required*. Say: *"The system never declares guilt.
The investigator decides."*

### Step 10 — Close (15s)
Analytics page: detection method
(Isolation Forest), features used, thresholds,
disclaimer: *"Model output supports investigator
prioritisation and requires human verification."*

## Key talking points

- **Problem**: fraudsters hide money through
  ordinary-looking accounts; single-transaction
  views hide the pattern.
- **Solution**: connect → network → behaviour →
  explainable risk → priority.
- **Credibility**: real pipeline (cleaning →
  features → graph → Isolation Forest → trails),
  real explainability, real tests (46 passing).
- **Safety**: synthetic data, human-in-the-loop,
  RBAC, audit log, no overclaiming.

## Backup demos if asked

- **Upload your own CSV**: Data Management →
  Upload CSV (schema shown on the page).
- **RBAC**: try to upload as investigator (403),
  succeed as analyst.
- **Error handling**: upload a CSV missing
  `timestamp` — clear validation message.
- **Cluster view**: Clusters show CLUSTER-01,
  31 accounts, hub-and-spoke pattern.
- **Alerts**: 7 typologies including rapid
  multi-hop and structuring/splitting.
- **Export**: CSV export of priority accounts.
