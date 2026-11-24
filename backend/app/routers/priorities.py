"""Investigation priority queue."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_current_user
from app.db.database import get_connection
from app.security import audit

router = APIRouter(prefix="/api/priorities",
                    tags=["priorities"])


@router.get("")
def priority_queue(
    limit: int = Query(default=50, le=200),
    user: dict = Depends(get_current_user),
):
    """Suspicious entities sorted by analytical priority."""
    conn = get_connection()
    rows = conn.execute(
        """SELECT r.account_id, r.risk_score, r.risk_category,
                  r.contributors, a.tx_count, a.in_amount,
                  a.out_amount, a.unique_counterparties,
                  a.status,
                  (a.in_amount + a.out_amount) AS amount_involved,
                  f.velocity, f.rapid_pass_pct, f.burst_score,
                  f.degree, c.cluster_label
           FROM risk_scores r
           JOIN accounts a ON a.account_id = r.account_id
           LEFT JOIN account_features f
             ON f.account_id = r.account_id
           LEFT JOIN clusters c
             ON c.account_list LIKE '%' || r.account_id || '%'
           WHERE r.risk_score >= 40
           ORDER BY r.risk_score DESC
           LIMIT ?""",
        (limit,),
    ).fetchall()

    queue = []
    for r in rows:
        reasons = _top_reasons(r["contributors"])
        queue.append({
            "rank": len(queue) + 1,
            "account_id": r["account_id"],
            "risk_score": r["risk_score"],
            "risk_category": r["risk_category"],
            "network_role": _network_role(
                r["degree"], r["unique_counterparties"]),
            "amount_involved": round(
                float(r["amount_involved"] or 0), 2),
            "velocity": float(r["velocity"] or 0),
            "rapid_pass_pct": float(r["rapid_pass_pct"] or 0),
            "tx_count": r["tx_count"],
            "counterparties": r["unique_counterparties"],
            "cluster": r["cluster_label"],
            "reason": "; ".join(reasons),
            "reasons": reasons,
            "status": r["status"],
        })

    audit.log(user["investigator_id"],
              "Viewed priority queue", action_type="view")
    return {"queue": queue, "count": len(queue),
            "risk_disclaimer": "Risk scores support "
                                "investigative prioritization. "
                                "They do not establish fraud "
                                "or guilt."}


def _top_reasons(contributors: str | None, n: int = 3):
    if not contributors:
        return []
    parts = []
    for item in contributors.split(";"):
        if ":" in item:
            k, v = item.split(":", 1)
            parts.append((k, float(v)))
    parts.sort(key=lambda kv: -kv[1])
    labels = {
        "pass_through": "Rapid pass-through",
        "velocity": "High transaction velocity",
        "centrality": "Network centrality",
        "counterparty_diversity": "Counterparty diversity",
        "burst": "Transaction burst",
        "temporal_concentration": "Temporal concentration",
        "ml_anomaly": "Anomaly signal",
    }
    return [f"{labels.get(k, k)} (+{v:.0f})"
            for k, v in parts[:n] if v > 0]


def _network_role(degree: int, counterparties: int) -> str:
    if degree >= 10:
        return "Hub / intermediary"
    if degree >= 6:
        return "Connector"
    if counterparties >= 5:
        return "Multi-counterparty"
    return "Standard"
