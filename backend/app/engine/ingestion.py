"""CSV ingestion and validation.

Validates structure, amounts, timestamps; flags (never silently drops) invalid
records. Returns a clean pandas DataFrame plus a validation report.
"""
from __future__ import annotations

import io
import math
from datetime import datetime, timezone

import pandas as pd

from app.config import MAX_AMOUNT, MIN_AMOUNT, TIMESTAMP_NAIVE_AS_UTC

REQUIRED_COLUMNS = [
    "transaction_id", "sender_account", "receiver_account",
    "amount", "timestamp", "transaction_type", "channel",
    "sender_location", "receiver_location",
]
OPTIONAL_COLUMNS = ["device_id", "ip_hash", "merchant_id", "cashout_location"]


class ValidationError(Exception):
    """Raised when an upload cannot be processed at all."""


def _increment_field_error(report: dict, field: str, count: int) -> None:
    """Increment field error counter in report."""
    report["field_errors"][field] = report["field_errors"].get(field, 0) + count


class ValidationError(Exception):
    """Raised when an upload cannot be processed at all."""


def parse_csv(raw: bytes | str, filename: str = "upload.csv") -> tuple[pd.DataFrame, dict]:
    """Parse and validate a CSV payload.

    Returns (clean_df, report). Invalid rows are flagged into the report and
    excluded from the clean frame, never silently discarded.
    """
    if filename.lower().endswith(".csv") is False and isinstance(raw, bytes):
        pass  # extension checked by caller; still accept csv content
    try:
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8-sig")
        df = pd.read_csv(io.StringIO(raw))
    except Exception as exc:
        raise ValidationError(f"Upload failed: file could not be parsed as CSV ({exc}).")

    if df.empty:
        raise ValidationError("Upload failed: the file contains no records.")

    # --- structural validation ---
    columns = [c.strip().lower() for c in df.columns]
    df.columns = columns
    missing = [c for c in REQUIRED_COLUMNS if c not in columns]
    if missing:
        raise ValidationError(
            "Upload failed: missing required column"
            f"{'s' if len(missing) > 1 else ''} {', '.join(missing)}."
        )

    df = df[columns].copy()
    # Add stable source row identifier (1-based CSV row number) before any filtering/sorting
    df["_source_row"] = range(1, len(df) + 1)
    for col in OPTIONAL_COLUMNS:
        if col not in df.columns:
            df[col] = ""

    report = {
        "total_rows": int(len(df)),
        "valid_rows": 0,
        "flagged_rows": 0,
        "errors": [],
        "warnings": [],
        "flags": {},
        "rejected_rows": [],
        "field_errors": {},  # field -> count
    }

    # --- row-level validation ---
    flags: list[str] = [""] * len(df)

    # amounts - convert in place to keep alignment
    df["_amount_num"] = pd.to_numeric(df["amount"], errors="coerce")
    
    # Check for NaN, negative, zero, infinity
    bad_amount = df["_amount_num"].isna() | (df["_amount_num"] <= 0)
    if bad_amount.any():
        n = int(bad_amount.sum())
        report["errors"].append(f"{n} record(s) with missing, zero, or negative amount")
        for i in df.index[bad_amount]:
            flags[i] = "invalid_amount"
        _increment_field_error(report, "amount", n)

    # Check for infinity/NaN values
    inf_amount = df["_amount_num"].apply(lambda x: math.isinf(x) if pd.notna(x) else False)
    if inf_amount.any():
        n = int(inf_amount.sum())
        report["errors"].append(f"{n} record(s) with infinite amount")
        for i in df.index[inf_amount]:
            if not flags[i]:
                flags[i] = "invalid_amount"
        _increment_field_error(report, "amount", n)

    # Check amount bounds
    out_of_bounds = (df["_amount_num"] < MIN_AMOUNT) | (df["_amount_num"] > MAX_AMOUNT)
    # Only flag if not already flagged (use flags list since _flag column not created yet)
    out_of_bounds = out_of_bounds & (pd.Series(flags) == "")
    if out_of_bounds.any():
        n = int(out_of_bounds.sum())
        report["warnings"].append(f"{n} record(s) with amount outside configured bounds [{MIN_AMOUNT}, {MAX_AMOUNT}]")
        for i in df.index[out_of_bounds]:
            flags[i] = "amount_out_of_bounds"
        _increment_field_error(report, "amount", n)

    # timestamps
    parsed_ts = pd.to_datetime(df["timestamp"], errors="coerce", utc=True)
    bad_ts = parsed_ts.isna()
    if bad_ts.any():
        n = int(bad_ts.sum())
        report["errors"].append(f"{n} record(s) with unparseable timestamp")
        for i in df.index[bad_ts]:
            flags[i] = "invalid_timestamp"
        _increment_field_error(report, "timestamp", n)

    df["_ts"] = parsed_ts

    # accounts
    df["sender_account"] = df["sender_account"].astype(str).str.strip().str.upper()
    df["receiver_account"] = df["receiver_account"].astype(str).str.strip().str.upper()
    bad_accounts = (df["sender_account"].isin(["", "NAN", "NONE"])) | (
        df["receiver_account"].isin(["", "NAN", "NONE"])
    )
    if bad_accounts.any():
        n = int(bad_accounts.sum())
        report["errors"].append(f"{n} record(s) with empty account identifier")
        for i in df.index[bad_accounts]:
            flags[i] = "invalid_account"
        _increment_field_error(report, "sender_account", n)
        _increment_field_error(report, "receiver_account", n)

    # self-transfer
    self_tx = df["sender_account"] == df["receiver_account"]
    if self_tx.any():
        n = int(self_tx.sum())
        report["warnings"].append(f"{n} self-transfer record(s) flagged")
        for i in df.index[self_tx]:
            if not flags[i]:
                flags[i] = "self_transfer"

    # duplicates
    dup = df.duplicated(subset=["transaction_id"], keep="first")
    if dup.any():
        n = int(dup.sum())
        report["warnings"].append(f"{n} duplicate transaction_id record(s) flagged")
        for i in df.index[dup]:
            if not flags[i]:
                flags[i] = "duplicate_id"
        _increment_field_error(report, "transaction_id", n)

    df["_flag"] = flags
    df["_ts"] = pd.to_datetime(df["timestamp"], errors="coerce", utc=True)

    valid = df[df["_flag"] == ""].copy()
    valid = valid.sort_values("_ts").reset_index(drop=True)

    report["valid_rows"] = int(len(valid))
    report["flagged_rows"] = int(len(df) - len(valid))
    report["flags"] = _count_by(df.loc[df["_flag"] != "", "_flag"])

    # capture rejected rows for investigator inspection
    rejected = df[df["_flag"] != ""].copy()
    for _, row in rejected.head(200).iterrows():
        report["rejected_rows"].append({
            "transaction_id": str(row.get("transaction_id", "")),
            "sender_account": str(row.get("sender_account", "")),
            "receiver_account": str(row.get("receiver_account", "")),
            "amount": str(row.get("amount", "")),
            "timestamp": str(row.get("timestamp", "")),
            "reason": _flag_reason(row["_flag"]),
        })
    report["rejected_total"] = int(len(rejected))
    report["rejected_shown"] = int(len(report["rejected_rows"]))

    if valid.empty:
        raise ValidationError("Upload failed: no valid records remained after validation.")

    # normalise fields
    for col in ["transaction_type", "channel"]:
        valid[col] = valid[col].astype(str).str.strip().str.lower().replace({"nan": "unknown", "": "unknown"})
    for col in ["sender_location", "receiver_location", "device_id", "ip_hash",
                "merchant_id", "cashout_location"]:
        valid[col] = valid[col].astype(str).str.strip().replace({"nan": ""})
    # Use the pre-converted numeric amount column (aligned via stable index)
    valid["amount"] = valid["_amount_num"].round(2)

    return valid, report


def _count_by(series: pd.Series) -> dict:
    return {str(k): int(v) for k, v in series.value_counts().items()}


def _flag_reason(flag: str) -> str:
    return {
        "invalid_amount": "Missing, zero, negative, or infinite amount",
        "invalid_timestamp": "Missing or unparseable timestamp",
        "invalid_account": "Empty account identifier",
        "self_transfer": "Self-transfer (sender = receiver)",
        "duplicate_id": "Duplicate transaction_id",
        "amount_out_of_bounds": f"Amount outside configured bounds [{MIN_AMOUNT}, {MAX_AMOUNT}]",
    }.get(flag, f"Flagged: {flag}")


def now_iso() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")