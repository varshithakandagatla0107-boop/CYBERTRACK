"""Settings endpoint — system configuration and integrations.

Shows what is configurable and clearly labels future integrations
that do NOT currently exist.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import get_current_user, require
from app.config import (BURST_WINDOW_MINUTES,
                        MULTI_HOP_MAX_MINUTES,
                        RAPID_PASS_MINUTES,
                        RISK_WEIGHTS)
from app.db.database import get_connection
from app.security import audit

router = APIRouter(prefix="/api/settings",
                    tags=["settings"])


@router.get("")
def settings(user: dict = Depends(get_current_user)):
    conn = get_connection()
    users = conn.execute(
        """SELECT investigator_id, role, full_name,
                  created_at FROM users""").fetchall()
    audit.log(user["investigator_id"],
              "Viewed settings", action_type="view")
    return {
        "environment": "Prototype Environment — Synthetic Data",
        "analysis_parameters": {
            "rapid_pass_through_minutes": RAPID_PASS_MINUTES,
            "burst_window_minutes": BURST_WINDOW_MINUTES,
            "rapid_multi_hop_minutes": MULTI_HOP_MAX_MINUTES,
            "risk_weights": RISK_WEIGHTS,
        },
        "users": [dict(u) for u in users]
                    if user["role"] == "admin" else [],
        "future_integrations": [
            {"name": "Bank transaction API feeds",
             "status": "Future Authorized Integration"},
            {"name": "I4C workflow integration",
             "status": "Future Authorized Integration"},
            {"name": "Real-time transaction streams",
             "status": "Future Authorized Integration"},
            {"name": "Geospatial intelligence service",
             "status": "Future Authorized Integration"},
            {"name": "Advanced graph / sequence models",
             "status": "Future Authorized Integration"},
        ],
        "data_privacy": (
            "All transactions shown in this prototype are "
            "synthetic demonstration data."),
    }
