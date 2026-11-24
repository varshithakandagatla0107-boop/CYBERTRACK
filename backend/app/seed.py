"""Seed default demo users.

Prototype accounts — passwords are demo-only.
"""
from __future__ import annotations

from app.db.database import get_connection
from app.security import auth

DEMO_USERS = [
    ("investigator", "cybertrack-demo", "investigator",
     "Demo Investigator"),
    ("analyst", "cybertrack-demo", "analyst",
     "Demo Analyst"),
    ("admin", "cybertrack-demo", "admin",
     "Demo Administrator"),
]


def seed_users() -> None:
    conn = get_connection()
    for investigator_id, password, role, name in DEMO_USERS:
        existing = conn.execute(
            "SELECT id FROM users WHERE investigator_id = ?",
            (investigator_id,),
        ).fetchone()
        if existing:
            continue
        conn.execute(
            """INSERT INTO users
               (investigator_id, password_hash, role, full_name)
               VALUES (?,?,?,?)""",
            (investigator_id,
             auth.hash_password(password), role, name),
        )
    conn.commit()
