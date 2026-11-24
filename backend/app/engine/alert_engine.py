"""Pattern alert engine.

Generates investigator-readable alerts for the fraud typologies
defined in PS-35: rapid pass-through, high connectivity, bursts,
structuring/splitting, rapid multi-hop, convergence and divergence.
"""
from __future__ import annotations

import pandas as pd

from app.config import MULTI_HOP_MAX_MINUTES, RAPID_PASS_MINUTES


def generate_alerts(features: pd.DataFrame,
                    risks: pd.DataFrame,
                    df: pd.DataFrame) -> list[dict]:
    alerts: list[dict] = []
    risk_by_account = dict(zip(risks["account_id"], risks["risk_score"]))
    feat = features.set_index("account_id")

    for _, row in features.iterrows():
        account = row["account_id"]
        risk = risk_by_account.get(account, 0.0)
        if risk < 40:
            continue  # only alert on medium+ risk accounts

        # Rapid pass-through
        if row["rapid_count"] >= 3 and row["rapid_pass_pct"] >= 60:
            alerts.append(_alert(
                "rapid_pass_through", account, risk,
                f"Rapid pass-through — {int(row['rapid_pass_pct'])}% of funds "
                f"forwarded within {RAPID_PASS_MINUTES} minutes",
                f"Account {account} received funds and forwarded "
                f"{int(row['rapid_pass_pct'])}% of the received value onward "
                f"within {RAPID_PASS_MINUTES} minutes on {int(row['rapid_count'])} "
                f"occasions. Funds did not rest in the account.",
                "Review incoming counterparties and forward destinations; "
                "trace the earliest large transfer.",
            ))

        # High connectivity
        if row["counterparties"] >= 10:
            alerts.append(_alert(
                "high_connectivity", account, risk,
                f"High connectivity — {int(row['counterparties'])} counterparties",
                f"Account {account} interacted with {int(row['counterparties'])} "
                f"unique counterparties, far beyond typical retail activity.",
                "Check whether counterparties share timing or amount patterns.",
            ))

        # Transaction burst
        if row["burst_score"] >= 0.6:
            alerts.append(_alert(
                "transaction_burst", account, risk,
                "Transaction burst — sudden activity spike",
                f"Account {account} shows a sudden burst of activity well above "
                f"its baseline transaction rate.",
                "Review the burst window for a coordinated transfer sequence.",
            ))

        # Divergence (structuring/splitting)
        div = _divergence_events(df, account)
        if div:
            for event in div[:2]:
                alerts.append(_alert(
                    "suspicious_divergence", account, risk,
                    f"Structuring/splitting — ₹{event['amount']:,.0f} split "
                    f"across {event['count']} accounts",
                    f"On {event['timestamp']}, account {account} split "
                    f"₹{event['amount']:,.0f} across {event['count']} different "
                    f"accounts within minutes — a structuring/splitting pattern.",
                    "Trace each downstream account; look for convergence at "
                    "cash-out points.",
                    occurred_at=event["timestamp"],
                    amount=event["amount"],
                ))

    # Rapid multi-hop and convergence across the whole dataset
    alerts.extend(_multi_hop_alerts(df, risk_by_account))
    alerts.extend(_convergence_alerts(df, risk_by_account, feat))

    # de-duplicate by type+account
    seen = set()
    unique = []
    for a in alerts:
        key = (a["alert_type"], a["entity_ids"][0])
        if key not in seen:
            seen.add(key)
            unique.append(a)
    return sorted(unique, key=lambda a: -(a["risk_score"] or 0))


def _alert(alert_type, account, risk, title, description,
           recommended_action, occurred_at=None, amount=None) -> dict:
    severity = "high" if risk >= 70 else "medium"
    return {
        "alert_type": alert_type,
        "title": title,
        "description": description,
        "entity_ids": [account],
        "account_ids": account,
        "amount": amount,
        "occurred_at": occurred_at,
        "risk_score": risk,
        "severity": severity,
        "recommended_action": recommended_action,
    }


