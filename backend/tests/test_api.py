"""Backend test suite for CYBERTRACK.

Run:  cd backend && python -m pytest tests/ -v

Covers: CSV validation, feature calculation, risk calculation,
graph creation, trail reconstruction, cluster detection,
authentication, authorization, API responses, invalid data,
empty dataset, missing timestamps, negative amounts, duplicate
transactions, disconnected graph, no trail found, ML fallback.
"""
from __future__ import annotations

import io
import os
import sys

import pandas as pd
import pytest

# ensure app package is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))

from fastapi.testclient import TestClient

from app.db.database import init_db, get_connection
from app.seed import seed_users
from app.demo.case import generate_demo_case
from app.engine import ingestion
from app.engine.features import extract_features
from app.engine.graph_engine import (
    build_graph, compute_centrality, detect_communities,
    shortest_money_path, neighbours,
)
from app.engine.ml_engine import detect_anomalies
from app.engine.risk_engine import score_accounts
from app.engine.trail_engine import trace_trail
from app.engine.alert_engine import generate_alerts
from app.engine.pipeline import load_dataset


@pytest.fixture(scope="session")
def client():
    from app.main import app
    init_db()
    seed_users()
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="session")
def demo_df():
    return generate_demo_case(seed=7)


@pytest.fixture(scope="session")
def auth(client):
    r = client.post("/api/auth/login", json={
        "investigator_id": "investigator",
        "password": "cybertrack-demo",
    })
    assert r.status_code == 200
    return r.json()["token"]


@pytest.fixture(scope="session")
def admin_auth(client):
    r = client.post("/api/auth/login", json={
        "investigator_id": "admin",
        "password": "cybertrack-demo",
    })
    return r.json()["token"]


@pytest.fixture(scope="session")
def analyst_auth(client):
    r = client.post("/api/auth/login", json={
        "investigator_id": "analyst",
        "password": "cybertrack-demo",
    })
    return r.json()["token"]


# ----------------------------------------------------------- auth
def test_login_success(client):
    r = client.post("/api/auth/login", json={
        "investigator_id": "investigator",
        "password": "cybertrack-demo",
    })
    assert r.status_code == 200
    assert "token" in r.json()


def test_login_failure(client):
    r = client.post("/api/auth/login", json={
        "investigator_id": "investigator",
        "password": "wrong-password",
    })
    assert r.status_code == 401


def test_unauthenticated_rejected(client):
    r = client.get("/api/dashboard")
    assert r.status_code == 401


def test_rbac_investigator_cannot_upload(client, auth):
    r = client.post("/api/data/demo",
                    headers={"Authorization": f"Bearer {auth}"})
    assert r.status_code == 403


def test_rbac_analyst_can_upload(client, analyst_auth):
    r = client.post("/api/data/demo",
                    headers={
                        "Authorization": f"Bearer {analyst_auth}"})
    assert r.status_code == 200
    assert r.json()["status"] == "complete"


def test_rbac_investigator_cannot_view_audit(client, auth):
    r = client.get("/api/audit",
                   headers={"Authorization": f"Bearer {auth}"})
    assert r.status_code == 403


def test_rbac_admin_can_view_audit(client, admin_auth):
    r = client.get("/api/audit",
                   headers={
                       "Authorization": f"Bearer {admin_auth}"})
    assert r.status_code == 200


# --------------------------------------------------- CSV validation
def test_csv_missing_required_column():
    raw = "transaction_id,sender,receiver\n1,A,B\n"
    with pytest.raises(ingestion.ValidationError) as exc:
        ingestion.parse_csv(raw.encode())
    assert "missing required column" in str(exc.value).lower()


def test_csv_negative_amount_flagged():
    raw = (
        "transaction_id,sender_account,receiver_account,"
        "amount,timestamp,transaction_type,channel,"
        "sender_location,receiver_location\n"
        "T1,A1,A2,-100,2026-01-01 10:00:00,"
        "transfer,bank,Mumbai,Delhi\n"
    )
    with pytest.raises(ingestion.ValidationError):
        # all rows invalid -> no valid records remain
        ingestion.parse_csv(raw.encode())


def test_csv_duplicate_ids_flagged():
    raw = (
        "transaction_id,sender_account,receiver_account,"
        "amount,timestamp,transaction_type,channel,"
        "sender_location,receiver_location\n"
        "T1,A1,A2,100,2026-01-01 10:00:00,"
        "transfer,bank,Mumbai,Delhi\n"
        "T1,A1,A2,200,2026-01-01 11:00:00,"
        "transfer,bank,Mumbai,Delhi\n"
    )
    df, report = ingestion.parse_csv(raw.encode())
    assert report["flagged_rows"] == 1
    assert report["flags"].get("duplicate_id") == 1


