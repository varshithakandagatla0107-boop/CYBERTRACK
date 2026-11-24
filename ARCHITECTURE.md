# CYBERTRACK — Architecture

**PS-35: Tracing Money Through Mule Accounts**
**Team DuoNova**

## Target architecture

```
React (Vite)
     │  REST / JSON (JWT bearer)
     ▼
FastAPI
     │
     ├─ Ingestion service      CSV validation, cleaning
     ├─ Feature engine         account-level behaviour
     ├─ Graph engine           NetworkX graph + communities
     ├─ Risk / ML engine       Isolation Forest + explainable scoring
     ├─ Trail engine           temporal money-trail reconstruction
     ├─ Alert engine           fraud-typology pattern alerts
     └─ Investigation service  workspace, audit, RBAC
     │
     ▼
SQLite (PostgreSQL-ready repository interfaces)
```

## The PS-35 pipeline (implemented exactly)

```
TRANSACTION DATA          /api/data/upload, /api/data/demo
DATA CLEANING             engine/ingestion.py
FEATURE EXTRACTION        engine/features.py
TRANSACTION GRAPH         engine/graph_engine.py
BEHAVIOUR + NETWORK ANALYSIS  features + centrality + communities
MULE / ANOMALY DETECTION  engine/ml_engine.py
TEMPORAL MONEY-TRAIL TRACING  engine/trail_engine.py
EXPLAINABLE RISK          engine/risk_engine.py
INVESTIGATION PRIORITY    routers/priorities.py
OPTIONAL CASH-OUT INTELLIGENCE  routers/trails.py (extension)
```

## Key design decisions

### 1. Time-respecting graph analysis
Money can only move forward in time. Trail
reconstruction and multi-hop detection enforce
temporal contiguity: each hop must occur shortly
after the previous one (default 30-minute gap).

### 2. Peak-hour velocity, not average velocity
Mule accounts transact in short bursts spread across
days. Average velocity over the whole span dilutes
the signal to near zero. We measure peak
transactions-per-hour instead.

### 3. Cumulative pass-through
Rapid pass-through measures the total value leaving
the account within 15 minutes of each inflow —
not just the first outgoing transfer. This correctly
scores hub-and-spoke splitting (AC381 forwards
~94% within minutes).

### 4. Balanced-flow centrality
Raw betweenness centrality favours legitimate
high-degree hubs (payroll companies paying 75
employees). Mule hubs are distinguished by
*balanced* in/out flow: they both receive from
many and send to many. Centrality signal =
0.7 × connector score + 0.3 × normalised
betweenness.

### 5. Explainable, not opaque
Every risk score is decomposed into weighted
contributors visible in the UI ("Why this score?").
The detection method (Isolation Forest / analytical
fallback) is always displayed.

### 6. Human-in-the-loop
The system detects, ranks, explains, suggests and
traces. The investigator decides: review, escalate,
close, or mark false positive (with mandatory
reason). No automated guilt determination.

## Module map

| Module | Responsibility |
| ------ | -------------- |
| `app/main.py` | FastAPI app, CORS, lifespan, static hosting |
| `app/config.py` | Settings, risk weights, thresholds, RBAC matrix |
| `app/db/database.py` | SQLite schema, connection, transactions |
| `app/engine/ingestion.py` | CSV parsing & validation |
| `app/engine/features.py` | Behavioural feature extraction |
| `app/engine/graph_engine.py` | NetworkX graph, centrality, communities |
| `app/engine/ml_engine.py` | Isolation Forest / deterministic fallback |
| `app/engine/risk_engine.py` | Explainable 0–100 risk scoring |
| `app/engine/trail_engine.py` | Temporal money-trail reconstruction |
| `app/engine/alert_engine.py` | Pattern alerts (7 typologies) |
| `app/engine/pipeline.py` | Orchestration + persistence |
| `app/demo/case.py` | Synthetic demonstration case |
| `app/security/auth.py` | PBKDF2 hashing, JWT, RBAC, masking |
| `app/security/audit.py` | Audit log writes/reads |
| `app/routers/*` | REST endpoints |
| `frontend/src/*` | React UI, Cytoscape graph, Leaflet-ready |

## Data flow

```
CSV upload / demo case
        │
        ▼
  validation (flag invalid rows, never drop silently)
        │
        ▼
  persist transactions + dataset metadata
        │
        ▼
  extract_features  ──► account_features
        │
        ▼
  build_graph  ──► nodes/edges (in-memory)
        │
        ▼
  detect_anomalies  ──► ml_score, ml_anomaly
        │
        ▼
  score_accounts  ──► risk_scores (with contributors)
        │
        ▼
  suspicious_communities  ──► clusters
        │
        ▼
  generate_alerts  ──► alerts
        │
        ▼
  REST API  ──► React UI
```

## Scaling notes

- Graph is rebuilt from SQLite on analysis and cached
  in memory; invalidated on new dataset upload.
- Network API caps returned edges (default 400,
  max 1500) and prioritises edges touching high-risk
  accounts, so graphs with 1,000+ nodes stay
  readable.
- Tables are paginated (25–500 rows).
- SQLite WAL mode allows concurrent reads.
- Repository layer uses parameterised queries only;
  PostgreSQL can replace SQLite by swapping the
  connection + schema dialect.
