"""Account-level behavioural feature extraction.

Computes the features required by the risk engine and the anomaly model.
All features are explainable and visible to the investigator.
"""
from __future__ import annotations

from datetime import timedelta

import numpy as np
import pandas as pd

from app.config import BURST_WINDOW_MINUTES, RAPID_PASS_MINUTES


def extract_features(df: pd.DataFrame) -> pd.DataFrame:
    """Compute account features from a validated transaction DataFrame."""
    ts = pd.to_datetime(df["_ts"])
    df = df.assign(_ts=ts).sort_values("_ts")

    frames = []
    for account, group in _iter_accounts(df):
        features = _account_features(account, group, df)
        frames.append(features)

    out = pd.DataFrame(frames)
    if out.empty:
        return out

    # normalise continuous features to 0-1 for ML input
    for col in ["tx_count", "in_amount", "out_amount", "counterparties", "degree"]:
        out[f"{col}_norm"] = _minmax(out[col])

    return out


def _iter_accounts(df: pd.DataFrame):
    """Yield (account_id, incoming+outgoing transactions) per account."""
    seen: dict[str, list[pd.DataFrame]] = {}
    for account, group in df.groupby("sender_account"):
        seen.setdefault(account, []).append(group)
    for account, group in df.groupby("receiver_account"):
        seen.setdefault(account, []).append(group)
    for account, parts in seen.items():
        yield account, pd.concat(parts).sort_values("_ts")


def _account_features(account: str, group: pd.DataFrame, all_df: pd.DataFrame) -> dict:
    incoming = group[group["receiver_account"] == account]
    outgoing = group[group["sender_account"] == account]

    in_amount = float(incoming["amount"].sum())
    out_amount = float(outgoing["amount"].sum())
    tx_count = int(len(group))
    counterparties = pd.concat([incoming["sender_account"], outgoing["receiver_account"]]).nunique()

    # velocity: peak transactions in the busiest single hour
    # (mule accounts transact in short bursts; average rate
    #  over a long span dilutes the signal)
    times = pd.to_datetime(group["_ts"])
    hourly = times.dt.floor("h").value_counts()
    velocity = float(hourly.max()) if len(hourly) else float(tx_count)

    # in/out ratio
    in_out_ratio = float(out_amount / in_amount) if in_amount > 0 else (0.0 if out_amount == 0 else 99.0)

    # rapid pass-through: how much received value leaves within the
    # window (cumulative across all outgoing transfers in the window)
    rapid_count, rapid_value = 0, 0.0
    for _, row in incoming.iterrows():
        t0 = row["_ts"]
        later = outgoing[pd.to_datetime(outgoing["_ts"]) > t0]
        if later.empty:
            continue
        window_end = t0 + pd.Timedelta(minutes=RAPID_PASS_MINUTES)
        in_window = later[pd.to_datetime(later["_ts"]) <= window_end]
        if not in_window.empty:
            rapid_count += 1
            rapid_value += float(in_window["amount"].sum())
    rapid_value = min(rapid_value, in_amount)
    rapid_pass_pct = float(100.0 * rapid_value / in_amount) if in_amount > 0 else 0.0

    # burst: max transactions inside any BURST_WINDOW_MINUTES sliding window
    burst = _burst_score(times)

    # temporal concentration: share of activity inside the busiest hour
    temporal_concentration = _temporal_concentration(times)

    # network degree
    degree = int(counterparties)
    in_degree = int(incoming["sender_account"].nunique())
    out_degree = int(outgoing["receiver_account"].nunique())

    return {
        "account_id": account,
        "tx_count": tx_count,
        "velocity": round(velocity, 4),
        "in_amount": round(in_amount, 2),
        "out_amount": round(out_amount, 2),
        "in_out_ratio": round(in_out_ratio, 4),
        "counterparties": int(counterparties),
        "rapid_pass_pct": round(rapid_pass_pct, 2),
        "rapid_count": int(rapid_count),
        "burst_score": round(burst, 4),
        "temporal_concentration": round(temporal_concentration, 4),
        "degree": degree,
        "in_degree": in_degree,
        "out_degree": out_degree,
    }


def _burst_score(times: pd.Series) -> float:
    """0-1 score: density of the busiest BURST_WINDOW_MINUTES window vs mean."""
    if len(times) < 2:
        return 0.0
    times = times.sort_values().reset_index(drop=True)
    window = timedelta(minutes=BURST_WINDOW_MINUTES)
    max_in_window = 1
    left = 0
    arr = times.values
    for right in range(len(arr)):
        while pd.Timestamp(arr[right]) - pd.Timestamp(arr[left]) > window:
            left += 1
        max_in_window = max(max_in_window, right - left + 1)
    mean_rate = len(times) / max((times.max() - times.min()).total_seconds() / 3600.0, 1 / 60.0)
    expected = max(mean_rate * (BURST_WINDOW_MINUTES / 60.0), 0.5)
    return float(min(max_in_window / expected, 5.0) / 5.0)


def _temporal_concentration(times: pd.Series) -> float:
    """Share of transactions occurring in the single busiest hour of the day."""
    if len(times) == 0:
        return 0.0
    counts = pd.Series(times.dt.hour).value_counts()
    return float(counts.max() / len(times))


def _minmax(series: pd.Series) -> pd.Series:
    s = series.astype(float)
    if s.max() == s.min():
        return pd.Series(0.0, index=s.index)
    return (s - s.min()) / (s.max() - s.min())


def build_feature_matrix(features: pd.DataFrame) -> np.ndarray:
    """Matrix for the anomaly model: normalised behavioural features."""
    cols = ["tx_count_norm", "in_amount_norm", "out_amount_norm",
            "counterparties_norm", "degree_norm", "rapid_pass_pct",
            "burst_score", "temporal_concentration", "velocity"]
    return features[cols].fillna(0.0).to_numpy(dtype=float)
