"""Network explorer endpoints.

Serves graph data for the frontend visualisation, with filtering
and ego-network ('Investigation View') support.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.deps import get_current_user
from app.db.database import get_connection
from app.engine import graph_engine
from app.engine.pipeline import build_graph_cached
from app.security import audit

router = APIRouter(prefix="/api/network", tags=["network"])


@router.get("")
def network(
    high_risk_only: bool = Query(default=False),
    min_amount: float = Query(default=0.0),
    time_from: str | None = Query(default=None),
    time_to: str | None = Query(default=None),
    limit: int = Query(default=400, le=1500),
    user: dict = Depends(get_current_user),
):
    """Graph data (nodes + edges) for visualisation."""
    conn = get_connection()
    G = build_graph_cached()
    if G is None or G.number_of_nodes() == 0:
        raise HTTPException(
            404,
            "No transactions loaded. Upload a dataset or use the "
            "demonstration dataset.",
        )

    risk_rows = conn.execute(
        "SELECT account_id, risk_score, risk_category "
        "FROM risk_scores").fetchall()
    risk = {r["account_id"]: r["risk_score"] for r in risk_rows}
    category = {r["account_id"]: r["risk_category"]
                for r in risk_rows}

    # filter edges
    edges = []
    for u, v, d in G.edges(data=True):
        if min_amount and d["weight"] < min_amount:
            continue
        if time_from and d["first"] < time_from:
            continue
        if time_to and d["first"] > time_to:
            continue
        if high_risk_only and max(
                risk.get(u, 0), risk.get(v, 0)) < 70:
            continue
        edges.append((u, v, d))

    # prioritise edges touching high-risk accounts
    edges.sort(
        key=lambda e: -(
            risk.get(e[0], 0) + risk.get(e[1], 0) + e[2]["weight"]
        ))
    edges = edges[:limit]

    nodes: dict[str, dict] = {}
    for u, v, d in edges:
        for n in (u, v):
            if n not in nodes:
                nodes[n] = {
                    "id": n,
                    "label": n,
                    "risk_score": risk.get(n, 0.0),
                    "risk_category": category.get(n, "low"),
                    "degree": G.degree(n),
                }

    audit.log(user["investigator_id"],
              "Viewed network graph", action_type="view")

    return {
        "nodes": list(nodes.values()),
        "edges": [
            {"source": u, "target": v,
             "weight": d["weight"], "count": d["count"],
             "first": d["first"], "last": d["last"]}
            for u, v, d in edges
        ],
        "total_nodes": len(nodes),
        "total_edges": len(edges),
        "truncated": len(edges) == limit,
    }


@router.get("/{account_id}")
def ego_network(account_id: str,
                    depth: int = Query(default=1, le=2),
                    user: dict = Depends(get_current_user)):
    """Investigation View: account + direct neighbours + risk."""
    conn = get_connection()
    account_id = account_id.upper()
    G = build_graph_cached()
    if G is None or account_id not in G:
        raise HTTPException(404,
                            f"Account {account_id} not in graph.")

    neighbour_ids = graph_engine.neighbours(G, account_id, depth)

    risk_rows = conn.execute(
        "SELECT account_id, risk_score, risk_category "
        "FROM risk_scores").fetchall()
    risk = {r["account_id"]: r["risk_score"] for r in risk_rows}
    category = {r["account_id"]: r["risk_category"]
                for r in risk_rows}

    nodes = {}
    edges = []
    relevant = neighbour_ids | {account_id}
    for u, v, d in G.edges(data=True):
        if u in relevant and v in relevant:
            suspicious = (risk.get(u, 0) >= 70
                            or risk.get(v, 0) >= 70)
            edges.append({
                "source": u, "target": v,
                "weight": d["weight"], "count": d["count"],
                "first": d["first"], "last": d["last"],
                "suspicious": suspicious,
            })
            for n in (u, v):
                if n not in nodes:
                    nodes[n] = {
                        "id": n, "label": n,
                        "risk_score": risk.get(n, 0.0),
                        "risk_category": category.get(n, "low"),
                        "degree": G.degree(n),
                        "is_centre": n == account_id,
                    }

    # suspicious neighbours (for highlight)
    suspicious_neighbours = [
        n for n in neighbour_ids if risk.get(n, 0) >= 70
    ]

    audit.log(user["investigator_id"],
              f"Viewed ego-network for {account_id}",
              entity_type="account", entity_id=account_id,
              action_type="view")

    return {
        "centre": account_id,
        "nodes": list(nodes.values()),
        "edges": edges,
        "suspicious_neighbours": suspicious_neighbours,
        "neighbour_count": len(neighbour_ids),
    }


@router.get("/{account_id}/paths")
def money_paths(account_id: str,
                    target: str | None = Query(default=None),
                    user: dict = Depends(get_current_user)):
    """Shortest money path between two accounts."""
    conn = get_connection()
    account_id = account_id.upper()
    G = build_graph_cached()
    if G is None or account_id not in G:
        raise HTTPException(404, "Account not in graph.")
    if not target:
        raise HTTPException(400, "target parameter required.")
    target = target.upper()
    if target not in G:
        raise HTTPException(404, "Target account not in graph.")

    path = graph_engine.shortest_money_path(G, account_id, target)
    if not path:
        return {
            "source": account_id, "target": target,
            "path": None,
            "message": "No connected path found within "
                        "the hop limit.",
        }
    return {
        "source": account_id, "target": target,
        "path": path, "hops": len(path) - 1,
    }
