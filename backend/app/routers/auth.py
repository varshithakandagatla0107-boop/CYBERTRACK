"""Authentication endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.api.deps import get_current_user
from app.db.database import get_connection
from app.security import audit, auth

router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginRequest(BaseModel):
    investigator_id: str
    password: str


@router.post("/login")
def login(req: LoginRequest):
    if not req.investigator_id or not req.password:
        raise HTTPException(400, "Investigator ID and password are required.")
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM users WHERE investigator_id = ?",
        (req.investigator_id.strip(),),
    ).fetchone()
    if not row or not auth.verify_password(req.password, row["password_hash"]):
        audit.log(req.investigator_id, "Failed login attempt",
                  action_type="auth", result="failure")
        raise HTTPException(401, "Invalid credentials.")

    token = auth.create_token(row["investigator_id"], row["role"])
    audit.log(row["investigator_id"], "Logged in", action_type="auth")
    return {
        "token": token,
        "user": {
            "investigator_id": row["investigator_id"],
            "role": row["role"],
            "full_name": row["full_name"],
        },
        "environment": "Prototype Environment — Synthetic Data",
    }


@router.get("/me")
def me(user: dict = Depends(get_current_user)):
    return user