def test_csv_missing_timestamps_flagged():
    raw = (
        "transaction_id,sender_account,receiver_account,"
        "amount,timestamp,transaction_type,channel,"
        "sender_location,receiver_location\n"
        "T1,A1,A2,100,not-a-date,transfer,bank,"
        "Mumbai,Delhi\n"
    )
    with pytest.raises(ingestion.ValidationError):
        ingestion.parse_csv(raw.encode())


def test_csv_empty_file():
    with pytest.raises(ingestion.ValidationError):
        ingestion.parse_csv(b"")


def test_csv_valid_parse():
    raw = (
        "transaction_id,sender_account,receiver_account,"
        "amount,timestamp,transaction_type,channel,"
        "sender_location,receiver_location\n"
        "T1,A1,A2,100,2026-01-01 10:00:00,"
        "transfer,bank,Mumbai,Delhi\n"
        "T2,A2,A3,50,2026-01-01 10:05:00,"
        "transfer,bank,Delhi,Pune\n"
    )
    df, report = ingestion.parse_csv(raw.encode())
    assert report["valid_rows"] == 2
    assert report["flagged_rows"] == 0
    assert len(df) == 2


# ------------------------------------------------- feature extraction
def test_features_computed(demo_df):
    features = extract_features(demo_df)
    assert len(features) > 100
    hub = features[features["account_id"] == "AC381"].iloc[0]
    assert hub["tx_count"] >= 20
    assert hub["rapid_pass_pct"] >= 60
    assert hub["counterparties"] >= 8


def test_velocity_peak_hour(demo_df):
    features = extract_features(demo_df)
    hub = features[features["account_id"] == "AC381"].iloc[0]
    # hub does several tx within the same hour
    assert hub["velocity"] >= 3


# ------------------------------------------------------- risk engine
def test_risk_scores(demo_df):
    features = extract_features(demo_df)
    G = build_graph(demo_df)
    betweenness = compute_centrality(G)
    features, method = detect_anomalies(features)
    risks = score_accounts(features, betweenness, method)
    hub = risks[risks["account_id"] == "AC381"].iloc[0]
    assert hub["risk_score"] >= 70
    assert hub["risk_category"] == "high"
    # hub is the top scored account
    top = risks.nlargest(1, "risk_score").iloc[0]
    assert top["account_id"] == "AC381"


def test_risk_explainable_contributors(demo_df):
    features = extract_features(demo_df)
    G = build_graph(demo_df)
    betweenness = compute_centrality(G)
    features, method = detect_anomalies(features)
    risks = score_accounts(features, betweenness, method)
    hub = risks[risks["account_id"] == "AC381"].iloc[0]
    assert len(hub["contributors"]) >= 5
    # pass-through must be a top contributor
    contrib = dict(hub["contributors"])
    assert contrib.get("pass_through", 0) >= 10


def test_ml_method_reported(demo_df):
    features = extract_features(demo_df)
    features, method = detect_anomalies(features)
    assert method in ("Isolation Forest", "Analytical fallback")
    assert "ml_score" in features.columns


# ------------------------------------------------------ graph engine
def test_graph_built(demo_df):
    G = build_graph(demo_df)
    assert G.number_of_nodes() > 100
    assert G.number_of_edges() > 100


def test_centrality_identifies_hub(demo_df):
    G = build_graph(demo_df)
    betweenness = compute_centrality(G)
    # hub should have high betweenness relative to graph
    assert betweenness.get("AC381", 0) > 0


def test_shortest_path(demo_df):
    G = build_graph(demo_df)
    path = shortest_money_path(G, "AC9001", "AC381")
    assert path is not None
    assert path[0] == "AC9001"
    assert path[-1] == "AC381"
    assert len(path) - 1 <= 3


def test_shortest_path_no_path(demo_df):
    G = build_graph(demo_df)
    path = shortest_money_path(G, "AC9001", "ZZZ999")
    assert path is None


def test_neighbours(demo_df):
    G = build_graph(demo_df)
    n = neighbours(G, "AC381")
    assert len(n) >= 5
    assert "AC245" in n or "AC101" in n


