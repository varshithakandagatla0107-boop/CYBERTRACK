"""Account endpoints: list, detail, explainable risk, behaviour features."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.deps import get_current_user, require
from app.db.database import get_connection
from app.engine.risk_engine import explain_reasons
from app.security import audit

router = APIRouter(prefix="/api/accounts", tags=["accounts"])


@router.get("")
def list_accounts(
    risk: str | None = Query(default=None),
    search: str | None = Query(default=None),
    limit: int = Query(default=100, le=500),
    offset: int = Query(default=0, ge=0),
    user: dict = Depends(get_current_user),
):
    conn = get_connection()
    where, params = [], []
    if risk:
        where.append("r.risk_category = ?")
        params.append(risk)
    if search:
        where.append("r.account_id LIKE ?")
        params.append(f"%{search.upper()}%")
    clause = f"WHERE {' AND '.join(where)}" if where else ""
    rows = conn.execute(
        f"""SELECT r.account_id, r.risk_score, r.risk_category,
                   a.tx_count, a.in_amount, a.out_amount,
                   a.unique_counterparties, a.status
            FROM risk_scores r
            JOIN accounts a ON a.account_id = r.account_id
            {clause}
            ORDER BY r.risk_score DESC, r.account_id
            LIMIT ? OFFSET ?""",
        (*params, limit, offset),
    ).fetchall()
    total = conn.execute(
        f"SELECT COUNT(*) AS n FROM risk_scores r {clause}",
        params,
    ).fetchone()["n"]
    return {"accounts": [dict(r) for r in rows], "total": total}


@router.get("/{account_id}")
def account_detail(account_id: str,
                     user: dict = Depends(get_current_user)):
    conn = get_connection()
    account_id = account_id.upper()

    risk = conn.execute(
        "SELECT * FROM risk_scores WHERE account_id = ?",
        (account_id,),
    ).fetchone()
    if not risk:
        raise HTTPException(404,
                            f"Account {account_id} not found in dataset.")

    account = conn.execute(
        "SELECT * FROM accounts WHERE account_id = ?",
        (account_id,),
    ).fetchone()
    features = conn.execute(
        "SELECT * FROM account_features WHERE account_id = ?",
        (account_id,),
    ).fetchone()

    # community membership
    cluster = conn.execute(
        "SELECT cluster_label FROM clusters WHERE account_list LIKE ?",
        (f"%{account_id}%",),
    ).fetchone()

    # recent transactions involving this account
    tx = conn.execute(
        """SELECT * FROM transactions
           WHERE sender_account = ? OR receiver_account = ?
           ORDER BY timestamp DESC LIMIT 50""",
        (account_id, account_id),
    ).fetchall()

    reasons = explain_reasons(dict(features) if features
                                else dict(risk))

    audit.log(user["investigator_id"], f"Viewed account {account_id}",
              entity_type="account", entity_id=account_id,
              action_type="view")

    return {
        "account": dict(account) if account else None,
        "risk": {
            "score": risk["risk_score"],
            "category": risk["risk_category"],
            "contributors": dict(
                kv.split(":") for kv in
                (risk["contributors"] or "").split(";") if kv
            ) if risk["contributors"] else {},
            "detection_method": risk["detection_method"],
        },
        "features": dict(features) if features else {},
        "reasons": reasons,
        "cluster": cluster["cluster_label"] if cluster else None,
        "status": account["status"] if account else "unreviewed",
        "analyst_note": account["analyst_note"] if account else "",
        "transactions": [dict(t) for t in tx],
        "disclaimer": "Risk scores support investigative "
                        "prioritization. They do not establish "
                        "fraud or guilt.",
    }


@router.patch("/{account_id}/status")
def update_account_status(account_id: str,
                            status: str,
                            reason: str = "",
                            user: dict = Depends(require("investigate"))):
    valid = {"unreviewed", "needs_review",
                "confirmed_suspicious", "false_positive", "legitimate"}
    if status not in valid:
        raise HTTPException(400,
                            f"Status must be one of: "
                            f"{', '.join(sorted(valid))}")
    if status == "false_positive" and not reason.strip():
        raise HTTPException(
            400, "A reason is required when marking a false positive.")

    conn = get_connection()
    account_id = account_id.upper()
    conn.execute(
        """UPDATE accounts SET status = ?, analyst_note = ?,
           updated_at = datetime('now') WHERE account_id = ?""",
        (status, reason, account_id),
    )
    conn.commit()
    audit.log(user["investigator_id"],
              f"Marked {account_id} as {status}",
              entity_type="account", entity_id=account_id,
              action_type="classification",
              details=reason)
    return {"account_id": account_id, "status": status}
