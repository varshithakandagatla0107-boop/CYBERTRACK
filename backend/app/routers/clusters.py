"""Cluster endpoints — suspicious network clusters."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_current_user
from app.db.database import get_connection
from app.security import audit

router = APIRouter(prefix="/api/clusters", tags=["clusters"])


@router.get("")
def list_clusters(user: dict = Depends(get_current_user)):
    conn = get_connection()
    rows = conn.execute(
        """SELECT * FROM clusters
           ORDER BY avg_risk DESC""").fetchall()
    return {"clusters": [dict(r) for r in rows]}


@router.get("/{cluster_label}")
def cluster_detail(cluster_label: str,
                        user: dict = Depends(get_current_user)):
    conn = get_connection()
    cluster = conn.execute(
        "SELECT * FROM clusters WHERE cluster_label = ?",
        (cluster_label,),
    ).fetchone()
    if not cluster:
        raise HTTPException(404,
                            f"Cluster {cluster_label} not found.")

    accounts = [a.strip()
                for a in cluster["account_list"].split(",")
                if a.strip()]

    account_details = []
    for account_id in accounts:
        r = conn.execute(
            """SELECT r.account_id, r.risk_score,
                      r.risk_category, a.tx_count,
                      a.in_amount, a.out_amount
               FROM risk_scores r
               JOIN accounts a ON a.account_id = r.account_id
               WHERE r.account_id = ?""",
            (account_id,),
        ).fetchone()
        if r:
            account_details.append(dict(r))

    # money movement window
    window = conn.execute(
        """SELECT MIN(timestamp) AS start,
                  MAX(timestamp) AS end,
                  COUNT(*) AS tx_count,
                  SUM(amount) AS total
           FROM transactions
           WHERE sender_account IN ({})
              OR receiver_account IN ({})""".format(
            ",".join("?" * len(accounts)),
            ",".join("?" * len(accounts))),
        (*accounts, *accounts),
    ).fetchone()

    audit.log(user["investigator_id"],
              f"Viewed cluster {cluster_label}",
              entity_type="cluster", entity_id=cluster_label,
              action_type="view")

    return {
        "cluster": dict(cluster),
        "accounts": sorted(account_details,
                            key=lambda a: -a["risk_score"]),
        "window": dict(window) if window else {},
    }
