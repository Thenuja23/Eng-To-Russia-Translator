"""SQLite storage for accounts, sessions and one-time email tokens.

SQLite keeps the authentication layer self-contained: no extra service, no
extra Python dependency, and it is a real database with real constraints
(unique e-mail, unique Google subject, hashed session/token values).
Switching to Postgres later only requires replacing this module.
"""
from __future__ import annotations

import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterator, Optional

from app.core.config import settings

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    email TEXT NOT NULL UNIQUE COLLATE NOCASE,
    full_name TEXT,
    picture_url TEXT,
    provider TEXT NOT NULL DEFAULT 'password',
    password_hash TEXT,
    google_sub TEXT UNIQUE,
    email_verified INTEGER NOT NULL DEFAULT 0,
    email_verified_at TEXT,
    role TEXT NOT NULL DEFAULT 'student',
    created_at TEXT NOT NULL,
    last_login_at TEXT
);

CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    last_seen_at TEXT NOT NULL,
    user_agent TEXT,
    ip_address TEXT
);

CREATE TABLE IF NOT EXISTS auth_tokens (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    purpose TEXT NOT NULL,
    token_hash TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    used_at TEXT,
    target_email TEXT
);

CREATE TABLE IF NOT EXISTS oauth_states (
    state TEXT PRIMARY KEY,
    code_verifier TEXT NOT NULL,
    redirect_to TEXT,
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS ai_credentials (
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    provider TEXT NOT NULL,
    ciphertext TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    PRIMARY KEY (user_id, provider)
);
CREATE TABLE IF NOT EXISTS ai_preferences (
    user_id TEXT PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    data TEXT NOT NULL DEFAULT '{}',
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS ai_history (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    source TEXT NOT NULL,
    translated TEXT NOT NULL,
    provider TEXT,
    model TEXT,
    mode TEXT,
    created_at TEXT NOT NULL,
    latency_ms INTEGER,
    token_usage INTEGER
);

CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_tokens_user ON auth_tokens(user_id, purpose);
"""


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def iso(moment: datetime) -> str:
    return moment.astimezone(timezone.utc).isoformat(timespec="seconds")


def in_days(days: int) -> str:
    return iso(utcnow() + timedelta(days=days))


def in_minutes(minutes: int) -> str:
    return iso(utcnow() + timedelta(minutes=minutes))


def new_id() -> str:
    return str(uuid.uuid4())


@contextmanager
def connect() -> Iterator[sqlite3.Connection]:
    path = Path(settings.auth_db_path)
    if not path.is_absolute():
        # Resolve relative paths against the backend directory, not the CWD.
        path = Path(__file__).resolve().parents[3] / path
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    try:
        yield connection
        connection.commit()
    finally:
        connection.close()


def init_db() -> None:
    with connect() as connection:
        connection.executescript(SCHEMA)
        # Idempotent, additive migrations preserve all existing account and
        # token records while bringing databases created by earlier versions
        # up to the current schema.
        user_columns = {
            row["name"] for row in connection.execute("PRAGMA table_info(users)")
        }
        if "email_verified_at" not in user_columns:
            connection.execute("ALTER TABLE users ADD COLUMN email_verified_at TEXT")
        token_columns = {
            row["name"] for row in connection.execute("PRAGMA table_info(auth_tokens)")
        }
        if "target_email" not in token_columns:
            connection.execute("ALTER TABLE auth_tokens ADD COLUMN target_email TEXT")


def row_to_user(row: Optional[sqlite3.Row]) -> Optional[dict]:
    """Public user shape. Never exposes the password hash."""
    if row is None:
        return None
    return {
        "id": row["id"],
        "email": row["email"],
        "full_name": row["full_name"] or "",
        "picture_url": row["picture_url"] or "",
        "provider": row["provider"],
        "email_verified": bool(row["email_verified"]),
        "email_verified_at": row["email_verified_at"],
        "role": row["role"],
        "created_at": row["created_at"],
        "last_login_at": row["last_login_at"],
        "has_password": bool(row["password_hash"]),
    }


def find_user_by_email(email: str) -> Optional[sqlite3.Row]:
    with connect() as connection:
        return connection.execute(
            "SELECT * FROM users WHERE email = ? COLLATE NOCASE", ((email or "").strip(),)
        ).fetchone()


def find_user_by_id(user_id: str) -> Optional[sqlite3.Row]:
    with connect() as connection:
        return connection.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()


def find_user_by_google_sub(sub: str) -> Optional[sqlite3.Row]:
    with connect() as connection:
        return connection.execute(
            "SELECT * FROM users WHERE google_sub = ?", (sub,)
        ).fetchone()


def create_user(
    *,
    email: str,
    full_name: str = "",
    picture_url: str = "",
    provider: str = "password",
    password_hash: Optional[str] = None,
    google_sub: Optional[str] = None,
    email_verified: bool = False,
) -> dict:
    user_id = new_id()
    with connect() as connection:
        connection.execute(
            """
            INSERT INTO users (id, email, full_name, picture_url, provider,
                               password_hash, google_sub, email_verified,
                               email_verified_at, role, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'student', ?)
            """,
            (
                user_id,
                email.strip(),
                full_name.strip(),
                picture_url.strip(),
                provider,
                password_hash,
                google_sub,
                1 if email_verified else 0,
                iso(utcnow()) if email_verified else None,
                iso(utcnow()),
            ),
        )
        row = connection.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    return row_to_user(row)


def update_user(user_id: str, **fields) -> Optional[dict]:
    allowed = {
        "email", "full_name", "picture_url", "email_verified", "email_verified_at", "last_login_at",
        "password_hash", "google_sub", "provider",
    }
    assignments = []
    values = []
    for key, value in fields.items():
        if key not in allowed:
            continue
        assignments.append(f"{key} = ?")
        values.append(1 if isinstance(value, bool) else value)
    if not assignments:
        return row_to_user(find_user_by_id(user_id))
    values.append(user_id)
    with connect() as connection:
        connection.execute(
            f"UPDATE users SET {', '.join(assignments)} WHERE id = ?", values
        )
        row = connection.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    return row_to_user(row)
