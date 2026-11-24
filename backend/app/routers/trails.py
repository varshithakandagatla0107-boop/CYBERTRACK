"""Money trail endpoints — temporal money-trail tracing."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.api.deps import get_current_user, require
from app.db.database import get_connection
from app.engine.pipeline import build_graph_cached
from app.engine.trail_engine import trace_trail
from app.security import audit

router = APIRouter(prefix="/api/trails", tags=["trails"])


class TraceRequest(BaseModel):
    source: str
    destination: str | None = None
    amount: float | None = None
    max_hops: int = 10
    max_minutes: int | None = None


@router.post("/trace")
def trace(req: TraceRequest,
            user: dict = Depends(require("trace"))):
    """Reconstruct the chronological money trail."""
    conn = get_connection()
    G = build_graph_cached()
    if G is None:
        raise HTTPException(
            404,
            "No transactions loaded. Upload a dataset or "
            "use the demonstration dataset.",
        )

    # load transaction dataframe
    import pandas as pd
    rows = conn.execute(
        "SELECT * FROM transactions").fetchall()
    df = pd.DataFrame([dict(r) for r in rows])
    if df.empty:
        raise HTTPException(404, "No transactions available.")
    df["_ts"] = pd.to_datetime(df["timestamp"])

    result = trace_trail(
        df, G,
        source=req.source.upper(),
        destination=req.destination.upper()
            if req.destination else None,
        amount_hint=req.amount,
        max_hops=req.max_hops,
        max_minutes=req.max_minutes,
    )

    # persist trail
    if result.get("hops", 0) > 0:
        trail_id = _next_trail_id(conn)
        result["trail_id"] = trail_id
        conn.execute(
            """INSERT INTO money_trails
               (trail_id, source_account, terminal_account,
                starting_amount, tracked_amount, hops,
                duration_minutes, accounts_involved,
                amount_difference, summary)
               VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (trail_id, result["source_account"],
             result["terminal_account"],
             result["starting_amount"], result["tracked_amount"],
             result["hops"], result["duration_minutes"],
             result["accounts_involved"],
             result["amount_difference"], result["summary"]),
        )
        for hop in result["hops_detail"]:
            conn.execute(
                """INSERT INTO trail_hops
                   (trail_id, hop_index, from_account,
                    to_account, amount, timestamp,
                    transaction_id)
                   VALUES (?,?,?,?,?,?,?)""",
                (trail_id, hop["hop_index"],
                 hop["from_account"], hop["to_account"],
                 hop["amount"], hop["timestamp"],
                 hop["transaction_id"]),
            )
        conn.commit()

    audit.log(user["investigator_id"],
              f"Generated money trail "
              f"{result.get('trail_id', 'unsuccessful')}",
              entity_type="money_trail",
              entity_id=result.get("trail_id"),
              action_type="trace")

    # cash-out intelligence (extension, analytical estimate)
    result["cashout_intelligence"] = _cashout_intelligence(
        conn, result)
    # Required disclaimer: a reconstructed path is a temporally
    # connected transaction sequence, not definitive legal tracing.
    result["tracing_disclaimer"] = (
        "This path shows a temporally connected transaction "
        "sequence. It is not definitive legal tracing of specific "
        "currency units: transaction amounts reflect observed "
        "transfer values, and branch points mean only part of the "
        "original value may follow the shown path."
    )
    return result


@router.get("")
def list_trails(user: dict = Depends(get_current_user)):
    conn = get_connection()
    rows = conn.execute(
        """SELECT * FROM money_trails
           ORDER BY id DESC LIMIT 50""").fetchall()
    return {"trails": [dict(r) for r in rows]}


@router.get("/{trail_id}")
def trail_detail(trail_id: str,
                    user: dict = Depends(get_current_user)):
    conn = get_connection()
    trail = conn.execute(
        "SELECT * FROM money_trails WHERE trail_id = ?",
        (trail_id,),
    ).fetchone()
    if not trail:
        raise HTTPException(404,
                            f"Trail {trail_id} not found.")
    hops = conn.execute(
        """SELECT * FROM trail_hops WHERE trail_id = ?
           ORDER BY hop_index""",
        (trail_id,),
    ).fetchall()
    result = dict(trail)
    result["hops_detail"] = [dict(h) for h in hops]
    result["cashout_intelligence"] = _cashout_intelligence(
        conn, result)
    result["tracing_disclaimer"] = (
        "This path shows a temporally connected transaction "
        "sequence. It is not definitive legal tracing of specific "
        "currency units: transaction amounts reflect observed "
        "transfer values, and branch points mean only part of the "
        "original value may follow the shown path."
    )
    return result


def _next_trail_id(conn) -> str:
    row = conn.execute(
        "SELECT COUNT(*) AS n FROM money_trails").fetchone()
    return f"TRAIL-{int(row['n']) + 1:04d}"


def _cashout_intelligence(conn, trail: dict) -> dict:
    """Cash-out intelligence — EXTENSION.

    Analytical estimate only. Never claims real-world certainty.
    """
    terminal = trail.get("terminal_account", "")
    row = conn.execute(
        """SELECT cashout_location, COUNT(*) AS n,
                  SUM(amount) AS total
           FROM transactions
           WHERE receiver_account = ? AND cashout_location != ''
           GROUP BY cashout_location
           ORDER BY total DESC LIMIT 1""",
        (terminal,),
    ).fetchone()

    if not row:
        # check whether any cashout locations exist at all
        any_loc = conn.execute(
            "SELECT COUNT(*) AS n FROM transactions "
            "WHERE cashout_location != ''").fetchone()["n"]
        if not any_loc:
            return {
                "available": False,
                "message": "No location intelligence available "
                            "for this transaction set.",
            }
        return {
            "available": False,
            "message": (
                "Terminal account has no recorded cash-out "
                "location. The trail may continue beyond the "
                "observed hops."),
        }

    return {
        "available": True,
        "estimate_type": "Analytical estimate — synthetic "
                            "demonstration data",
        "likely_cashout_location": row["cashout_location"],
        "supporting_transactions": int(row["n"]),
        "total_value": round(float(row["total"] or 0), 2),
        "confidence": "moderate",
        "disclaimer": (
            "Analytical estimate based on synthetic data. "
            "Not a real-world location determination."),
    }
