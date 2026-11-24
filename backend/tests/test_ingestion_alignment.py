"""Regression tests for CSV amount alignment fix.

The bug: after sorting by timestamp and resetting index, the amount values
were misaligned because the `amount` Series kept the original DataFrame index
while `valid` DataFrame was reset with `reset_index(drop=True)`.

These tests ensure the fix works correctly.
"""
from __future__ import annotations

import pandas as pd
import pytest

from app.engine import ingestion


def test_amount_alignment_out_of_order_timestamps():
    """Test that amounts stay with their rows when timestamps are out of order."""
    # CSV with amounts 500, 100, 900 but timestamps out of order
    # Row 1: 500 at 10:02
    # Row 2: 100 at 10:01  (earliest)
    # Row 3: 900 at 10:03
    raw = (
        "transaction_id,sender_account,receiver_account,"
        "amount,timestamp,transaction_type,channel,"
        "sender_location,receiver_location\n"
        "T1,A1,A2,500,2026-01-01 10:02:00,transfer,bank,Mumbai,Delhi\n"
        "T2,A2,A3,100,2026-01-01 10:01:00,transfer,bank,Delhi,Pune\n"
        "T3,A3,A4,900,2026-01-01 10:03:00,transfer,bank,Pune,Chennai\n"
    )
    df, report = ingestion.parse_csv(raw.encode())
    assert report["valid_rows"] == 3
    # After sorting by timestamp, order should be T2(100), T1(500), T3(900)
    assert df.iloc[0]["transaction_id"] == "T2"
    assert df.iloc[0]["amount"] == 100.0
    assert df.iloc[1]["transaction_id"] == "T1"
    assert df.iloc[1]["amount"] == 500.0
    assert df.iloc[2]["transaction_id"] == "T3"
    assert df.iloc[2]["amount"] == 900.0


def test_amount_alignment_mixed_valid_rejected():
    """Test that amounts stay aligned when valid and rejected rows are interleaved."""
    # Row 1: valid (amount 500)
    # Row 2: invalid amount (-100) -> rejected
    # Row 3: valid (amount 900)
    # Row 4: invalid timestamp -> rejected
    # Row 5: valid (amount 200)
    raw = (
        "transaction_id,sender_account,receiver_account,"
        "amount,timestamp,transaction_type,channel,"
        "sender_location,receiver_location\n"
        "T1,A1,A2,500,2026-01-01 10:00:00,transfer,bank,Mumbai,Delhi\n"
        "T2,A2,A3,-100,2026-01-01 10:01:00,transfer,bank,Delhi,Pune\n"
        "T3,A3,A4,900,2026-01-01 10:02:00,transfer,bank,Pune,Chennai\n"
        "T4,A4,A5,300,not-a-date,transfer,bank,Chennai,Kolkata\n"
        "T5,A5,A6,200,2026-01-01 10:03:00,transfer,bank,Kolkata,Hyderabad\n"
    )
    df, report = ingestion.parse_csv(raw.encode())
    assert report["valid_rows"] == 3
    assert report["flagged_rows"] == 2
    # Valid rows should have correct amounts: 500, 900, 200 (in timestamp order)
    # After sorting: T1(500@10:00), T3(900@10:02), T5(200@10:03)
    assert df.iloc[0]["transaction_id"] == "T1"
    assert df.iloc[0]["amount"] == 500.0
    assert df.iloc[1]["transaction_id"] == "T3"
    assert df.iloc[1]["amount"] == 900.0
    assert df.iloc[2]["transaction_id"] == "T5"
    assert df.iloc[2]["amount"] == 200.0


def test_amount_alignment_duplicate_timestamps():
    """Test stable ordering when timestamps are identical."""
    # Same timestamp for all, different amounts
    raw = (
        "transaction_id,sender_account,receiver_account,"
        "amount,timestamp,transaction_type,channel,"
        "sender_location,receiver_location\n"
        "T1,A1,A2,500,2026-01-01 10:00:00,transfer,bank,Mumbai,Delhi\n"
        "T2,A2,A3,100,2026-01-01 10:00:00,transfer,bank,Delhi,Pune\n"
        "T3,A3,A4,900,2026-01-01 10:00:00,transfer,bank,Pune,Chennai\n"
    )
    df, report = ingestion.parse_csv(raw.encode())
    assert report["valid_rows"] == 3
    # With identical timestamps, original order should be preserved (stable sort)
    # Original order: T1(500), T2(100), T3(900)
    # Pandas sort is stable, so original order preserved
    assert list(df["transaction_id"]) == ["T1", "T2", "T3"]
    assert list(df["amount"]) == [500.0, 100.0, 900.0]


