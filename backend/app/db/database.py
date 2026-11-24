"""SQLite database layer.

Uses parameterised queries only (no string interpolation of user input).
Schema is modular so PostgreSQL can replace SQLite later.
"""
import sqlite3
import threading
from contextlib import contextmanager

from app.config import DB_PATH, DATA_DIR

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    investigator_id TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL,
    full_name TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS datasets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    source TEXT NOT NULL DEFAULT 'upload',
    row_count INTEGER NOT NULL DEFAULT 0,
    valid_rows INTEGER NOT NULL DEFAULT 0,
    flagged_rows INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    transaction_id TEXT UNIQUE NOT NULL,
    sender_account TEXT NOT NULL,
    receiver_account TEXT NOT NULL,
    amount REAL NOT NULL,
    timestamp TEXT NOT NULL,
    transaction_type TEXT NOT NULL DEFAULT 'transfer',
    channel TEXT NOT NULL DEFAULT 'bank',
    sender_location TEXT,
    receiver_location TEXT,
    device_id TEXT,
    ip_hash TEXT,
    merchant_id TEXT,
    cashout_location TEXT,
    lat REAL,
    lon REAL,
    flags TEXT NOT NULL DEFAULT '',
    dataset_id INTEGER,
    FOREIGN KEY (dataset_id) REFERENCES datasets(id)
);
CREATE INDEX IF NOT EXISTS idx_tx_sender ON transactions(sender_account);
CREATE INDEX IF NOT EXISTS idx_tx_receiver ON transactions(receiver_account);
CREATE INDEX IF NOT EXISTS idx_tx_time ON transactions(timestamp);

CREATE TABLE IF NOT EXISTS accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id TEXT UNIQUE NOT NULL,
    tx_count INTEGER NOT NULL DEFAULT 0,
    in_amount REAL NOT NULL DEFAULT 0,
    out_amount REAL NOT NULL DEFAULT 0,
    unique_counterparties INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'unreviewed',
    analyst_note TEXT DEFAULT '',
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS account_features (
    account_id TEXT PRIMARY KEY,
    tx_count INTEGER, velocity REAL, in_amount REAL, out_amount REAL,
    in_out_ratio REAL, counterparties INTEGER, rapid_pass_pct REAL,
    rapid_count INTEGER, burst_score REAL, temporal_concentration REAL,
    degree INTEGER, in_degree INTEGER, out_degree INTEGER,
    betweenness REAL, clustering REAL,
    ml_score REAL, ml_anomaly INTEGER, feature_json TEXT
);

CREATE TABLE IF NOT EXISTS risk_scores (
    account_id TEXT PRIMARY KEY,
    risk_score REAL, risk_category TEXT,
    contributors TEXT, detection_method TEXT,
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS clusters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cluster_label TEXT UNIQUE NOT NULL,
    account_count INTEGER, total_amount REAL, avg_risk REAL,
    main_intermediary TEXT, primary_pattern TEXT,
    window_start TEXT, window_end TEXT, account_list TEXT
);

CREATE TABLE IF NOT EXISTS alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    alert_type TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    account_ids TEXT NOT NULL,
    amount REAL, occurred_at TEXT,
    risk_score REAL, severity TEXT NOT NULL,
    recommended_action TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'open',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS money_trails (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trail_id TEXT UNIQUE NOT NULL,
    source_account TEXT NOT NULL,
    terminal_account TEXT NOT NULL,
    starting_amount REAL, tracked_amount REAL,
    hops INTEGER, duration_minutes REAL,
    accounts_involved INTEGER, amount_difference REAL,
    summary TEXT, created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS trail_hops (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trail_id TEXT NOT NULL,
    hop_index INTEGER NOT NULL,
    from_account TEXT NOT NULL,
    to_account TEXT NOT NULL,
    amount REAL NOT NULL,
    timestamp TEXT NOT NULL,
    transaction_id TEXT,
    FOREIGN KEY (trail_id) REFERENCES money_trails(trail_id)
);

CREATE TABLE IF NOT EXISTS investigations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    investigation_id TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    priority TEXT NOT NULL DEFAULT 'medium',
    assigned_to TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'open',
    review_decision TEXT NOT NULL DEFAULT 'pending',
    notes TEXT NOT NULL DEFAULT '',
    created_by TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS investigation_entities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    investigation_id TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    UNIQUE(investigation_id, entity_type, entity_id)
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL DEFAULT (datetime('now')),
    investigator_id TEXT NOT NULL,
    action TEXT NOT NULL,
    entity_type TEXT,
    entity_id TEXT,
    action_type TEXT,
    result TEXT NOT NULL DEFAULT 'success',
    details TEXT DEFAULT ''
);
"""

# Single-writer SQLite connection with WAL for concurrent reads.
_local = threading.local()


def get_connection() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not hasattr(_local, "conn") or _local.conn is None:
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        _local.conn = conn
    return _local.conn


@contextmanager
def transaction():
    """Context manager providing a connection with commit/rollback."""
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise


def init_db() -> None:
    conn = get_connection()
    conn.executescript(SCHEMA)
    # migrate: add review_decision column if missing
    # (for databases created before Round 3)
    cols = [r[1] for r in conn.execute(
        "PRAGMA table_info(investigations)").fetchall()]
    if "review_decision" not in cols:
        conn.execute(
            "ALTER TABLE investigations "
            "ADD COLUMN review_decision "
            "TEXT NOT NULL DEFAULT 'pending'")
    conn.commit()
