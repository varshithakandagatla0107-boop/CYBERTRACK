"""Synthetic demonstration case generator.

Builds a deliberate, chronologically coherent fraud scenario embedded in
realistic legitimate activity:

    Victim → AC101 → AC245 → AC381 ↙ AC427 → CASH-OUT
                                ↘ AC522 → CASH-OUT
                                ↘ AC610

...plus several parallel chains feeding the same hub, a secondary hub,
and ~900 ordinary accounts providing legitimate background traffic.

All data is synthetic. Coordinates are synthetic demonstration locations.
"""
from __future__ import annotations

import random
from datetime import datetime, timedelta

import pandas as pd

# ---------------------------------------------------------------- scenario

HUB = "AC381"          # primary mule hub
HUB2 = "AC382"         # secondary hub
FIRST_HOPS = ["AC101", "AC102", "AC103"]
SECOND_HOPS = ["AC245", "AC246", "AC247"]
CASHOUT_MULES = ["AC427", "AC522", "AC610", "AC428", "AC523"]
CASHOUT_NODES = ["CO-01", "CO-02", "CO-03"]

CITIES = [
    ("Mumbai", 19.0760, 72.8777), ("Delhi", 28.7041, 77.1025),
    ("Bengaluru", 12.9716, 77.5946), ("Chennai", 13.0827, 80.2707),
    ("Kolkata", 22.5726, 88.3639), ("Hyderabad", 17.3850, 78.4867),
    ("Pune", 18.5204, 73.8567), ("Jaipur", 26.9124, 75.7873),
    ("Lucknow", 26.8467, 80.9462), ("Patna", 25.5941, 85.1376),
]

CHANNELS = ["bank_transfer", "upi", "wallet", "neft", "imps"]
TYPES = ["transfer", "payment", "p2p", "merchant"]


