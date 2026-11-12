"""Server-side Google OAuth 2.0 (authorization code flow with PKCE).

The client secret never leaves the backend. The browser is redirected to
Google, Google redirects back to this backend, and only then is a session
cookie issued. The returned access token is used to read the verified profile
from Google's OpenID userinfo endpoint.
"""
from __future__ import annotations

import base64
import hashlib
import secrets
from typing import Optional, Tuple
from urllib.parse import urlencode

import httpx

from app.core.config import settings
from app.services.auth import db as store

AUTHORIZE_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
USERINFO_URL = "https://openidconnect.googleapis.com/v1/userinfo"
SCOPES = "openid email profile"


class GoogleAuthError(RuntimeError):
    """Google OAuth could not be completed."""


def configured() -> bool:
    return settings.google_oauth_configured


def start_flow(redirect_to: str = "/") -> Tuple[str, str]:
    """Create a state row and return (state, code_challenge)."""
    state = secrets.token_urlsafe(24)
    verifier = secrets.token_urlsafe(48)
    challenge = (
        base64.urlsafe_b64encode(hashlib.sha256(verifier.encode("ascii")).digest())
        .decode("ascii")
        .rstrip("=")
    )
    with store.connect() as connection:
        connection.execute(
            """
            INSERT INTO oauth_states (state, code_verifier, redirect_to, created_at, expires_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (state, verifier, redirect_to or "/", store.iso(store.utcnow()), store.in_minutes(15)),
        )
        connection.execute(
            "DELETE FROM oauth_states WHERE expires_at <= ?", (store.iso(store.utcnow()),)
        )
    return state, challenge


def authorize_url(state: str, code_challenge: str) -> str:
    params = {
        "client_id": settings.auth_google_client_id,
        "redirect_uri": settings.google_redirect_uri,
        "response_type": "code",
        "scope": SCOPES,
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
        "access_type": "online",
        "prompt": "select_account",
    }
    return f"{AUTHORIZE_URL}?{urlencode(params)}"


def consume_state(state: str) -> Optional[str]:
    """Return the stored code verifier once, then delete the state row."""
    if not state:
        return None
    with store.connect() as connection:
        row = connection.execute(
            "SELECT * FROM oauth_states WHERE state = ?", (state,)
        ).fetchone()
        if row is None:
            return None
        connection.execute("DELETE FROM oauth_states WHERE state = ?", (state,))
        if row["expires_at"] <= store.iso(store.utcnow()):
            return None
    return row["code_verifier"]


def exchange_code(code: str, code_verifier: str) -> dict:
    if not configured():
        raise GoogleAuthError("Google sign-in is not configured on this server.")
    payload = {
        "code": code,
        "client_id": settings.auth_google_client_id,
        "client_secret": settings.auth_google_client_secret,
        "redirect_uri": settings.google_redirect_uri,
        "grant_type": "authorization_code",
        "code_verifier": code_verifier,
    }
    try:
        with httpx.Client(timeout=20) as client:
            response = client.post(TOKEN_URL, data=payload)
    except httpx.HTTPError as exc:
        raise GoogleAuthError(f"Could not reach Google: {exc}") from exc
    if response.status_code >= 400:
        raise GoogleAuthError(
            f"Google rejected the sign-in ({response.status_code}). "
            "Check the OAuth redirect URI and client credentials."
        )
    data = response.json()
    if not data.get("access_token"):
        raise GoogleAuthError("Google did not return an access token.")
    return data


def fetch_profile(access_token: str) -> dict:
    try:
        with httpx.Client(timeout=20) as client:
            response = client.get(
                USERINFO_URL, headers={"Authorization": f"Bearer {access_token}"}
            )
    except httpx.HTTPError as exc:
        raise GoogleAuthError(f"Could not read the Google profile: {exc}") from exc
    if response.status_code >= 400:
        raise GoogleAuthError("Google did not return a profile for this account.")
    profile = response.json()
    if not profile.get("sub") or not profile.get("email"):
        raise GoogleAuthError("The Google profile is missing an account id or e-mail.")
    return profile
