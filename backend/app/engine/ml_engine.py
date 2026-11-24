"""Lightweight anomaly-detection layer.

Uses scikit-learn Isolation Forest when available. If the runtime cannot
support it, falls back to a deterministic analytical score (robust z-score
composite). Never fakes a result: the active method is reported with every
score so the UI can show "Detection method: Isolation Forest" or
"Detection method: Analytical fallback".
"""
from __future__ import annotations

import numpy as np
import pandas as pd

ISOLATION_FOREST_AVAILABLE = False
try:
    from sklearn.ensemble import IsolationForest
    ISOLATION_FOREST_AVAILABLE = True
except Exception:  # pragma: no cover
    IsolationForest = None


def detect_anomalies(features: pd.DataFrame) -> tuple[pd.DataFrame, str]:
    """Return features with ml_score (0-1) and ml_anomaly (0/1), plus method name."""
    if ISOLATION_FOREST_AVAILABLE and len(features) >= 10:
        try:
            return _isolation_forest(features), "Isolation Forest"
        except Exception:
            return _analytical_fallback(features), "Analytical fallback"
    return _analytical_fallback(features), "Analytical fallback"


def _isolation_forest(features: pd.DataFrame) -> pd.DataFrame:
    from app.engine.features import build_feature_matrix
    X = build_feature_matrix(features)
    # contamination tuned conservatively for a mule-typology demo
    model = IsolationForest(n_estimators=120, contamination=0.05, random_state=42)
    preds = model.fit_predict(X)
    scores = model.score_samples(X)
    # normalise score_samples to 0-1 (more negative = more anomalous)
    lo, hi = float(scores.min()), float(scores.max())
    norm = (scores - lo) / (hi - lo) if hi > lo else scores * 0
    out = features.copy()
    out["ml_score"] = (1.0 - norm).round(4)
    out["ml_anomaly"] = (preds == -1).astype(int)
    return out


def _analytical_fallback(features: pd.DataFrame) -> pd.DataFrame:
    """Deterministic composite anomaly score (robust z-score mean)."""
    out = features.copy()
    cols = ["velocity", "counterparties", "rapid_pass_pct",
            "burst_score", "temporal_concentration"]
    composite = np.zeros(len(out))
    for col in cols:
        s = out[col].astype(float)
        median = s.median()
        mad = (s - median).abs().median()
        if mad == 0:
            z = (s - median) / (s.std() + 1e-9)
        else:
            z = 0.6745 * (s - median) / (mad + 1e-9)
        composite += np.clip(np.abs(z), 0, 5)
    composite /= len(cols)
    mx = composite.max()
    out["ml_score"] = pd.Series(
        (composite / mx if mx > 0 else composite), index=out.index
    ).round(4)
    threshold = float(np.percentile(out["ml_score"], 95))
    out["ml_anomaly"] = (out["ml_score"] >= max(threshold, 0.5)).astype(int)
    return out
