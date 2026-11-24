"""Graph engine built on NetworkX.

Accounts are nodes, transactions are (aggregated) edges. Provides centrality,
community detection, shortest money paths and cluster summaries.
"""
from __future__ import annotations

import networkx as nx
import pandas as pd


def build_graph(df: pd.DataFrame) -> nx.DiGraph:
    """Construct a directed transaction graph.

    Parallel transactions between the same pair are aggregated into a single
    edge carrying total amount, count, first/last timestamp and hop-level detail.
    """
    G = nx.DiGraph()
    grouped = df.groupby(["sender_account", "receiver_account"], sort=False)
    for (sender, receiver), grp in grouped:
        times = pd.to_datetime(grp["_ts"]).sort_values()
        if not G.has_node(sender):
            G.add_node(sender)
        if not G.has_node(receiver):
            G.add_node(receiver)
        G.add_edge(
            sender, receiver,
            weight=float(grp["amount"].sum()),
            count=int(len(grp)),
            first=str(times.min()),
            last=str(times.max()),
            tx_ids=";".join(grp["transaction_id"].tolist()),
        )
    return G


def compute_centrality(G: nx.DiGraph) -> dict[str, float]:
    """Betweenness centrality — identifies intermediary/connector accounts."""
    if len(G) < 3:
        return {n: 0.0 for n in G.nodes}
    try:
        return {k: float(v) for k, v in nx.betweenness_centrality(G).items()}
    except Exception:
        return {n: 0.0 for n in G.nodes}


def detect_communities(G: nx.DiGraph) -> dict[str, int]:
    """Community detection on the undirected projection of the graph."""
    undirected = G.to_undirected()
    if undirected.number_of_nodes() < 3:
        return {n: 0 for n in undirected.nodes}
    try:
        communities = nx.community.louvain_communities(undirected, seed=42, resolution=1.0)
    except Exception:
        communities = [set(undirected.nodes)]
    labels: dict[str, int] = {}
    for idx, community in enumerate(sorted(communities, key=len, reverse=True)):
        for node in community:
            labels[node] = idx
    return labels


def suspicious_communities(G: nx.DiGraph, risk: dict[str, float],
                           labels: dict[str, int],
                           high_threshold: float) -> list[dict]:
    """Summarise communities that contain meaningful high-risk structure."""
    from collections import defaultdict
    members: dict[int, list[str]] = defaultdict(list)
    for node, label in labels.items():
        members[label].append(node)

    results = []
    seq = 0
    for label, nodes in sorted(members.items(), key=lambda kv: -len(kv[1])):
        if len(nodes) < 3:
            continue
        subgraph = G.subgraph(nodes)
        total_amount = sum(d["weight"] for _, _, d in subgraph.edges(data=True))
        risks = [risk.get(n, 0.0) for n in nodes]
        high_count = sum(1 for r in risks if r >= high_threshold)
        if high_count == 0:
            continue
        seq += 1
        # main intermediary = highest betweenness within cluster
        between = {n: subgraph.degree(n) for n in nodes}
        main_intermediary = max(nodes, key=lambda n: (risk.get(n, 0.0), between[n]))
        avg_risk = sum(risks) / len(risks)
        # dominant pattern
        internal = subgraph.number_of_edges()
        density = internal / max(nodes.__len__() * (nodes.__len__() - 1), 1)
        pattern = _cluster_pattern(subgraph, nodes, risk, high_threshold)
        results.append({
            "cluster_label": f"CLUSTER-{seq:02d}",
            "account_count": len(nodes),
            "high_risk_accounts": high_count,
            "avg_risk": round(avg_risk, 1),
            "total_amount": round(total_amount, 2),
            "main_intermediary": main_intermediary,
            "primary_pattern": pattern,
            "density": round(density, 3),
            "accounts": sorted(nodes, key=lambda n: -risk.get(n, 0.0)),
        })
    return sorted(results, key=lambda c: (-c["avg_risk"], -c["account_count"]))


def _cluster_pattern(subgraph, nodes, risk, high_threshold) -> str:
    """Human-readable description of the cluster's dominant behaviour."""
    high = [n for n in nodes if risk.get(n, 0.0) >= high_threshold]
    in_deg = dict(subgraph.in_degree())
    out_deg = dict(subgraph.out_degree())
    hub = max(high or nodes, key=lambda n: in_deg.get(n, 0) + out_deg.get(n, 0))
    if out_deg.get(hub, 0) >= 3 and in_deg.get(hub, 0) >= 2:
        return "Rapid multi-hop convergence and divergence (hub-and-spoke)"
    if out_deg.get(hub, 0) >= 3:
        return "Rapid divergence — funds split to many accounts"
    if in_deg.get(hub, 0) >= 3:
        return "Convergence — many accounts feeding one intermediary"
    return "Layered multi-hop movement"


def shortest_money_path(G: nx.DiGraph, source: str, target: str,
                        max_hops: int = 8) -> list[str] | None:
    """Shortest directed path (fewest hops) between two accounts."""
    try:
        path = nx.shortest_path(G, source=source, target=target)
        return path if len(path) - 1 <= max_hops else None
    except nx.NetworkXNoPath:
        return None
    except nx.NodeNotFound:
        return None


def neighbours(G: nx.DiGraph, account: str, depth: int = 1) -> set[str]:
    """Direct (depth=1) neighbourhood of an account."""
    seen = {account}
    frontier = {account}
    for _ in range(depth):
        nxt = set()
        for node in frontier:
            if node in G:
                nxt |= set(G.successors(node)) | set(G.predecessors(node))
        frontier = nxt - seen
        seen |= frontier
    seen.discard(account)
    return seen
