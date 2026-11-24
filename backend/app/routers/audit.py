"""Audit log endpoints (admin / full view)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_current_user, require
from app.db.database import get_connection
from app.security import audit

router = APIRouter(prefix="/api/audit", tags=["audit"])


@router.get("")
def audit_log(
    limit: int = Query(default=100, le=500),
    investigator_id: str | None = Query(default=None),
    user: dict = Depends(require("view_audit")),
):
    entries = audit.recent(limit=limit,
                            investigator_id=investigator_id)
    return {"entries": entries, "count": len(entries)}


@router.get("/my")
def my_audit_log(
    limit: int = Query(default=50, le=200),
    user: dict = Depends(get_current_user),
):
    """Investigator's own actions (available to all roles)."""
    entries = audit.recent(limit=limit,
                            investigator_id=user["investigator_id"])
    return {"entries": entries, "count": len(entries)}
