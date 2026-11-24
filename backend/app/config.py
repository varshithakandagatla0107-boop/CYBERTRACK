"""CYBERTRACK application configuration.

Secrets come from environment variables. Never commit secrets.
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

def _parse_db_path(raw: str) -> str:
    """Parse CYBERTRACK_DB into a filesystem path.
    Accepts: plain path, sqlite:///relative.db, sqlite:////abs/path.db
    Rejects: postgres://, mysql://, etc.
    """
    raw = raw.strip()
    if raw.lower().startswith(("postgres://", "postgresql://", "mysql://", "mariadb://")):
        raise ValueError("PostgreSQL/MySQL not supported in this release. Use SQLite only.")
    if raw.lower().startswith("sqlite:///"):
        # sqlite:///relative.db or sqlite:////absolute/path.db
        path_part = raw[9:]  # strip 'sqlite:///'
        if path_part.startswith("/"):
            # absolute path (sqlite:////abs/path.db)
            return path_part
        # relative path (sqlite:///relative.db)
        return str(Path(raw[9:]).resolve())
    # plain path
    return str(Path(raw).resolve())

DB_PATH = _parse_db_path(os.environ.get("CYBERTRACK_DB", str(DATA_DIR / "cybertrack.db")))

# JWT secret — override via environment variable in any real deployment.
JWT_SECRET = os.environ.get("CYBERTRACK_JWT_SECRET", "prototype-demo-secret-change-me")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = int(os.environ.get("CYBERTRACK_JWT_EXPIRE_MINUTES", "480"))

# Deprecated alias
if os.environ.get("CYBERTRACK_JWT_EXPIRE"):
    import warnings
    warnings.warn("CYBERTRACK_JWT_EXPIRE is deprecated, use CYBERTRACK_JWT_EXPIRE_MINUTES", DeprecationWarning)
    JWT_EXPIRE_MINUTES = int(os.environ.get("CYBERTRACK_JWT_EXPIRE", "480"))
else:
    JWT_EXPIRE_MINUTES = int(os.environ.get("CYBERTRACK_JWT_EXPIRE_MINUTES", "480"))

JWT_ALGORITHM = "HS256"

# Risk model weights (configurable). Normalised to a 0-100 scale.
RISK_WEIGHTS = {
    "pass_through": 22,
    "velocity": 18,
    "centrality": 17,
    "counterparty_diversity": 14,
    "burst": 11,
    "ml_anomaly": 9,
    "temporal_concentration": 9,
}

RISK_THRESHOLDS = {"high": 70, "medium": 40}  # 0-39 low, 40-69 medium, 70-100 high

RAPID_PASS_MINUTES = 15      # funds forwarded within this window count as rapid
BURST_WINDOW_MINUTES = 60    # window used for burst detection
MULTI_HOP_MAX_MINUTES = 30   # rapid multi-hop detection window

# File upload limits
MAX_UPLOAD_MB = 25
ALLOWED_EXTENSIONS = {".csv"}

# Amount validation bounds (configurable)
MIN_AMOUNT = float(os.environ.get("CYBERTRACK_MIN_AMOUNT", "0.01"))
MAX_AMOUNT = float(os.environ.get("CYBERTRACK_MAX_AMOUNT", "100000000"))  # 100M

# Timestamp parsing: naive timestamps treated as UTC
TIMESTAMP_NAIVE_AS_UTC = True

# Roles and their capabilities (RBAC)
ROLE_PERMISSIONS = {
    "investigator": {"view", "trace", "investigate", "note", "update_status", "export"},
    "analyst": {"view", "trace", "investigate", "note", "update_status", "export",
                "upload", "run_analysis", "review_models"},
    "admin": {"view", "trace", "investigate", "note", "update_status", "export",
              "upload", "run_analysis", "review_models", "manage_users", "view_audit", "configure"},
}

# Application mode: demo | production
MODE = os.environ.get("CYBERTRACK_MODE", "demo")

# Demo users are only created in demo mode
DEMO_ENABLED = os.environ.get("CYBERTRACK_MODE", "demo") == "demo"

# Data directory
DATA_DIR = Path(__file__).resolve().parent.parent / "data"