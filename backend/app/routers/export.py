"""CSV export endpoints."""
from __future__ import annotations

import csv
import io

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.api.deps import get_current_user, require
from app.db.database import get_connection
from app.security import audit

router = APIRouter(prefix="/api/export", tags=["export"])


def _csv_response(rows: list[dict], filename: str,
                    user: dict, action: str):
    if not rows:
        return {"message": "No data to export."}
    output = io.StringIO()
    writer = csv.DictWriter(output,
                                fieldnames=list(rows[0].keys()))
    writer.writeheader()
    for r in rows:
        writer.writerow({
            k: v for k, v in r.items()
        })
    output.seek(0)
    audit.log(user["investigator_id"],
              f"Exported {action}", action_type="export")
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition":
                    f"attachment; filename={filename}"},
    )


@router.get("/transactions")
def export_transactions(
        user: dict = Depends(require("export"))):
    conn = get_connection()
    rows = conn.execute(
        """SELECT transaction_id, sender_account,
                  receiver_account, amount, timestamp,
                  transaction_type, channel
           FROM transactions ORDER BY timestamp DESC
           LIMIT 5000""").fetchall()
    return _csv_response([dict(r) for r in rows],
                            "transactions.csv", user,
                            "transactions")


@router.get("/priority-accounts")
def export_priority(
        user: dict = Depends(require("export"))):
    conn = get_connection()
    rows = conn.execute(
        """SELECT r.account_id, r.risk_score,
                  r.risk_category, a.tx_count,
                  a.in_amount, a.out_amount,
                  a.unique_counterparties, a.status
           FROM risk_scores r JOIN accounts a
             ON a.account_id = r.account_id
           WHERE r.risk_score >= 40
           ORDER BY r.risk_score DESC""").fetchall()
    return _csv_response([dict(r) for r in rows],
                            "priority_accounts.csv", user,
                            "priority accounts")


@router.get("/alerts")
def export_alerts(user: dict = Depends(require("export"))):
    conn = get_connection()
    rows = conn.execute(
        """SELECT alert_type, title, description,
                  account_ids, amount, occurred_at,
                  risk_score, severity, status
           FROM alerts ORDER BY risk_score DESC""").fetchall()
    return _csv_response([dict(r) for r in rows],
                            "alerts.csv", user, "alerts")
