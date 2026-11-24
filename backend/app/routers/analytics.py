"""Analytics & model transparency.

Shows what the detection layer does, which features it uses,
and clearly states that model output supports investigator
prioritisation and requires human verification.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.config import RISK_THRESHOLDS, RISK_WEIGHTS
from app.db.database import get_connection
from app.engine import ml_engine
from app.security import audit

router = APIRouter(prefix="/api/analytics",
                    tags=["analytics"])


@router.get("/model")
def model_transparency(user: dict = Depends(get_current_user)):
    conn = get_connection()
    ds = conn.execute(
        "SELECT * FROM datasets ORDER BY id DESC LIMIT 1"
    ).fetchone()

    method_row = conn.execute(
        "SELECT detection_method FROM risk_scores LIMIT 1"
    ).fetchone()
    method = (method_row["detection_method"]
                if method_row else "not run")

    accounts = conn.execute(
        "SELECT COUNT(*) AS n FROM accounts").fetchone()["n"]
    anomalies = conn.execute(
        "SELECT COUNT(*) AS n FROM account_features "
        "WHERE ml_anomaly = 1").fetchone()["n"]
    high = conn.execute(
        "SELECT COUNT(*) AS n FROM risk_scores "
        "WHERE risk_category = 'high'").fetchone()["n"]
    medium = conn.execute(
        "SELECT COUNT(*) AS n FROM risk_scores "
        "WHERE risk_category = 'medium'").fetchone()["n"]

    audit.log(user["investigator_id"],
              "Viewed analytics/model transparency",
              action_type="view")

    return {
        "detection_method": method,
        "isolation_forest_available":
            ml_engine.ISOLATION_FOREST_AVAILABLE,
        "fallback_description": (
            "Deterministic analytical scoring "
            "(robust z-score composite) used when "
            "scikit-learn is unavailable."),
        "features_used": [
            "Transaction velocity",
            "Incoming volume",
            "Outgoing volume",
            "In/out ratio",
            "Counterparty diversity",
            "Rapid pass-through percentage",
            "Transaction burst score",
            "Temporal concentration",
            "Network degree",
            "Betweenness centrality",
            "Anomaly model score",
        ],
        "accounts_analyzed": accounts,
        "anomalies_detected": anomalies,
        "high_risk": high,
        "medium_risk": medium,
        "thresholds": RISK_THRESHOLDS,
        "weights": RISK_WEIGHTS,
        "risk_disclaimer": (
            "Risk score is an analytical prioritisation "
            "signal, not a determination of fraud. Model "
            "output supports investigator prioritisation "
            "and requires human verification."),
        "last_analysis": ds["created_at"] if ds else None,
    }


@router.get("/risk-distribution")
def risk_distribution(user: dict = Depends(get_current_user)):
    conn = get_connection()
    buckets = conn.execute(
        """SELECT
             CASE
               WHEN risk_score >= 70 THEN '70-100 (High)'
               WHEN risk_score >= 40 THEN '40-69 (Medium)'
               ELSE '0-39 (Low)'
             END AS bucket,
             COUNT(*) AS n
           FROM risk_scores GROUP BY bucket""").fetchall()
    return {
        "distribution": [dict(b) for b in buckets],
    }
