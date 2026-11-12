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
TOKENINFO_URL = "https://oauth2.googleapis.com/tokeninfo"
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
    if not data.get("access_token") or not data.get("id_token"):
        raise GoogleAuthError("Google did not return the required sign-in tokens.")
    return data


def verify_id_token(id_token: str) -> dict:
    """Ask Google's TLS-protected tokeninfo endpoint to validate the ID token.

    Audience, issuer and expiry are checked explicitly before claims are used.
    The ID token is never sent to or exposed by the frontend.
    """
    try:
        with httpx.Client(timeout=20) as client:
            response = client.get(
                TOKENINFO_URL, params={"id_token": id_token}
            )
    except httpx.HTTPError as exc:
        raise GoogleAuthError("Could not validate the Google identity token.") from exc
    if response.status_code >= 400:
        raise GoogleAuthError("Google rejected the identity token.")
    profile = response.json()
    try:
        expires_at = int(profile.get("exp", "0"))
    except (TypeError, ValueError):
        expires_at = 0
    if profile.get("aud") != settings.auth_google_client_id:
        raise GoogleAuthError("Google identity token was issued for a different application.")
    if profile.get("iss") not in ("accounts.google.com", "https://accounts.google.com"):
        raise GoogleAuthError("Google identity token has an invalid issuer.")
    if expires_at <= int(store.utcnow().timestamp()):
        raise GoogleAuthError("Google identity token has expired.")
    if not profile.get("sub") or not profile.get("email"):
        raise GoogleAuthError("Google identity token is missing an account id or e-mail.")
    if str(profile.get("email_verified", "")).lower() not in ("true", "1"):
        raise GoogleAuthError("Google has not verified this e-mail address.")
    return profile


def fetch_profile(access_token: str) -> dict:
    """Fetch display-only profile fields after independently validating ID token."""
    try:
        with httpx.Client(timeout=20) as client:
            response = client.get(
                USERINFO_URL, headers={"Authorization": f"Bearer {access_token}"}
            )
    except httpx.HTTPError as exc:
        raise GoogleAuthError("Could not read the Google profile.") from exc
    if response.status_code >= 400:
        raise GoogleAuthError("Google did not return a profile for this account.")
    return response.json()