def _divergence_events(df: pd.DataFrame, account: str) -> list[dict]:
    """One incoming followed by split to many accounts within minutes."""
    out = df[df["sender_account"] == account].sort_values("_ts")
    events = []
    for _, first_out in out.iterrows():
        t0 = first_out["_ts"]
        window = out[(out["_ts"] > t0) &
                     (out["_ts"] <= t0 + pd.Timedelta(minutes=10))]
        if len(window) >= 3 and window["receiver_account"].nunique() >= 3:
            events.append({
                "timestamp": pd.Timestamp(t0).strftime("%Y-%m-%d %H:%M"),
                "amount": float(first_out["amount"] + window["amount"].sum()),
                "count": int(window["receiver_account"].nunique()),
            })
    return events


def _multi_hop_alerts(df: pd.DataFrame, risk_by_account) -> list[dict]:
    """Find 3+ hop chains completed within MULTI_HOP_MAX_MINUTES."""
    alerts = []
    by_sender: dict[str, list] = {}
    for _, row in df.sort_values("_ts").iterrows():
        by_sender.setdefault(row["sender_account"], []).append(row)

    chains = set()
    for _, row in df.iterrows():
        chain = _follow_chain(by_sender, row, MULTI_HOP_MAX_MINUTES)
        if chain and len(chain) >= 3:
            key = tuple((h["sender_account"], h["receiver_account"])
                        for h in chain)
            if key not in chains:
                chains.add(key)
                amounts = [h["amount"] for h in chain]
                t0, t1 = chain[0]["_ts"], chain[-1]["_ts"]
                duration = (t1 - t0).total_seconds() / 60.0
                alerts.append({
                    "alert_type": "rapid_multi_hop",
                    "title": (f"Rapid multi-hop — {len(chain)} accounts in "
                              f"{int(duration)} minutes"),
                    "description": (
                        f"Money moved through {len(chain)} transfers "
                        f"({chain[0]['sender_account']} → "
                        f"{' → '.join(h['receiver_account'] for h in chain)}) "
                        f"within {int(duration)} minutes. Individually each "
                        f"transfer looks ordinary; connected together they form "
                        f"a rapid multi-hop money trail."),
                    "entity_ids": list(dict.fromkeys(
                        [chain[0]["sender_account"]] +
                        [h["receiver_account"] for h in chain])),
                    "account_ids": ", ".join(dict.fromkeys(
                        [chain[0]["sender_account"]] +
                        [h["receiver_account"] for h in chain])),
                    "amount": float(sum(amounts)),
                    "occurred_at": pd.Timestamp(t0).strftime("%Y-%m-%d %H:%M:%S"),
                    "risk_score": max(
                        risk_by_account.get(h["receiver_account"], 0.0)
                        for h in chain),
                    "severity": "high",
                    "recommended_action": "Run a full money trail trace on "
                                          "this chain.",
                })
    return alerts[:20]


def _follow_chain(by_sender, first_row, max_minutes):
    chain = [first_row]
    current = first_row["receiver_account"]
    t0 = first_row["_ts"]
    for _ in range(8):
        nxt = [r for r in by_sender.get(current, [])
               if r["_ts"] > chain[-1]["_ts"] and
               (r["_ts"] - t0).total_seconds() / 60.0 <= max_minutes]
        if not nxt:
            break
        chain.append(max(nxt, key=lambda r: r["amount"]))
        current = chain[-1]["receiver_account"]
    return chain if len(chain) >= 2 else None


def _convergence_alerts(df, risk_by_account, feat) -> list[dict]:
    """Multiple distinct accounts sending into one intermediary."""
    alerts = []
    for receiver, grp in df.groupby("receiver_account"):
        senders = grp["sender_account"].nunique()
        if senders >= 5:
            f = feat.loc[receiver] if receiver in feat.index else None
            rapid = float(f["rapid_pass_pct"]) if f is not None else 0.0
            if rapid >= 40:
                alerts.append({
                    "alert_type": "suspicious_convergence",
                    "title": (f"Suspicious convergence — {senders} accounts "
                              f"feeding {receiver}"),
                    "description": (
                        f"{senders} distinct accounts sent funds into "
                        f"intermediary {receiver}, which then forwarded "
                        f"{int(rapid)}% of received value onward rapidly."),
                    "entity_ids": [receiver],
                    "account_ids": receiver,
                    "amount": float(grp["amount"].sum()),
                    "occurred_at": None,
                    "risk_score": risk_by_account.get(receiver, 0.0),
                    "severity": "high" if risk_by_account.get(receiver, 0) >= 70 else "medium",
                    "recommended_action": "Investigate the intermediary's "
                                          "upstream network.",
                })
    return alerts[:10]
