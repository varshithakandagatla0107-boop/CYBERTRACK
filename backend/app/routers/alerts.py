"""Alerts endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_current_user
from app.db.database import get_connection
from app.security import audit

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


@router.get("")
def list_alerts(
    severity: str | None = Query(default=None),
    status: str | None = Query(default=None),
    alert_type: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
):
    conn = get_connection()
    where, params = [], []
    if severity:
        where.append("severity = ?")
        params.append(severity)
    if status:
        where.append("status = ?")
        params.append(status)
    if alert_type:
        where.append("alert_type = ?")
        params.append(alert_type)
    clause = f"WHERE {' AND '.join(where)}" if where else ""

    rows = conn.execute(
        f"""SELECT * FROM alerts {clause}
            ORDER BY risk_score DESC, id DESC""",
        params,
    ).fetchall()

    alerts = []
    for r in rows:
        item = dict(r)
        item["account_list"] = [
            a.strip() for a in item["account_ids"].split(",")
            if a.strip()]
        item["what"] = item["title"]
        item["why"] = item["description"]
        item["when"] = item["occurred_at"]
        alerts.append(item)

    return {"alerts": alerts, "count": len(alerts)}


@router.patch("/{alert_id}/status")
def update_alert_status(alert_id: int, status: str,
                            user: dict = Depends(get_current_user)):
    valid = {"open", "acknowledged", "escalated", "closed"}
    if status not in valid:
        from fastapi import HTTPException
        raise HTTPException(
            400, f"Status must be one of: "
                    f"{', '.join(sorted(valid))}")
    conn = get_connection()
    conn.execute(
        "UPDATE alerts SET status = ? WHERE id = ?",
        (status, alert_id),
    )
    conn.commit()
    audit.log(user["investigator_id"],
              f"Alert {alert_id} set to {status}",
              entity_type="alert", entity_id=str(alert_id),
              action_type="update_status")
    return {"alert_id": alert_id, "status": status}
