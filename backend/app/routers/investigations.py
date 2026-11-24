"""Investigation workspace — human-in-the-loop investigations.

The system detects, ranks, explains, suggests and traces.
The investigator decides: review, escalate, close,
mark false positive, add notes.
"""
from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.api.deps import get_current_user, require
from app.db.database import get_connection
from app.security import audit

router = APIRouter(prefix="/api/investigations",
                    tags=["investigations"])


class InvestigationCreate(BaseModel):
    title: str
    priority: str = "medium"
    accounts: list[str] = []
    transactions: list[str] = []
    trails: list[str] = []
    clusters: list[str] = []
    alerts: list[int] = []
    notes: str = ""


class InvestigationUpdate(BaseModel):
    status: str | None = None
    priority: str | None = None
    notes: str | None = None
    review_decision: str | None = None
    reopen: bool = False


@router.post("")
def create_investigation(
        req: InvestigationCreate,
        user: dict = Depends(require("investigate"))):
    if not req.title.strip():
        raise HTTPException(400, "Investigation title required.")

    conn = get_connection()
    inv_id = _next_inv_id(conn)
    conn.execute(
        """INSERT INTO investigations
           (investigation_id, title, priority, assigned_to,
            status, review_decision, notes, created_by)
           VALUES (?,?,?,?,?,?,?,?)""",
        (inv_id, req.title.strip(), req.priority,
         user["investigator_id"], "open", "pending",
         req.notes, user["investigator_id"]),
    )
    inv_pk = conn.execute("SELECT last_insert_rowid()").fetchone()

    for entity_type, entity_ids in (
            ("account", req.accounts),
            ("transaction", req.transactions),
            ("money_trail", req.trails),
            ("cluster", req.clusters)):
        for eid in entity_ids:
            conn.execute(
                """INSERT OR IGNORE INTO
                   investigation_entities
                   (investigation_id, entity_type, entity_id)
                   VALUES (?,?,?)""",
                (inv_id, entity_type, eid),
            )
    for alert_id in req.alerts:
        conn.execute(
            """INSERT OR IGNORE INTO
               investigation_entities
               (investigation_id, entity_type, entity_id)
               VALUES (?,?,?)""",
            (inv_id, "alert", str(alert_id)),
        )
    conn.commit()

    audit.log(user["investigator_id"],
              f"Created investigation {inv_id}",
              entity_type="investigation",
              entity_id=inv_id,
              action_type="create")
    return {"investigation_id": inv_id, "status": "open"}


@router.get("")
def list_investigations(
        status: str | None = None,
        user: dict = Depends(get_current_user)):
    conn = get_connection()
    where, params = [], []
    if status:
        where.append("status = ?")
        params.append(status)
    clause = f"WHERE {' AND '.join(where)}" if where else ""
    rows = conn.execute(
        f"""SELECT * FROM investigations {clause}
            ORDER BY id DESC LIMIT 100""",
        params,
    ).fetchall()
    return {"investigations": [dict(r) for r in rows]}


@router.get("/{investigation_id}")
def investigation_detail(investigation_id: str,
                            user: dict = Depends(get_current_user)):
    conn = get_connection()
    inv = conn.execute(
        "SELECT * FROM investigations WHERE investigation_id = ?",
        (investigation_id,),
    ).fetchone()
    if not inv:
        raise HTTPException(
            404,
            f"Investigation {investigation_id} not found.")

    entities = conn.execute(
        """SELECT entity_type, entity_id FROM
           investigation_entities WHERE investigation_id = ?""",
        (investigation_id,),
    ).fetchall()

    # risk context for attached accounts
    account_context = []
    for e in entities:
        if e["entity_type"] == "account":
            r = conn.execute(
                "SELECT risk_score, risk_category "
                "FROM risk_scores WHERE account_id = ?",
                (e["entity_id"],),
            ).fetchone()
            if r:
                account_context.append({
                    "account_id": e["entity_id"],
                    "risk_score": r["risk_score"],
                    "risk_category": r["risk_category"],
                })

    # details for attached money trails
    trail_details = []
    for e in entities:
        if e["entity_type"] == "money_trail":
            t = conn.execute(
                "SELECT * FROM money_trails "
                "WHERE trail_id = ?",
                (e["entity_id"],),
            ).fetchone()
            if t:
                trail_details.append(dict(t))

    audit.log(user["investigator_id"],
              f"Viewed investigation {investigation_id}",
              entity_type="investigation",
              entity_id=investigation_id,
              action_type="view")

    result = dict(inv)
    result["entities"] = [dict(e) for e in entities]
    result["account_context"] = account_context
    result["trail_details"] = trail_details
    return result