def test_amount_alignment_shuffle_invariance():
    """Property test: shuffle CSV rows 50 times, amounts must match their transaction IDs."""
    import random

    base_rows = [
        "T1,A1,A2,500,2026-01-01 10:00:00,transfer,bank,Mumbai,Delhi",
        "T2,A2,A3,100,2026-01-01 10:01:00,transfer,bank,Delhi,Pune",
        "T3,A3,A4,900,2026-01-01 10:02:00,transfer,bank,Pune,Chennai",
        "T4,A4,A5,200,2026-01-01 10:03:00,transfer,bank,Chennai,Kolkata",
        "T5,A5,A6,300,2026-01-01 10:03:30,transfer,bank,Kolkata,Hyderabad",
    ]

    expected = {
        "T1": 500.0,
        "T2": 100.0,
        "T3": 900.0,
        "T4": 200.0,
        "T5": 300.0,
    }

    header = (
        "transaction_id,sender_account,receiver_account,"
        "amount,timestamp,transaction_type,channel,"
        "sender_location,receiver_location\n"
    )

    for _ in range(50):
        shuffled = base_rows.copy()
        random.shuffle(shuffled)
        raw = header + "\n".join(shuffled) + "\n"
        df, report = ingestion.parse_csv(raw.encode())
        assert report["valid_rows"] == 5
        # Verify each transaction has its correct amount
        for _, row in df.iterrows():
            txn_id = row["transaction_id"]
            amount = row["amount"]
            assert amount == expected[txn_id], (
                f"Transaction {txn_id} has amount {amount}, expected {expected[txn_id]}"
            )


def test_amount_alignment_self_transfer_flagged():
    """Self-transfers are flagged but amounts should still align for other rows."""
    raw = (
        "transaction_id,sender_account,receiver_account,"
        "amount,timestamp,transaction_type,channel,"
        "sender_location,receiver_location\n"
        "T1,A1,A2,500,2026-01-01 10:00:00,transfer,bank,Mumbai,Delhi\n"
        "T2,A2,A2,100,2026-01-01 10:01:00,transfer,bank,Delhi,Pune\n"  # self-transfer
        "T3,A3,A4,900,2026-01-01 10:02:00,transfer,bank,Pune,Chennai\n"
    )
    df, report = ingestion.parse_csv(raw.encode())
    assert report["valid_rows"] == 2  # T2 is flagged as self_transfer
    assert report["flagged_rows"] == 1
    assert report["flags"].get("self_transfer") == 1
    # Valid rows should be T1(500) and T3(900)
    amounts = set(df["amount"])
    assert amounts == {500.0, 900.0}


def test_amount_alignment_duplicate_ids():
    """Duplicate transaction IDs are flagged, amounts align for kept rows."""
    raw = (
        "transaction_id,sender_account,receiver_account,"
        "amount,timestamp,transaction_type,channel,"
        "sender_location,receiver_location\n"
        "T1,A1,A2,500,2026-01-01 10:00:00,transfer,bank,Mumbai,Delhi\n"
        "T1,A2,A3,100,2026-01-01 10:01:00,transfer,bank,Delhi,Pune\n"  # duplicate
        "T2,A3,A4,900,2026-01-01 10:02:00,transfer,bank,Pune,Chennai\n"
    )
    df, report = ingestion.parse_csv(raw.encode())
    assert report["valid_rows"] == 2  # First T1 kept, second T1 flagged
    assert report["flagged_rows"] == 1
    assert report["flags"].get("duplicate_id") == 1
    # First T1 (500) and T2 (900) should be valid
    amounts = set(df["amount"])
    assert amounts == {500.0, 900.0}


def test_amount_alignment_invalid_amounts():
    """Invalid amounts are flagged, valid amounts align."""
    raw = (
        "transaction_id,sender_account,receiver_account,"
        "amount,timestamp,transaction_type,channel,"
        "sender_location,receiver_location\n"
        "T1,A1,A2,500,2026-01-01 10:00:00,transfer,bank,Mumbai,Delhi\n"
        "T2,A2,A3,not-a-number,2026-01-01 10:01:00,transfer,bank,Delhi,Pune\n"
        "T3,A3,A4,900,2026-01-01 10:02:00,transfer,bank,Pune,Chennai\n"
    )
    df, report = ingestion.parse_csv(raw.encode())
    assert report["valid_rows"] == 2  # T2 flagged
    assert report["flagged_rows"] == 1
    assert report["flags"].get("invalid_amount") == 1
    # Valid rows: T1(500) and T3(900)
    amounts = set(df["amount"])
    assert amounts == {500.0, 900.0}