def test_clusters_detected(demo_df):
    features = extract_features(demo_df)
    G = build_graph(demo_df)
    betweenness = compute_centrality(G)
    features, method = detect_anomalies(features)
    risks = score_accounts(features, betweenness, method)
    risk_map = dict(zip(risks["account_id"],
                        risks["risk_score"]))
    labels = detect_communities(G)
    clusters = __import__(
        "app.engine.graph_engine",
        fromlist=["suspicious_communities"]
    ).suspicious_communities(G, risk_map, labels, 70.0)
    assert len(clusters) >= 1
    hub_cluster = [c for c in clusters
                   if c["main_intermediary"] == "AC381"]
    assert len(hub_cluster) >= 1
    assert hub_cluster[0]["account_count"] >= 10


# -------------------------------------------------- trail engine
def test_trail_reconstruction(demo_df):
    G = build_graph(demo_df)
    result = trace_trail(demo_df, G, "AC9001")
    assert result["hops"] >= 4
    assert result["duration_minutes"] <= 30
    assert result["accounts_involved"] >= 5
    assert result["hops_detail"][0]["from_account"] == "AC9001"


def test_trail_targeted(demo_df):
    G = build_graph(demo_df)
    result = trace_trail(demo_df, G, "AC9001", "AC381")
    assert result["hops"] == 3
    assert result["hops_detail"][-1]["to_account"] == "AC381"


def test_trail_no_source(demo_df):
    G = build_graph(demo_df)
    result = trace_trail(demo_df, G, "ZZZ999")
    assert "error" in result
    assert result["hops"] == 0


def test_trail_disconnected(demo_df):
    # create an isolated account pair
    isolated = pd.DataFrame([{
        "transaction_id": "TX999999",
        "sender_account": "ISO-A",
        "receiver_account": "ISO-B",
        "amount": 100.0,
        "timestamp": "2026-02-01 12:00:00",
        "transaction_type": "transfer",
        "channel": "bank",
        "sender_location": "Mumbai",
        "receiver_location": "Delhi",
        "device_id": "", "ip_hash": "", "merchant_id": "",
        "cashout_location": "", "lat": 19.0, "lon": 72.8,
        "_ts": pd.Timestamp("2026-02-01 12:00:00"),
    }])
    combined = pd.concat([demo_df, isolated],
                           ignore_index=True)
    G = build_graph(combined)
    result = trace_trail(combined, G, "ISO-A", "AC381")
    assert "error" in result


def test_trail_temporal_contiguity(demo_df):
    G = build_graph(demo_df)
    result = trace_trail(demo_df, G, "AC9001")
    hops = result["hops_detail"]
    for i in range(1, len(hops)):
        t_prev = pd.Timestamp(hops[i - 1]["timestamp"])
        t_cur = pd.Timestamp(hops[i]["timestamp"])
        gap = (t_cur - t_prev).total_seconds() / 60.0
        assert gap <= 60, f"hop {i} gap {gap}min too large"


# -------------------------------------------------- alert engine
def test_alerts_generated(demo_df):
    features = extract_features(demo_df)
    G = build_graph(demo_df)
    betweenness = compute_centrality(G)
    features, method = detect_anomalies(features)
    risks = score_accounts(features, betweenness, method)
    alerts = generate_alerts(features, risks, demo_df)
    assert len(alerts) >= 1
    types = {a["alert_type"] for a in alerts}
    assert "rapid_multi_hop" in types


# -------------------------------------------------- pipeline / API
def test_pipeline_load(demo_df):
    report = load_dataset(demo_df, "test-pipeline", "test")
    assert report["status"] == "complete"
    assert report["transactions"] == len(demo_df)
    assert report["high_risk_accounts"] >= 1
    assert report["clusters"] >= 1


def test_api_dashboard(client, auth):
    r = client.get("/api/dashboard",
                   headers={"Authorization": f"Bearer {auth}"})
    assert r.status_code == 200
    data = r.json()
    assert data["loaded"] is True
    assert data["metrics"]["total_transactions"] > 0


def test_api_account_detail(client, auth):
    r = client.get("/api/accounts/AC381",
                   headers={"Authorization": f"Bearer {auth}"})
    assert r.status_code == 200
    data = r.json()
    assert data["risk"]["score"] >= 70
    assert len(data["reasons"]) >= 1


def test_api_account_not_found(client, auth):
    r = client.get("/api/accounts/ZZZ999",
                   headers={"Authorization": f"Bearer {auth}"})
    assert r.status_code == 404


def test_api_network_ego(client, auth):
    r = client.get("/api/network/AC381",
                   headers={"Authorization": f"Bearer {auth}"})
    assert r.status_code == 200
    data = r.json()
    assert len(data["nodes"]) >= 5