def generate_demo_case(seed: int = 42) -> pd.DataFrame:
    random.seed(seed)
    rows: list[dict] = []
    base_date = datetime(2026, 2, 1, 8, 0, 0)

    tx_seq = 0

    def add(sender, receiver, amount, when, *, tx_type=None, channel=None,
            sender_loc=None, receiver_loc=None, cashout=None,
            lat=None, lon=None, device=None, ip=None, merchant=None):
        nonlocal tx_seq
        tx_seq += 1
        scity, slat, slon = sender_loc or random.choice(CITIES)
        rcity, rlat, rlon = receiver_loc or random.choice(CITIES)
        rows.append({
            "transaction_id": f"TX{tx_seq:06d}",
            "sender_account": sender,
            "receiver_account": receiver,
            "amount": round(float(amount), 2),
            "timestamp": when.strftime("%Y-%m-%d %H:%M:%S"),
            "transaction_type": tx_type or random.choice(TYPES),
            "channel": channel or random.choice(CHANNELS),
            "sender_location": scity,
            "receiver_location": rcity,
            "device_id": device or f"DEV-{random.randint(10000, 99999)}",
            "ip_hash": ip or f"{random.getrandbits(32):08x}",
            "merchant_id": merchant or "",
            "cashout_location": cashout or "",
            "lat": lat if lat is not None else rlat,
            "lon": lon if lon is not None else rlon,
        })

    # ---------------------------------------------------------- fraud chains
    # Six victims across ten days, all funnelled into the hub network.
    chains = [
        # (day_offset, victim, first, second, amount)
        (0, "AC9001", "AC101", "AC245", 50000),
        (1, "AC9002", "AC102", "AC246", 75000),
        (2, "AC9003", "AC103", "AC247", 62000),
        (4, "AC9004", "AC101", "AC245", 43000),
        (6, "AC9005", "AC102", "AC246", 88000),
        (8, "AC9006", "AC103", "AC247", 54000),
        (9, "AC9007", "AC101", "AC245", 39000),
    ]
    victim_city = ("Mumbai", 19.0760, 72.8777)

    for day, victim, first, second, amount in chains:
        t0 = base_date + timedelta(days=day, hours=2, minutes=42)
        fee = 0.96  # each hop retains ~96% of value

        # victim -> first hop (the fraudulent inflow)
        add(victim, first, amount, t0, tx_type="transfer",
            channel="imps", sender_loc=victim_city,
            receiver_loc=("Pune", 18.5204, 73.8567))

        # first -> second (2 minutes later)
        amt1 = round(amount * fee, 2)
        add(first, second, amt1, t0 + timedelta(minutes=2),
            tx_type="transfer", channel="imps")

        # second -> hub (2 minutes later)
        amt2 = round(amt1 * fee, 2)
        add(second, HUB, amt2, t0 + timedelta(minutes=4),
            tx_type="transfer", channel="imps")

        # hub branches to cashout mules (1-2 minutes later)
        part_a = round(amt2 * 0.47, 2)
        part_b = round(amt2 * 0.47, 2)
        part_c = round(amt2 - part_a - part_b, 2)
        mule_a, mule_b = random.sample(CASHOUT_MULES, 2)
        add(HUB, mule_a, part_a, t0 + timedelta(minutes=6),
            tx_type="transfer", channel="upi")
        add(HUB, mule_b, part_b, t0 + timedelta(minutes=6, seconds=40),
            tx_type="transfer", channel="upi")
        if part_c > 100:
            add(HUB, "AC610", part_c, t0 + timedelta(minutes=7),
                tx_type="transfer", channel="upi")

        # cashout mules -> cash-out nodes (ATM/merchant) minutes later
        co = random.choice(CASHOUT_NODES)
        co_city = random.choice(CITIES)
        add(mule_a, co, part_a * 0.98, t0 + timedelta(minutes=10),
            tx_type="atm_withdrawal", channel="atm",
            receiver_loc=co_city, cashout=f"ATM/{co_city[0]}")
        add(mule_b, random.choice(CASHOUT_NODES), part_b * 0.98,
            t0 + timedelta(minutes=11),
            tx_type="merchant_payment", channel="pos",
            receiver_loc=co_city, cashout=f"POS/{co_city[0]}")

    # secondary hub chain (medium-risk network)
    for day, victim in [(3, "AC9011"), (7, "AC9012")]:
        t0 = base_date + timedelta(days=day, hours=15, minutes=10)
        amount = 35000
        add(victim, "AC150", amount, t0, tx_type="transfer",
            channel="neft", sender_loc=("Delhi", 28.7041, 77.1025))
        add("AC150", "AC260", round(amount * 0.95, 2),
            t0 + timedelta(minutes=8), tx_type="transfer", channel="neft")
        add("AC260", HUB2, round(amount * 0.9, 2),
            t0 + timedelta(minutes=17), tx_type="transfer", channel="neft")
        add(HUB2, "AC530", round(amount * 0.85, 2),
            t0 + timedelta(minutes=19), tx_type="transfer", channel="upi")
        add("AC530", "CO-03", round(amount * 0.83, 2),
            t0 + timedelta(minutes=26), tx_type="merchant_payment",
            channel="pos", receiver_loc=("Jaipur", 26.9124, 75.7873),
            cashout="POS/Jaipur")

    # legitimate-looking noise inside the hub neighbourhood
    # (ordinary accounts transacting with the hub occasionally)
    for i, ordinary in enumerate(["AC700", "AC701", "AC702", "AC703"]):
        t0 = base_date + timedelta(days=5 + i, hours=11)
        add(ordinary, HUB, random.randint(2000, 9000), t0,
            tx_type="payment", channel="upi")

    # ------------------------------------------------- legitimate background
    # ~900 ordinary accounts, 1-6 transactions each: salaries, merchants,
    # utilities, P2P — the "normal" traffic the fraud hides within.
    ordinary_accounts = [f"AC{random.randint(1000, 9999):04d}"
                         for _ in range(900)]
    companies = [f"CO-PAY-{i:03d}" for i in range(12)]

    n_legit = 0
    for account in ordinary_accounts:
        for _ in range(random.randint(1, 6)):
            n_legit += 1
            t0 = (base_date + timedelta(days=random.randint(0, 12),
                                        hours=random.randint(7, 22),
                                        minutes=random.randint(0, 59)))
            kind = random.random()
            if kind < 0.3:      # salary / payout from a company
                add(random.choice(companies), account,
                    random.randint(8000, 65000), t0, tx_type="salary",
                    channel="neft")
            elif kind < 0.55:   # merchant purchase
                merchant = f"M-{random.randint(100, 999)}"
                add(account, merchant, random.randint(150, 8000), t0,
                    tx_type="merchant", channel="pos",
                    merchant=merchant)
            elif kind < 0.8:    # P2P transfer between ordinary accounts
                other = random.choice(ordinary_accounts)
                if other != account:
                    add(account, other, random.randint(100, 25000), t0,
                        tx_type="p2p", channel="upi")
            else:               # utility / bill
                add(account, "UTILITY-BILL", random.randint(200, 6000), t0,
                    tx_type="bill_payment", channel="bank_transfer")

    df = pd.DataFrame(rows)
    df["_ts"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values("_ts").reset_index(drop=True)
    return df


def case_metadata() -> dict:
    return {
        "name": "Demonstration Case — Mule Network PS35-DEMO-01",
        "description": (
            "Synthetic fraud scenario: stolen funds move from victims through "
            "collector accounts (AC101-103) to a hub (AC381), then branch to "
            "cash-out mules and cash-out points. Embedded in ~900 ordinary "
            "accounts of legitimate activity."),
        "created": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
