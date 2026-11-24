"""Dashboard endpoint — dataset overview and top priorities."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.db.database import get_connection
from app.security import audit

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("")
def dashboard(user: dict = Depends(get_current_user)):
    conn = get_connection()

    ds = conn.execute(
        "SELECT * FROM datasets ORDER BY id DESC LIMIT 1").fetchone()
    if not ds:
        return {
            "loaded": False,
            "message": "No transactions loaded. Upload a dataset or "
                        "use the demonstration dataset.",
        }

    tx_total = conn.execute(
        "SELECT COUNT(*) AS n FROM transactions").fetchone()["n"]
    tx_value = conn.execute(
        "SELECT COALESCE(SUM(amount),0) AS s FROM transactions"
    ).fetchone()["s"]
    accounts = conn.execute(
        "SELECT COUNT(*) AS n FROM accounts").fetchone()["n"]
    risk_rows = conn.execute(
        """SELECT risk_category, COUNT(*) AS n
           FROM risk_scores GROUP BY risk_category""").fetchall()
    risk_counts = {r["risk_category"]: r["n"] for r in risk_rows}

    top_accounts = conn.execute(
        """SELECT r.account_id, r.risk_score, r.risk_category,
                  a.in_amount + a.out_amount AS volume
           FROM risk_scores r
           JOIN accounts a ON a.account_id = r.account_id
           WHERE r.risk_category IN ('high','medium')
           ORDER BY r.risk_score DESC LIMIT 10""").fetchall()

    recent_suspicious = conn.execute(
        """SELECT t.timestamp, t.sender_account, t.receiver_account,
                  t.amount, t.transaction_type, t.channel
           FROM transactions t
           JOIN risk_scores r ON r.account_id IN
             (t.sender_account, t.receiver_account)
           WHERE r.risk_score >= 70
           ORDER BY t.id DESC LIMIT 12""").fetchall()

    alerts = conn.execute(
        """SELECT * FROM alerts
           ORDER BY risk_score DESC LIMIT 6""").fetchall()

    clusters = conn.execute(
        """SELECT * FROM clusters
           ORDER BY avg_risk DESC LIMIT 5""").fetchall()

    investigations = conn.execute(
        """SELECT * FROM investigations
           WHERE status IN ('open','under_review')
           ORDER BY id DESC LIMIT 6""").fetchall()

    audit.log(user["investigator_id"], "Viewed dashboard",
              action_type="view")

    return {
        "loaded": True,
        "dataset": dict(ds),
        "metrics": {
            "total_transactions": tx_total,
            "total_value": round(float(tx_value), 2),
            "accounts_analyzed": accounts,
            "suspicious_accounts": risk_counts.get("high", 0)
                                    + risk_counts.get("medium", 0),
            "high_risk_networks": len(clusters),
            "active_investigations": len(investigations),
        },
        "risk_overview": {
            "high": risk_counts.get("high", 0),
            "medium": risk_counts.get("medium", 0),
            "low": risk_counts.get("low", 0),
        },
        "top_accounts": [dict(r) for r in top_accounts],
        "recent_suspicious": [dict(r) for r in recent_suspicious],
        "alerts": [dict(r) for r in alerts],
        "clusters": [dict(r) for r in clusters],
        "investigations": [dict(r) for r in investigations],
        "detection_method": conn.execute(
            "SELECT detection_method FROM risk_scores LIMIT 1"
        ).fetchone()["detection_method"],
        "risk_disclaimer": "Risk scores support investigative "
                            "prioritization. They do not "
                            "establish fraud or guilt.",
    }
