"""Temporal money-trail reconstruction.

Reconstructs chronological paths through the transaction graph,
respecting time order: money can only move forward in time.
Each hop records WHO / WHEN / HOW MUCH / FROM / TO so the
investigator can explain the trail in plain language.
"""
from __future__ import annotations

from datetime import timedelta

import networkx as nx
import pandas as pd

MAX_TRAIL_HOPS = 10


def trace_trail(df: pd.DataFrame, G: nx.DiGraph,
                source: str, destination: str | None = None,
                amount_hint: float | None = None,
                max_hops: int = MAX_TRAIL_HOPS,
                max_minutes: int | None = None) -> dict:
    """Reconstruct a money trail from source toward destination.

    Time-respecting search: every hop must occur after the previous one.
    When destination is None, walks downstream following the largest
    amounts until a terminal account (low out-degree) is reached.
    """
    tx = df.copy()
    tx["_ts"] = pd.to_datetime(tx["_ts"])
    tx = tx.sort_values("_ts")

    if source not in G:
        return _no_trail(source, destination or "—", "Source account not present in dataset.")
    if destination and destination not in G:
        return _no_trail(source, destination, "Destination account not present in dataset.")

    if destination:
        path = _find_time_path(tx, source, destination, amount_hint,
                               max_hops, max_minutes)
        if path is None:
            return _no_trail(
                source, destination,
                "No connected money trail found within the selected constraints. "
                "Try widening the time window or increasing allowed hops.")
        hops = path
        terminal = destination
    else:
        hops, terminal = _walk_downstream(tx, source, amount_hint, max_hops, max_minutes)
        if not hops:
            return _no_trail(source, "—", "No onward movement found from this account.")

    return _assemble(source, terminal, hops, df)


def _find_time_path(tx: pd.DataFrame, source: str, destination: str,
                    amount_hint, max_hops: int, max_minutes: int | None,
                    hop_gap_minutes: int = 30):
    """DFS over time-ordered edges, preferring large amounts.

    Each hop must occur shortly after the previous one
    (money does not rest in mule accounts).
    """
    by_sender: dict[str, pd.DataFrame] = {
        s: g.sort_values("_ts") for s, g in tx.groupby("sender_account")
    }
    best: list[dict] | None = None

    def dfs(current, started, path, remaining):
        nonlocal best
        if best is not None and len(path) >= len(best):
            return
        if current == destination and path:
            best = list(path)
            return
        if remaining <= 0:
            return
        grp = by_sender.get(current)
        if grp is None:
            return
        last_ts = started if not path else path[-1]["timestamp"]
        candidates = grp[grp["_ts"] >= last_ts]
        # hops must be temporally contiguous
        gap_cutoff = pd.Timestamp(last_ts) + timedelta(
            minutes=hop_gap_minutes)
        candidates = candidates[candidates["_ts"] <= gap_cutoff]
        if max_minutes is not None:
            cutoff = (pd.Timestamp(started) + timedelta(minutes=max_minutes))
            candidates = candidates[candidates["_ts"] <= cutoff]
        # prefer larger amounts, then earlier
        candidates = candidates.sort_values(["amount", "_ts"],
                                            ascending=[False, True])
        for _, edge in candidates.iterrows():
            nxt = edge["receiver_account"]
            if nxt in [h["to"] for h in path]:
                continue  # avoid cycles
            path.append({
                "from": current, "to": nxt,
                "amount": float(edge["amount"]),
                "timestamp": edge["_ts"],
                "transaction_id": edge["transaction_id"],
            })
            dfs(nxt, started, path, remaining - 1)
            path.pop()

    start_times = tx[tx["sender_account"] == source]["_ts"].sort_values()
    for t0 in start_times.head(50):
        dfs(source, t0, [], max_hops)
        if best:
            break
    return best


