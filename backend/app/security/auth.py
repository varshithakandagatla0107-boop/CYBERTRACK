"""Security: password hashing, JWT sessions, role-based access control,
and account identifier masking.

Prototype authentication — do NOT use in production.
"""
from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta

import jwt

from app.config import JWT_ALGORITHM, JWT_EXPIRE_MINUTES, JWT_SECRET, ROLE_PERMISSIONS


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(),
                                 salt.encode(), 120_000)
    return f"pbkdf2_sha256${salt}${digest.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        algo, salt, digest = stored_hash.split("$")
        if algo != "pbkdf2_sha256":
            return False
        computed = hashlib.pbkdf2_hmac("sha256", password.encode(),
                                       salt.encode(), 120_000).hex()
        return hmac.compare_digest(computed, digest)
    except Exception:
        return False


def create_token(investigator_id: str, role: str) -> str:
    payload = {
        "sub": investigator_id,
        "role": role,
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(minutes=JWT_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        return {"error": "Session expired. Please log in again."}
    except jwt.InvalidTokenError:
        return None


def require_permission(role: str | None, permission: str) -> bool:
    if not role or role not in ROLE_PERMISSIONS:
        return False
    return permission in ROLE_PERMISSIONS[role]


def mask_account(account_id: str, keep_last: int = 3) -> str:
    """Mask identifiers: XXXXXX381 instead of full account numbers."""
    if not account_id:
        return ""
    if len(account_id) <= keep_last:
        return account_id
    return "X" * (len(account_id) - keep_last) + account_id[-keep_last:]
