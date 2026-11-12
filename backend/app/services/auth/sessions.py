"""Opaque server-side sessions stored as hashes.

The browser only receives a random token in an HttpOnly cookie. The database
stores SHA-256 hashes, so a database leak does not hand out live sessions.
"""
from __future__ import annotations

import hashlib
import secrets
from typing import Optional

from app.core.config import settings
from app.services.auth import db as store


def _hash(token: str) -> str:
    return hashlib.sha256((token or "").encode("utf-8")).hexdigest()


def create_session(user_id: str, user_agent: str = "", ip_address: str = "") -> str:
    token = secrets.token_urlsafe(32)
    now = store.iso(store.utcnow())
    with store.connect() as connection:
        connection.execute(
            """
            INSERT INTO sessions (id, user_id, created_at, expires_at, last_seen_at,
                                  user_agent, ip_address)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                _hash(token),
                user_id,
                now,
                store.in_days(settings.auth_session_days),
                now,
                (user_agent or "")[:300],
                (ip_address or "")[:64],
            ),
        )
    return token


def session_user(token: Optional[str]) -> Optional[dict]:
    """Resolve a cookie token to a user, expiring dead sessions on the way."""
    if not token:
        return None
    token_hash = _hash(token)
    now = store.iso(store.utcnow())
    with store.connect() as connection:
        row = connection.execute(
            """
            SELECT u.*, s.expires_at AS session_expires_at
            FROM sessions s JOIN users u ON u.id = s.user_id
            WHERE s.id = ?
            """,
            (token_hash,),
        ).fetchone()
        if row is None:
            return None
        if row["session_expires_at"] <= now:
            connection.execute("DELETE FROM sessions WHERE id = ?", (token_hash,))
            return None
        connection.execute(
            "UPDATE sessions SET last_seen_at = ? WHERE id = ?", (now, token_hash)
        )
        connection.execute("DELETE FROM sessions WHERE expires_at <= ?", (now,))
    return store.row_to_user(row)


def revoke_session(token: Optional[str]) -> None:
    if not token:
        return
    with store.connect() as connection:
        connection.execute("DELETE FROM sessions WHERE id = ?", (_hash(token),))


def revoke_all_sessions(user_id: str) -> None:
    with store.connect() as connection:
        connection.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))