def _walk_downstream(tx: pd.DataFrame, source: str, amount_hint,
                     max_hops: int, max_minutes: int | None):
    """Follow the money greedily from source to a terminal account."""
    by_sender: dict[str, pd.DataFrame] = {
        s: g.sort_values("_ts") for s, g in tx.groupby("sender_account")
    }
    hops: list[dict] = []
    current = source
    started = None
    remaining_amount = amount_hint

    for _ in range(max_hops):
        grp = by_sender.get(current)
        if grp is None or grp.empty:
            break
        if started is not None:
            grp = grp[grp["_ts"] >= started]
            # hops must be temporally contiguous
            last_ts = hops[-1]["timestamp"] if hops else started
            grp = grp[grp["_ts"] <= pd.Timestamp(last_ts)
                        + timedelta(minutes=30)]
            if max_minutes is not None:
                cutoff = pd.Timestamp(started) + timedelta(minutes=max_minutes)
                grp = grp[grp["_ts"] <= cutoff]
        if grp.empty:
            break
        edge = grp.sort_values(["amount", "_ts"], ascending=[False, True]).iloc[0]
        if started is None:
            started = edge["_ts"]
        hops.append({
            "from": current, "to": edge["receiver_account"],
            "amount": float(edge["amount"]),
            "timestamp": edge["_ts"],
            "transaction_id": edge["transaction_id"],
        })
        if remaining_amount is not None:
            remaining_amount = float(edge["amount"])
        current = edge["receiver_account"]

    terminal = current
    return hops, terminal


def _assemble(source: str, terminal: str, hops: list[dict],
              df: pd.DataFrame) -> dict:
    """Build the trail record with summary and plain-language explanation."""
    trail_hops = []
    for i, hop in enumerate(hops):
        trail_hops.append({
            "hop_index": i + 1,
            "from_account": hop["from"],
            "to_account": hop["to"],
            "amount": round(hop["amount"], 2),
            "timestamp": pd.Timestamp(hop["timestamp"]).strftime("%Y-%m-%d %H:%M:%S"),
            "transaction_id": hop["transaction_id"],
        })

    starting = trail_hops[0]["amount"] if trail_hops else 0.0
    tracked = trail_hops[-1]["amount"] if trail_hops else 0.0
    t0 = pd.Timestamp(trail_hops[0]["timestamp"])
    t1 = pd.Timestamp(trail_hops[-1]["timestamp"])
    duration = max((t1 - t0).total_seconds() / 60.0, 0.0)

    accounts = [source] + [h["to_account"] for h in trail_hops]
    passed_pct = (100.0 * tracked / starting) if starting > 0 else 0.0
    branching = sum(1 for h in trail_hops
                    if _out_degree(df, h["from_account"], after=h["timestamp"]) > 1)

    if duration <= 30 and len(trail_hops) >= 3:
        summary = (f"Rapid multi-hop movement: money moved through "
                   f"{len(trail_hops)} transfer(s) across {len(set(accounts))} accounts "
                   f"in {int(duration)} minutes, with {passed_pct:.0f}% of received "
                   f"value forwarded downstream.")
    elif passed_pct >= 90:
        summary = (f"Near-complete pass-through: {passed_pct:.0f}% of value moved "
                   f"from {source} to {terminal} across {len(trail_hops)} hop(s).")
    else:
        summary = (f"Money trail reconstructed: {len(trail_hops)} hop(s), "
                   f"{passed_pct:.0f}% of starting value tracked to {terminal}.")

    return {
        "trail_id": None,  # assigned by caller when persisted
        "source_account": source,
        "terminal_account": terminal,
        "starting_amount": round(starting, 2),
        "tracked_amount": round(tracked, 2),
        "hops": len(trail_hops),
        "duration_minutes": round(duration, 1),
        "accounts_involved": len(set(accounts)),
        "accounts": list(dict.fromkeys(accounts)),
        "amount_difference": round(starting - tracked, 2),
        "passed_forward_pct": round(passed_pct, 1),
        "branching_hops": branching,
        "hops_detail": trail_hops,
        "summary": summary,
        "created_at": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


def _out_degree(df: pd.DataFrame, account: str, after) -> int:
    sub = df[(df["sender_account"] == account) & (df["_ts"] >= after)]
    return int(sub["receiver_account"].nunique())


def _no_trail(source: str, destination: str, reason: str) -> dict:
    return {
        "trail_id": None,
        "source_account": source,
        "terminal_account": destination,
        "starting_amount": 0.0,
        "tracked_amount": 0.0,
        "hops": 0,
        "duration_minutes": 0.0,
        "accounts_involved": 0,
        "accounts": [],
        "amount_difference": 0.0,
        "passed_forward_pct": 0.0,
        "branching_hops": 0,
        "hops_detail": [],
        "summary": reason,
        "error": reason,
        "created_at": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
