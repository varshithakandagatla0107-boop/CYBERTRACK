# CYBERTRACK — API Reference

Base URL: `http://127.0.0.1:8000`
Authentication: `Authorization: Bearer <JWT>`

All endpoints return JSON. Errors return
`{"detail": "human-readable message"}` with the
appropriate HTTP status. No raw stack traces are
ever exposed.

## Auth

| Method | Endpoint | Description |
| ------ | -------- | ----------- |
| POST | `/api/auth/login` | `{investigator_id, password}` → `{token, user}` |
| GET | `/api/auth/me` | Current session user |

## Data

| Method | Endpoint | Description |
| ------ | -------- | ----------- |
| POST | `/api/data/upload` | multipart CSV upload + analysis (analyst+) |
| POST | `/api/data/demo` | Load synthetic demonstration case (analyst+) |
| GET | `/api/data/status` | Current dataset / processing status |

## Dashboard

| Method | Endpoint | Description |
| ------ | -------- | ----------- |
| GET | `/api/dashboard` | Metrics, risk overview, top accounts, recent suspicious activity, alerts, clusters, investigations |

## Accounts

| Method | Endpoint | Description |
| ------ | -------- | ----------- |
| GET | `/api/accounts` | List (`?risk=&search=&limit=&offset=`) |
| GET | `/api/accounts/{id}` | Detail: risk, features, reasons, timeline, cluster |
| PATCH | `/api/accounts/{id}/status` | `?status=&reason=` — classify (false positive requires reason) |

## Transactions

| Method | Endpoint | Description |
| ------ | -------- | ----------- |
| GET | `/api/transactions` | Filtered explorer (sender, receiver, channel, type, min/max amount, dates, search, risk, limit, offset) |
| GET | `/api/transactions/{id}` | Detail + preceding/following transactions |

## Network

| Method | Endpoint | Description |
| ------ | -------- | ----------- |
| GET | `/api/network` | Graph data (`?high_risk_only=&min_amount=&limit=`) |
| GET | `/api/network/{account_id}` | Investigation View (ego network + suspicious neighbours) |
| GET | `/api/network/{account_id}/paths` | Shortest money path (`?target=`) |

## Money trails

| Method | Endpoint | Description |
| ------ | -------- | ----------- |
| POST | `/api/trails/trace` | `{source, destination?, amount?, max_hops?, max_minutes?}` |
| GET | `/api/trails` | List persisted trails |
| GET | `/api/trails/{trail_id}` | Trail detail + cash-out intelligence |

## Priorities, clusters, alerts

| Method | Endpoint | Description |
| ------ | -------- | ----------- |
| GET | `/api/priorities` | Investigation priority queue |
| GET | `/api/clusters` | List clusters |
| GET | `/api/clusters/{label}` | Cluster detail |
| GET | `/api/alerts` | Alerts (`?severity=&status=&alert_type=`) |
| PATCH | `/api/alerts/{id}/status` | `?status=acknowledged\|escalated\|closed` |

## Investigations

| Method | Endpoint | Description |
| ------ | -------- | ----------- |
| POST | `/api/investigations` | Create (title, priority, accounts, transactions, trails, clusters, alerts, notes) |
| GET | `/api/investigations` | List (`?status=`) |
| GET | `/api/investigations/{id}` | Detail + attached entities |
| PATCH | `/api/investigations/{id}` | Update status / priority / notes |
| GET | `/api/investigations/{id}/report` | Structured summary report (printable) |

## Analytics, audit, settings, export

| Method | Endpoint | Description |
| ------ | -------- | ----------- |
| GET | `/api/analytics/model` | Model transparency (method, features, thresholds, weights) |
| GET | `/api/analytics/risk-distribution` | Risk bucket counts |
| GET | `/api/audit` | Full audit log (admin) |
| GET | `/api/audit/my` | Own audit log |
| GET | `/api/settings` | Analysis parameters, future integrations, security posture |
| GET | `/api/export/transactions` | CSV export |
| GET | `/api/export/priority-accounts` | CSV export |
| GET | `/api/export/alerts` | CSV export |

## Health

| Method | Endpoint | Description |
| ------ | -------- | ----------- |
| GET | `/api/health` | Service health |

## Status codes

| Code | Meaning |
| ---- | ------- |
| 200 | Success |
| 400 | Invalid input (e.g. missing false-positive reason) |
| 401 | Missing/expired/invalid session |
| 403 | Role lacks the required permission |
| 404 | Entity not found / no data loaded |
| 422 | Validation failure (CSV, payload) |
