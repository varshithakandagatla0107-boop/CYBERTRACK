"""Explainable risk engine.

Risk Score = weighted sum of behavioural + network + velocity + pass-through
+ burst + centrality + anomaly signals, normalised to 0-100.

The engine is deliberately transparent: every score is returned with its
contributors so the UI can show "Why this score?".

Risk score is an analytical prioritisation signal, not a determination of fraud.
"""
from __future__ import annotations

import pandas as pd

from app.config import RISK_THRESHOLDS, RISK_WEIGHTS


def score_accounts(features: pd.DataFrame,
                   betweenness: dict[str, float],
                   detection_method: str) -> pd.DataFrame:
    """Score every account and return (features + risk columns)."""
    rows = []
    weight_sum = sum(RISK_WEIGHTS.values())
    for _, row in features.iterrows():
        # --- raw signals (0-1 normalised where applicable) ---
        pass_through = min(row["rapid_pass_pct"] / 100.0, 1.0)
        velocity = min(row["velocity"] / 4.0, 1.0)          # ~4 tx/hour saturates
        counterparty = min(row["counterparties"] / 12.0, 1.0)  # 12 counterparties saturates
        burst = min(row["burst_score"], 1.0)
        temporal = min(row["temporal_concentration"] * 1.4, 1.0)
        max_between = max(betweenness.values()) if betweenness else 1.0
        between_norm = betweenness.get(row["account_id"], 0.0) / max(max_between, 1e-9)
        # connector score: balanced in/out flow identifies intermediaries
        # (pure payers or pure receivers score 0; mule hubs score ~1)
        in_deg = int(row.get("in_degree", 0))
        out_deg = int(row.get("out_degree", 0))
        connector = (min(in_deg, out_deg) /
                        max(in_deg, out_deg, 1))
        centrality = 0.7 * connector + 0.3 * between_norm
        ml = min(float(row.get("ml_score", 0.0)), 1.0)

        raw = {
            "pass_through": pass_through,
            "velocity": velocity,
            "centrality": centrality,
            "counterparty_diversity": counterparty,
            "burst": burst,
            "temporal_concentration": temporal,
            "ml_anomaly": ml,
        }
        score = sum(RISK_WEIGHTS[k] * raw[k] for k in RISK_WEIGHTS) / weight_sum * 100.0
        score = round(min(max(score, 0.0), 100.0), 1)

        contributors = sorted(
            ((k, round(RISK_WEIGHTS[k] * raw[k] / weight_sum * 100.0, 1)) for k in RISK_WEIGHTS),
            key=lambda kv: -kv[1],
        )

        rows.append({
            **row.to_dict(),
            "risk_score": score,
            "risk_category": _category(score),
            "contributors": contributors,
            "detection_method": detection_method,
        })

    return pd.DataFrame(rows)


def _category(score: float) -> str:
    if score >= RISK_THRESHOLDS["high"]:
        return "high"
    if score >= RISK_THRESHOLDS["medium"]:
        return "medium"
    return "low"


def explain_reasons(row: dict) -> list[str]:
    """Human-readable 'why suspicious' strings for the investigation page."""
    reasons = []
    if row["rapid_pass_pct"] >= 60:
        reasons.append(
            f"{int(row['rapid_pass_pct'])}% of received funds forwarded within "
            f"15 minutes (rapid pass-through)")
    if row["velocity"] >= 3:
        reasons.append(f"High transaction velocity ({row['velocity']:.1f} transactions/hour)")
    if row["counterparties"] >= 8:
        reasons.append(f"{int(row['counterparties'])} unique counterparties (high connectivity)")
    if row["burst_score"] >= 0.5:
        reasons.append("Sudden transaction burst detected")
    if row["temporal_concentration"] >= 0.6:
        reasons.append("Activity concentrated in an unusually short time window")
    if row.get("ml_anomaly") == 1:
        method = row.get("detection_method", "analytical model")
        reasons.append(f"Anomaly signal from {method} analysis")
    if row["degree"] >= 8:
        reasons.append(f"High network degree — connector between {int(row['degree'])} accounts")
    if row["in_out_ratio"] > 0.85:
        reasons.append("Nearly all received value is forwarded onward")
    if not reasons:
        reasons.append("Below behavioural thresholds — no specific anomaly pattern")
    return reasons
