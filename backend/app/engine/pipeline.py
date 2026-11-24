"""Analysis pipeline orchestrator.

Runs the complete PS-35 pipeline and persists every stage to SQLite:

TRANSACTION DATA → DATA CLEANING → FEATURE EXTRACTION → TRANSACTION GRAPH
→ BEHAVIOUR + NETWORK ANALYSIS → MULE / ANOMALY DETECTION → TEMPORAL
MONEY-TRAIL TRACING → EXPLAINABLE RISK → INVESTIGATION PRIORITY
→ OPTIONAL CASH-OUT INTELLIGENCE
"""
from __future__ import annotations

import sqlite3
from datetime import datetime

import networkx as nx
import pandas as pd

from app.db.database import get_connection, transaction
from app.engine import alert_engine, graph_engine, ingestion
from app.engine.features import extract_features
from app.engine.ml_engine import detect_anomalies
from app.engine.risk_engine import score_accounts


def persist_dataset(conn: sqlite3.Connection, name: str, source: str,
                    df: pd.DataFrame, report: dict) -> int:
    cur = conn.execute(
        """INSERT INTO datasets (name, source, row_count, valid_rows,
                                 flagged_rows)
           VALUES (?, ?, ?, ?, ?)""",
        (name, source, report["total_rows"], report["valid_rows"],
         report["flagged_rows"]),
    )
    dataset_id = cur.lastrowid

    for _, row in df.iterrows():
        conn.execute(
            """INSERT OR IGNORE INTO transactions
               (transaction_id, sender_account, receiver_account, amount,
                timestamp, transaction_type, channel, sender_location,
                receiver_location, device_id, ip_hash, merchant_id,
                cashout_location, lat, lon, dataset_id)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (row["transaction_id"], row["sender_account"],
             row["receiver_account"], float(row["amount"]),
             row["timestamp"], row["transaction_type"], row["channel"],
             row["sender_location"], row["receiver_location"],
             row["device_id"], row["ip_hash"], row["merchant_id"],
             row["cashout_location"],
             float(row["lat"]) if pd.notna(row.get("lat")) else None,
             float(row["lon"]) if pd.notna(row.get("lon")) else None,
             dataset_id),
        )
    return dataset_id


def run_pipeline(df: pd.DataFrame, dataset_id: int,
                 dataset_name: str = "dataset") -> dict:
    """Execute the full analysis pipeline and persist results."""
    conn = get_connection()

    # --- feature extraction -------------------------------------------------
    features = extract_features(df)

    # --- graph construction -------------------------------------------------
    G = graph_engine.build_graph(df)
    betweenness = graph_engine.compute_centrality(G)
    community_labels = graph_engine.detect_communities(G)

    # --- anomaly detection (Isolation Forest / fallback) --------------------
    features, detection_method = detect_anomalies(features)

    # --- explainable risk ---------------------------------------------------
    risks = score_accounts(features, betweenness, detection_method)
    risk_by_account = dict(zip(risks["account_id"], risks["risk_score"]))

    # --- clusters ------------------------------------------------------------
    clusters = graph_engine.suspicious_communities(
        G, risk_by_account, community_labels, 70.0)

    # --- alerts --------------------------------------------------------------
    alerts = alert_engine.generate_alerts(features, risks, df)

    # --- persist -------------------------------------------------------------
    with transaction():
        _persist_accounts(conn, features)
        _persist_risk(conn, risks)
        _persist_clusters(conn, clusters)
        _persist_alerts(conn, alerts, dataset_id)
        _persist_features(conn, features)

    high_risk = int((risks["risk_category"] == "high").sum())
    medium_risk = int((risks["risk_category"] == "medium").sum())
    low_risk = int((risks["risk_category"] == "low").sum())

    report = {
        "status": "complete",
        "dataset_id": dataset_id,
        "dataset_name": dataset_name,
        "transactions": int(len(df)),
        "accounts": int(len(features)),
        "edges": int(G.number_of_edges()),
        "high_risk_accounts": high_risk,
        "medium_risk_accounts": medium_risk,
        "low_risk_accounts": low_risk,
        "clusters": len(clusters),
        "alerts": len(alerts),
        "detection_method": detection_method,
        "processed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "top_accounts": risks.nlargest(10, "risk_score")[
            ["account_id", "risk_score", "risk_category"]
        ].to_dict("records"),
    }
    return report


def _persist_accounts(conn, features: pd.DataFrame) -> None:
    for _, row in features.iterrows():
        conn.execute(
            """INSERT INTO accounts (account_id, tx_count, in_amount,
                                     out_amount, unique_counterparties)
               VALUES (?,?,?,?,?)
               ON CONFLICT(account_id) DO UPDATE SET
                 tx_count=excluded.tx_count,
                 in_amount=excluded.in_amount,
                 out_amount=excluded.out_amount,
                 unique_counterparties=excluded.unique_counterparties""",
            (row["account_id"], int(row["tx_count"]),
             float(row["in_amount"]), float(row["out_amount"]),
             int(row["counterparties"])),
        )


def _persist_risk(conn, risks: pd.DataFrame) -> None:
    for _, row in risks.iterrows():
        contributors = "; ".join(
            f"{k}:{v}" for k, v in row["contributors"])
        conn.execute(
            """INSERT INTO risk_scores
               (account_id, risk_score, risk_category, contributors,
                detection_method)
               VALUES (?,?,?,?,?)
               ON CONFLICT(account_id) DO UPDATE SET
                 risk_score=excluded.risk_score,
                 risk_category=excluded.risk_category,
                 contributors=excluded.contributors,
                 detection_method=excluded.detection_method""",
            (row["account_id"], float(row["risk_score"]),
             row["risk_category"], contributors, row["detection_method"]),
        )


def _persist_features(conn, features: pd.DataFrame) -> None:
    for _, row in features.iterrows():
        conn.execute(
            """INSERT INTO account_features
               (account_id, tx_count, velocity, in_amount, out_amount,
                in_out_ratio, counterparties, rapid_pass_pct, rapid_count,
                burst_score, temporal_concentration, degree, in_degree,
                out_degree, ml_score, ml_anomaly)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
               ON CONFLICT(account_id) DO UPDATE SET
                 tx_count=excluded.tx_count, velocity=excluded.velocity,
                 in_amount=excluded.in_amount,
                 out_amount=excluded.out_amount,
                 in_out_ratio=excluded.in_out_ratio,
                 counterparties=excluded.counterparties,
                 rapid_pass_pct=excluded.rapid_pass_pct,
                 rapid_count=excluded.rapid_count,
                 burst_score=excluded.burst_score,
                 temporal_concentration=excluded.temporal_concentration,
                 degree=excluded.degree,
                 in_degree=excluded.in_degree,
                 out_degree=excluded.out_degree,
                  ml_score=excluded.ml_score,
                  ml_anomaly=excluded.ml_anomaly""",
            (row["account_id"], int(row["tx_count"]),
             float(row["velocity"]), float(row["in_amount"]),
             float(row["out_amount"]), float(row["in_out_ratio"]),
             int(row["counterparties"]), float(row["rapid_pass_pct"]),
             int(row["rapid_count"]), float(row["burst_score"]),
             float(row["temporal_concentration"]), int(row["degree"]),
             int(row["in_degree"]), int(row["out_degree"]),
             float(row.get("ml_score", 0.0) or 0.0),
             int(row.get("ml_anomaly", 0) or 0)),
        )


def _persist_clusters(conn, clusters: list[dict]) -> None:
    for cluster in clusters:
        conn.execute(
            """INSERT INTO clusters
               (cluster_label, account_count, total_amount, avg_risk,
                main_intermediary, primary_pattern, account_list)
               VALUES (?,?,?,?,?,?,?)
               ON CONFLICT(cluster_label) DO UPDATE SET
                 account_count=excluded.account_count,
                 total_amount=excluded.total_amount,
                 avg_risk=excluded.avg_risk,
                 main_intermediary=excluded.main_intermediary,
                 primary_pattern=excluded.primary_pattern,
                 account_list=excluded.account_list""",
            (cluster["cluster_label"], cluster["account_count"],
             float(cluster["total_amount"]), float(cluster["avg_risk"]),
             cluster["main_intermediary"], cluster["primary_pattern"],
             ",".join(cluster["accounts"])),
        )


def _persist_alerts(conn, alerts: list[dict], dataset_id: int) -> None:
    conn.execute("DELETE FROM alerts")
    for alert in alerts:
        conn.execute(
            """INSERT INTO alerts
               (alert_type, title, description, account_ids, amount,
                occurred_at, risk_score, severity, recommended_action)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            (alert["alert_type"], alert["title"], alert["description"],
             alert["account_ids"],
             float(alert["amount"]) if alert.get("amount") else None,
             alert.get("occurred_at"),
             float(alert["risk_score"]) if alert.get("risk_score") else None,
             alert["severity"], alert["recommended_action"]),
        )