@router.patch("/{investigation_id}")
def update_investigation(
        investigation_id: str,
        req: InvestigationUpdate,
        user: dict = Depends(require("update_status"))):
    valid = {"open", "under_review", "escalated",
               "resolved", "closed"}
    conn = get_connection()
    inv = conn.execute(
        "SELECT * FROM investigations WHERE investigation_id = ?",
        (investigation_id,),
    ).fetchone()
    if not inv:
        raise HTTPException(404, "Investigation not found.")

    updates, params = [], []
    if req.status:
        if req.status not in valid:
            raise HTTPException(
                400, f"Status must be one of: "
                        f"{', '.join(sorted(valid))}")
        updates.append("status = ?")
        params.append(req.status)
    if req.priority:
        updates.append("priority = ?")
        params.append(req.priority)
    if req.notes is not None:
        updates.append("notes = ?")
        params.append(req.notes)
    if req.review_decision:
        decisions = {"pending", "confirmed_suspicious",
                        "false_positive", "inconclusive"}
        if req.review_decision not in decisions:
            raise HTTPException(
                400, f"Review decision must be one of: "
                        f"{', '.join(sorted(decisions))}")
        updates.append("review_decision = ?")
        params.append(req.review_decision)
    # explicit reopen: resolved/closed -> open
    if req.reopen:
        if inv["status"] not in ("resolved", "closed"):
            raise HTTPException(
                400, "Only resolved or closed "
                        "investigations can be reopened.")
        updates.append("status = ?")
        params.append("open")

    if updates:
        updates.append("updated_at = datetime('now')")
        params.append(investigation_id)
        conn.execute(
            f"""UPDATE investigations
                SET {', '.join(updates)}
                WHERE investigation_id = ?""",
            params,
        )
        conn.commit()

    audit.log(user["investigator_id"],
              f"Updated investigation {investigation_id}",
              entity_type="investigation",
              entity_id=investigation_id,
              action_type="update_status",
              details=(req.status or req.review_decision
                        or ("reopened" if req.reopen
                            else "")))
    return {"investigation_id": investigation_id,
            "updated": True,
            "reopened": req.reopen}


@router.get("/{investigation_id}/report")
def investigation_report(investigation_id: str,
                            user: dict = Depends(
                                require("export"))):
    """Structured investigation summary (printable)."""
    conn = get_connection()
    inv = conn.execute(
        "SELECT * FROM investigations WHERE investigation_id = ?",
        (investigation_id,),
    ).fetchone()
    if not inv:
        raise HTTPException(404, "Investigation not found.")

    entities = conn.execute(
        """SELECT entity_type, entity_id FROM
           investigation_entities WHERE investigation_id = ?""",
        (investigation_id,),
    ).fetchall()

    accounts = [e["entity_id"] for e in entities
                if e["entity_type"] == "account"]
    trails = [e["entity_id"] for e in entities
              if e["entity_type"] == "money_trail"]

    account_rows = []
    total_amount = 0.0
    for a in accounts:
        r = conn.execute(
            """SELECT r.account_id, r.risk_score,
                      r.risk_category, r.contributors,
                      a.in_amount, a.out_amount, a.tx_count
               FROM risk_scores r JOIN accounts a
                 ON a.account_id = r.account_id
               WHERE r.account_id = ?""",
            (a,),
        ).fetchone()
        if r:
            account_rows.append(dict(r))
            total_amount += float(r["in_amount"] +
                                    r["out_amount"])

    trail_rows = []
    for t in trails:
        tr = conn.execute(
            "SELECT * FROM money_trails WHERE trail_id = ?",
            (t,),
        ).fetchone()
        if tr:
            trail_rows.append(dict(tr))

    audit.log(user["investigator_id"],
              f"Exported report for {investigation_id}",
              entity_type="investigation",
              entity_id=investigation_id,
              action_type="export")

    return {
        "investigation_id": inv["investigation_id"],
        "title": inv["title"],
        "priority": inv["priority"],
        "status": inv["status"],
        "assigned_to": inv["assigned_to"],
        "created_by": inv["created_by"],
        "created_at": inv["created_at"],
        "accounts": account_rows,
        "trails": trail_rows,
        "total_amount": round(total_amount, 2),
        "notes": inv["notes"],
        "entities": [dict(e) for e in entities],
        "generated_at": datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"),
        "disclaimer": "Generated from synthetic/demo data "
                        "for prototype evaluation. Risk scores "
                        "support prioritisation and do not "
                        "establish guilt or fraud.",
    }


def _next_inv_id(conn) -> str:
    year = datetime.now().year
    row = conn.execute(
        """SELECT COUNT(*) AS n FROM investigations
           WHERE investigation_id LIKE ?""",
        (f"INV-{year}-%",),
    ).fetchone()
    return f"INV-{year}-{int(row['n']) + 1:04d}"
