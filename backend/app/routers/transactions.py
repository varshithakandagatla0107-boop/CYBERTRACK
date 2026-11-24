"""Transaction explorer endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.deps import get_current_user, require
from app.db.database import get_connection
from app.security import audit

router = APIRouter(prefix="/api/transactions",
                    tags=["transactions"])


@router.get("")
def list_transactions(
    sender: str | None = Query(default=None),
    receiver: str | None = Query(default=None),
    channel: str | None = Query(default=None),
    tx_type: str | None = Query(default=None),
    min_amount: float | None = Query(default=None),
    max_amount: float | None = Query(default=None),
    date_from: str | None = Query(default=None),
    date_to: str | None = Query(default=None),
    search: str | None = Query(default=None),
    risk: str | None = Query(default=None),
    limit: int = Query(default=50, le=500),
    offset: int = Query(default=0, ge=0),
    user: dict = Depends(get_current_user),
):
    conn = get_connection()
    where, params = [], []
    if sender:
        where.append("sender_account = ?")
        params.append(sender.upper())
    if receiver:
        where.append("receiver_account = ?")
        params.append(receiver.upper())
    if channel:
        where.append("channel = ?")
        params.append(channel)
    if tx_type:
        where.append("transaction_type = ?")
        params.append(tx_type)
    if min_amount is not None:
        where.append("amount >= ?")
        params.append(min_amount)
    if max_amount is not None:
        where.append("amount <= ?")
        params.append(max_amount)
    if date_from:
        where.append("timestamp >= ?")
        params.append(date_from)
    if date_to:
        where.append("timestamp <= ?")
        params.append(date_to + " 23:59:59")
    if search:
        where.append(
            "(transaction_id LIKE ? OR sender_account LIKE ? "
            "OR receiver_account LIKE ?)")
        s = f"%{search.upper()}%"
        params += [s, s, s]
    if risk:
        # risk filter via join on risk scores
        where.append(
            "(SELECT COALESCE(MAX(r.risk_score),0) FROM risk_scores r "
            "WHERE r.account_id IN (sender_account, receiver_account)) "
            ">= ?")
        params.append(70.0 if risk == "high" else 40.0)

    clause = f"WHERE {' AND '.join(where)}" if where else ""
    total = conn.execute(
        f"SELECT COUNT(*) AS n FROM transactions {clause}",
        params,
    ).fetchone()["n"]
    rows = conn.execute(
        f"""SELECT * FROM transactions {clause}
            ORDER BY timestamp DESC LIMIT ? OFFSET ?""",
        (*params, limit, offset),
    ).fetchall()

    enriched = []
    for r in rows:
        item = dict(r)
        item["sender_risk"] = _risk(conn, item["sender_account"])
        item["receiver_risk"] = _risk(conn, item["receiver_account"])
        enriched.append(item)

    return {"transactions": enriched, "total": total}


@router.get("/{transaction_id}")
def transaction_detail(transaction_id: str,
                        user: dict = Depends(get_current_user)):
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM transactions WHERE transaction_id = ?",
        (transaction_id,),
    ).fetchone()
    if not row:
        raise HTTPException(404,
                            f"Transaction {transaction_id} not found.")

    item = dict(row)
    item["sender_risk"] = _risk(conn, item["sender_account"])
    item["receiver_risk"] = _risk(conn, item["receiver_account"])

    # preceding and following transactions for the involved accounts
    preceding = conn.execute(
        """SELECT * FROM transactions
           WHERE (sender_account = ? OR receiver_account = ?)
             AND timestamp < ?
           ORDER BY timestamp DESC LIMIT 3""",
        (item["sender_account"], item["sender_account"],
         item["timestamp"]),
    ).fetchall()
    following = conn.execute(
        """SELECT * FROM transactions
           WHERE (sender_account = ? OR receiver_account = ?)
             AND timestamp > ?
           ORDER BY timestamp ASC LIMIT 3""",
        (item["receiver_account"], item["receiver_account"],
         item["timestamp"]),
    ).fetchall()
    item["preceding"] = [dict(p) for p in preceding]
    item["following"] = [dict(f) for f in following]

    audit.log(user["investigator_id"],
              f"Viewed transaction {transaction_id}",
              entity_type="transaction", entity_id=transaction_id,
              action_type="view")
    return item


def _risk(conn, account_id: str) -> float:
    row = conn.execute(
        "SELECT risk_score FROM risk_scores WHERE account_id = ?",
        (account_id,),
    ).fetchone()
    return float(row["risk_score"]) if row else 0.0
