"""One-time e-mail tokens plus optional SMTP delivery.

Verification and password-reset tokens are real: random, single-use, hashed at
rest and time limited. Delivery needs SMTP settings; when they are missing the
token is still created and the API reports that e-mail delivery is not
configured, instead of claiming a message was sent.
"""
from __future__ import annotations

import hashlib
import logging
import secrets
import smtplib
from email.message import EmailMessage
from typing import Optional

from app.core.config import settings
from app.services.auth import db as store

logger = logging.getLogger("app.auth.mailer")

VERIFY_TTL_MINUTES = 60 * 24
RESET_TTL_MINUTES = 60

PURPOSE_VERIFY = "verify"
PURPOSE_RESET = "reset"


def _hash(token: str) -> str:
    return hashlib.sha256((token or "").encode("utf-8")).hexdigest()


def create_token(user_id: str, purpose: str, ttl_minutes: int) -> str:
    token = secrets.token_urlsafe(32)
    with store.connect() as connection:
        # Only the newest link for a purpose should work.
        connection.execute(
            "UPDATE auth_tokens SET used_at = ? WHERE user_id = ? AND purpose = ? AND used_at IS NULL",
            (store.iso(store.utcnow()), user_id, purpose),
        )
        connection.execute(
            """
            INSERT INTO auth_tokens (id, user_id, purpose, token_hash, created_at, expires_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                store.new_id(),
                user_id,
                purpose,
                _hash(token),
                store.iso(store.utcnow()),
                store.in_minutes(ttl_minutes),
            ),
        )
    return token


def consume_token(token: str, purpose: str) -> Optional[str]:
    """Mark a token used and return its user id, or None when invalid."""
    if not token:
        return None
    token_hash = _hash(token)
    now = store.iso(store.utcnow())
    with store.connect() as connection:
        row = connection.execute(
            "SELECT * FROM auth_tokens WHERE token_hash = ? AND purpose = ?",
            (token_hash, purpose),
        ).fetchone()
        if row is None or row["used_at"] or row["expires_at"] <= now:
            return None
        connection.execute(
            "UPDATE auth_tokens SET used_at = ? WHERE id = ?", (now, row["id"])
        )
        return row["user_id"]


def verification_url(token: str) -> str:
    base = settings.auth_app_base_url.rstrip("/")
    return f"{base}/auth/verify-email?token={token}"


def reset_url(token: str) -> str:
    base = settings.auth_app_base_url.rstrip("/")
    return f"{base}/reset-password?token={token}"


def send(to_email: str, subject: str, body: str) -> bool:
    """Send an e-mail. Returns False when SMTP is not configured/failed."""
    if not settings.email_delivery_configured:
        logger.warning(
            "SMTP is not configured; %s for %s was created but not delivered",
            subject,
            to_email,
        )
        return False

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = settings.auth_smtp_from or settings.auth_smtp_user or "no-reply@localhost"
    message["To"] = to_email
    message.set_content(body)
    try:
        with smtplib.SMTP(settings.auth_smtp_host, settings.auth_smtp_port, timeout=15) as server:
            if settings.auth_smtp_starttls:
                server.starttls()
            if settings.auth_smtp_user and settings.auth_smtp_password:
                server.login(settings.auth_smtp_user, settings.auth_smtp_password)
            server.send_message(message)
        return True
    except Exception as exc:  # noqa: BLE001 - delivery failure must not break sign-up
        logger.error("Failed to send %s to %s: %s", subject, to_email, exc)
        return False
