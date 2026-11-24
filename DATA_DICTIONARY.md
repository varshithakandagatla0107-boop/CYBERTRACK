# CYBERTRACK — Data Dictionary

## Input CSV schema

### Required columns

| Column | Type | Description |
| ------ | ---- | ----------- |
| `transaction_id` | string | Unique transaction identifier |
| `sender_account` | string | Originating account (normalised to upper-case) |
| `receiver_account` | string | Destination account |
| `amount` | number | Transaction value (₹); must be ≥ 0 |
| `timestamp` | datetime | When the money moved |
| `transaction_type` | string | transfer / payment / p2p / merchant / atm_withdrawal / salary / bill_payment |
| `channel` | string | bank / upi / neft / imps / pos / atm / wallet |
| `sender_location` | string | Origin city/label |
| `receiver_location` | string | Destination city/label |

### Optional columns

| Column | Type | Description |
| ------ | ---- | ----------- |
| `device_id` | string | Device fingerprint |
| `ip_hash` | string | Hashed IP |
| `merchant_id` | string | Merchant identifier |
| `cashout_location` | string | Cash-out point label (e.g. `ATM/Mumbai`) |

## Database tables (SQLite)

| Table | Purpose |
| ----- | ------- |
| `users` | Investigator accounts (PBKDF2 password hash, role) |
| `datasets` | Uploaded/demo dataset metadata |
| `transactions` | Validated transaction records |
| `accounts` | Account rollup (counts, volumes, status) |
| `account_features` | Behavioural features per account |
| `risk_scores` | Risk score, category, contributors, method |
| `clusters` | Detected suspicious network clusters |
| `alerts` | Pattern alerts |
| `money_trails` | Reconstructed trails (summary) |
| `trail_hops` | Individual hops within a trail |
| `investigations` | Investigator workspace records |
| `investigation_entities` | Accounts/trails/alerts attached to investigations |
| `audit_logs` | Investigator action log |

## Account behavioural features

| Feature | Meaning |
| ------- | ------- |
| `tx_count` | Total transactions involving the account |
| `velocity` | Peak transactions in the busiest single hour |
| `in_amount` / `out_amount` | Total received / sent value |
| `in_out_ratio` | out_amount ÷ in_amount |
| `counterparties` | Unique interacting accounts |
| `rapid_pass_pct` | % of received value forwarded within 15 minutes |
| `rapid_count` | Number of inflows forwarded within 15 minutes |
| `burst_score` | 0–1 density of the busiest 60-minute window vs baseline |
| `temporal_concentration` | Share of activity in the single busiest hour-of-day |
| `degree` | Unique counterparties (graph degree) |
| `in_degree` / `out_degree` | Unique senders / receivers |
| `ml_score` | 0–1 anomaly score (Isolation Forest or fallback) |
| `ml_anomaly` | 1 if flagged anomalous by the model |

## Risk model

```
Risk = Σ (weight_i × normalised_signal_i) / Σ weights × 100
```

| Signal | Weight | Saturation |
| ------ | ------ | ---------- |
| Rapid pass-through | 22 | 100% forwarded |
| Transaction velocity | 18 | 4 tx/hour |
| Network centrality | 17 | balanced-flow + betweenness |
| Counterparty diversity | 14 | 12 counterparties |
| Transaction burst | 11 | 5× baseline |
| Temporal concentration | 9 | 100% in one hour |
| Anomaly model signal | 9 | Isolation Forest score |

Categories: **0–39 Low · 40–69 Medium · 70–100 High**

> Risk score is an analytical prioritisation signal,
> not a determination of fraud.

## Alert typologies

| Type | Trigger |
| ---- | ------- |
| Rapid pass-through | ≥3 inflows forwarded within 15 min, ≥60% forwarded |
| High connectivity | ≥10 unique counterparties |
| Transaction burst | burst_score ≥ 0.6 |
| Structuring / splitting | One inflow split across ≥3 accounts within 10 min |
| Rapid multi-hop | ≥3 hops within 30 minutes |
| Suspicious convergence | ≥5 accounts feeding one intermediary that forwards rapidly |
| Suspicious divergence | Rapid distribution to many accounts |

## Roles & permissions

| Capability | Investigator | Analyst | Admin |
| ---------- | :--: | :--: | :--: |
| View / trace / investigate | ✓ | ✓ | ✓ |
| Add notes / update status | ✓ | ✓ | ✓ |
| Export | ✓ | ✓ | ✓ |
| Upload datasets / run analysis | — | ✓ | ✓ |
| Review models | — | ✓ | ✓ |
| Manage users / view full audit / configure | — | — | ✓ |

## Demo case identifiers

| Account | Role |
| ------- | ---- |
| AC9001–AC9007 | Victims (fraudulent inflows) |
| AC101–AC103 | Collector (first-hop) mules |
| AC245–AC247 | Second-hop mules |
| **AC381** | **Primary hub — risk ≈ 90** |
| AC382 | Secondary hub (medium-risk network) |
| AC427, AC522, AC610, AC428, AC523, AC530 | Cash-out layer mules |
| CO-01–CO-03 | Cash-out terminals (ATM/POS) |
| AC700–AC703 | Legitimate look-alike accounts |
| ~900 AC1xxx–AC9xxx | Ordinary background accounts |