def test_api_trace(client, auth):
    r = client.post("/api/trails/trace",
                   json={"source": "AC9001"},
                   headers={"Authorization": f"Bearer {auth}"})
    assert r.status_code == 200
    data = r.json()
    assert data["hops"] >= 4
    assert data["trail_id"]


def test_api_trace_no_trail(client, auth):
    r = client.post("/api/trails/trace",
                   json={"source": "AC9001",
                         "destination": "ZZZ999"},
                   headers={"Authorization": f"Bearer {auth}"})
    assert r.status_code == 200
    assert r.json()["hops"] == 0


def test_api_priority_queue(client, auth):
    r = client.get("/api/priorities",
                   headers={"Authorization": f"Bearer {auth}"})
    assert r.status_code == 200
    queue = r.json()["queue"]
    assert len(queue) >= 1
    assert queue[0]["account_id"] == "AC381"


def test_api_investigation_lifecycle(client, auth):
    r = client.post("/api/investigations",
                   json={
                       "title": "Test mule investigation",
                       "priority": "high",
                       "accounts": ["AC381"],
                       "notes": "created in test",
                   },
                   headers={"Authorization": f"Bearer {auth}"})
    assert r.status_code == 200
    inv_id = r.json()["investigation_id"]

    r = client.get(f"/api/investigations/{inv_id}",
                   headers={"Authorization": f"Bearer {auth}"})
    assert r.status_code == 200
    assert r.json()["title"] == "Test mule investigation"

    r = client.patch(f"/api/investigations/{inv_id}",
                     json={"status": "escalated"},
                     headers={"Authorization": f"Bearer {auth}"})
    assert r.status_code == 200

    r = client.patch(f"/api/investigations/{inv_id}",
                     json={"status": "invalid_status"},
                     headers={"Authorization": f"Bearer {auth}"})
    assert r.status_code == 400


def test_api_false_positive_requires_reason(client, auth):
    r = client.patch(
        "/api/accounts/AC700/status?status=false_positive",
        headers={"Authorization": f"Bearer {auth}"})
    assert r.status_code == 400


def test_api_account_classification(client, auth):
    r = client.patch(
        "/api/accounts/AC700/status?status=needs_review"
        "&reason=reviewing",
        headers={"Authorization": f"Bearer {auth}"})
    assert r.status_code == 200


def test_api_audit_logged(client, admin_auth):
    r = client.get("/api/audit",
                   headers={
                       "Authorization": f"Bearer {admin_auth}"})
    assert r.status_code == 200
    assert r.json()["count"] >= 1
    actions = [e["action"] for e in r.json()["entries"]]
    assert any("dashboard" in a.lower() for a in actions)


def test_api_transactions_filter(client, auth):
    r = client.get(
        "/api/transactions?sender=AC9001",
        headers={"Authorization": f"Bearer {auth}"})
    assert r.status_code == 200
    data = r.json()
    assert data["total"] >= 1
    assert all(
        t["sender_account"] == "AC9001"
        for t in data["transactions"]
    )


def test_api_export_priority(client, auth):
    r = client.get("/api/export/priority-accounts",
                   headers={"Authorization": f"Bearer {auth}"})
    assert r.status_code == 200
    assert "account_id" in r.text


def test_api_csv_upload_invalid(client, analyst_auth):
    files = {
        "file": ("bad.csv",
                 io.BytesIO(b"a,b\n1,2\n"),
                 "text/csv"),
    }
    r = client.post("/api/data/upload", files=files,
                    headers={
                        "Authorization":
                            f"Bearer {analyst_auth}"})
    assert r.status_code == 422
    assert "missing required column" in r.json()["detail"].lower()


def test_api_csv_upload_valid(client, analyst_auth):
    rows = [
        "transaction_id,sender_account,receiver_account,"
        "amount,timestamp,transaction_type,channel,"
        "sender_location,receiver_location"
    ]
    for i in range(1, 40):
        rows.append(
            f"T{i},ACC{100 + i % 3},ACC{200 + i % 4},"
            f"{100 * i},2026-04-0{i % 9 + 1} "
            f"1{i % 10}:00:00,transfer,bank,Mumbai,Delhi"
        )
    files = {
        "file": ("good.csv",
                 io.BytesIO("\n".join(rows).encode()),
                 "text/csv"),
    }
    r = client.post("/api/data/upload", files=files,
                    headers={
                        "Authorization":
                            f"Bearer {analyst_auth}"})
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "complete"
    assert data["validation"]["valid_rows"] == 39
