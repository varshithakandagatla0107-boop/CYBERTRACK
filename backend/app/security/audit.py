"""Audit service — records investigator actions for accountability.

Records: timestamp, investigator, action, entity, action type, result.
Never stores passwords or sensitive financial data.
"""
from __future__ import annotations

import sqlite3

from app.db.database import get_connection


def log(investigator_id: str, action: str, entity_type: str | None = None,
        entity_id: str | None = None, action_type: str = "access",
        result: str = "success", details: str = "") -> None:
    conn: sqlite3.Connection = get_connection()
    conn.execute(
        """INSERT INTO audit_logs
           (investigator_id, action, entity_type, entity_id,
            action_type, result, details)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (investigator_id, action, entity_type, entity_id,
         action_type, result, details),
    )
    conn.commit()


def recent(limit: int = 100, investigator_id: str | None = None) -> list[dict]:
    conn: sqlite3.Connection = get_connection()
    if investigator_id:
        rows = conn.execute(
            """SELECT * FROM audit_logs WHERE investigator_id = ?
               ORDER BY id DESC LIMIT ?""",
            (investigator_id, limit),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM audit_logs ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [dict(r) for r in rows]