_graph_cache: dict | None = None


def build_graph_cached():
    """Cached transaction graph (rebuilt when dataset changes)."""
    global _graph_cache
    if _graph_cache is not None:
        return _graph_cache
    conn = get_connection()
    rows = conn.execute(
        "SELECT transaction_id, sender_account, "
        "receiver_account, amount, timestamp FROM transactions"
    ).fetchall()
    if not rows:
        return None
    import pandas as pd
    df = pd.DataFrame([dict(r) for r in rows])
    df["_ts"] = pd.to_datetime(df["timestamp"])
    _graph_cache = __import__(
        "app.engine.graph_engine", fromlist=["build_graph"]
    ).build_graph(df)
    return _graph_cache


def invalidate_cache() -> None:
    global _graph_cache
    _graph_cache = None


def load_dataset(df: pd.DataFrame, name: str,
                 source: str = "demo") -> dict:
    """Ingest + validate + analyse.

    Loads one investigation case at a time: the
    previous working dataset (transactions, features,
    risk, clusters, alerts, trails) is cleared so
    every view reflects the current case only.
    """
    report = {
        "total_rows": int(len(df)),
        "valid_rows": int(len(df)),
        "flagged_rows": 0,
        "errors": [],
        "warnings": [],
        "flags": {},
    }
    conn = get_connection()
    invalidate_cache()
    with transaction():
        for table in ("trail_hops", "money_trails",
                        "alerts", "clusters",
                        "risk_scores", "account_features",
                        "accounts", "transactions"):
            conn.execute(f"DELETE FROM {table}")
        dataset_id = persist_dataset(conn, name, source, df, report)
    result = run_pipeline(df, dataset_id, name)
    invalidate_cache()
    return result
