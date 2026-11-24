"""Shared API dependencies: authentication + RBAC."""
from __future__ import annotations

from fastapi import Depends, Header, HTTPException

from app.db.database import get_connection
from app.security import auth


def get_current_user(authorization: str | None = Header(default=None)) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401,
                            detail="Authentication required.")
    token = authorization.split(" ", 1)[1].strip()
    payload = auth.decode_token(token)
    if not payload:
        raise HTTPException(status_code=401,
                            detail="Invalid or expired session.")
    if "error" in payload:
        raise HTTPException(status_code=401, detail=payload["error"])

    conn = get_connection()
    row = conn.execute(
        "SELECT investigator_id, role, full_name FROM users WHERE investigator_id = ?",
        (payload["sub"],),
    ).fetchone()
    if not row:
        raise HTTPException(status_code=401, detail="Account not found.")
    return {
        "investigator_id": row["investigator_id"],
        "role": row["role"],
        "full_name": row["full_name"],
    }


def require(permission: str):
    def checker(user: dict = Depends(get_current_user)) -> dict:
        if not auth.require_permission(user["role"], permission):
            raise HTTPException(
                status_code=403,
                detail=f"Role '{user['role']}' cannot perform this action.",
            )
        return user
    return checker
