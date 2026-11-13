"""Real authentication: e-mail/password accounts, sessions and Google OAuth.

Security notes
--------------
* Passwords are hashed with scrypt (salted, per user), or PBKDF2-HMAC-SHA256
  with a high iteration count on Python builds whose OpenSSL lacks scrypt, and
  are never stored or returned in plain text.
* Sessions are opaque random tokens. The browser gets one HttpOnly, SameSite=Lax
  cookie; the database stores only a SHA-256 hash of the token.
* Google sign-in is the server-side authorization-code flow with PKCE. The
  client secret stays on the backend and the browser never sees a provider token.
* Users, roles and ids always come from the session, never from the request body.
"""
from __future__ import annotations

import logging
import ipaddress
import re
import sqlite3
import time
from typing import Dict, List, Optional
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field

from app.core.config import settings
from app.services.auth import db as store
from app.services.auth import google, mailer, sessions
from app.services.auth.passwords import (
    hash_password,
    needs_rehash,
    strength_errors,
    verify_password,
)

logger = logging.getLogger("app.auth")

router = APIRouter(prefix="/auth", tags=["auth"])

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$")

# Small in-process throttle for credential endpoints (brute-force defence).
_ATTEMPTS: Dict[str, List[float]] = {}
_WINDOW_SECONDS = 300
_MAX_ATTEMPTS = 12


# --------------------------------------------------------------------- models
class RegisterIn(BaseModel):
    full_name: str = Field(default="", max_length=120)
    email: str = Field(..., max_length=254)
    password: str = Field(..., max_length=200)


class LoginIn(BaseModel):
    email: str = Field(..., max_length=254)
    password: str = Field(..., max_length=200)


class EmailIn(BaseModel):
    email: str = Field(..., max_length=254)


class TokenIn(BaseModel):
    token: str = Field(..., max_length=200)


class ResetIn(BaseModel):
    token: str = Field(..., max_length=200)
    password: str = Field(..., max_length=200)


class ProfileIn(BaseModel):
    full_name: str = Field(..., min_length=1, max_length=120)


# ------------------------------------------------------------------- helpers
def _clean_email(value: str) -> str:
    return (value or "").strip().lower()


def _valid_email(value: str) -> bool:
    return bool(EMAIL_RE.match(value or ""))


def _throttle(key: str) -> None:
    now = time.time()
    recent = [stamp for stamp in _ATTEMPTS.get(key, []) if now - stamp < _WINDOW_SECONDS]
    if len(recent) >= _MAX_ATTEMPTS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many attempts. Please wait a few minutes and try again.",
        )
    recent.append(now)
    _ATTEMPTS[key] = recent


def _clear_throttle(key: str) -> None:
    """Forget failed attempts after a successful sign-in."""
    _ATTEMPTS.pop(key, None)


def _forwarded(value: str) -> str:
    """Nearest proxy's value for an X-Forwarded-* header.

    Proxies append, so the last entry is the one added by the proxy closest to
    this server (e.g. the Vite dev proxy). Taking it prevents a client from
    spoofing an earlier entry to impersonate the app's own origin.
    """
    parts = [part.strip() for part in (value or "").split(",") if part.strip()]
    return parts[-1] if parts else ""


def _request_origin(request: Request) -> str:
    """Effective browser origin, accounting for a same-host proxy."""
    forwarded = _forwarded(request.headers.get("x-forwarded-proto") or "")
    host = _forwarded(request.headers.get("x-forwarded-host") or "") or request.headers.get(
        "host", ""
    )
    scheme = forwarded or request.url.scheme
    return f"{scheme}://{host}" if host else ""


def _check_origin(request: Request) -> None:
    """Reject cross-site form posts; cookies are SameSite=Lax as well.

    A request from the app's own origin is always fine. This covers the case
    where the frontend reaches this API through a reverse/proxy on the same
    hostname (e.g. Vite dev proxy, or a production same-origin deployment):
    we read the effective origin from X-Forwarded-Host / X-Forwarded-Proto / Host.
    Anything else must appear in the configured CORS origins.
    """
    origin = (request.headers.get("origin") or "").rstrip("/")
    if not origin:
        return

    if origin == _request_origin(request):
        return
    allowed = settings.cors_origin_list
    if origin in allowed:
        return
    # The configured public frontend origin is always trusted, even when a
    # reverse proxy rewrites the Host header before forwarding to this API.
    if origin == settings.auth_app_base_url.rstrip("/"):
        return
    regex = (settings.cors_origin_regex or "").strip()
    if regex:
        try:
            if re.match(regex, origin):
                return
        except re.error:
            pass
    raise HTTPException(status_code=403, detail="Cross-site request rejected.")


def _is_https(request: Request) -> bool:
    forwarded = _forwarded(request.headers.get("x-forwarded-proto") or "")
    return forwarded == "https" or request.url.scheme == "https"


def _set_session_cookie(response: Response, request: Request, token: str) -> None:
    response.set_cookie(
        key=settings.auth_cookie_name,
        value=token,
        max_age=settings.auth_session_days * 24 * 3600,
        httponly=True,
        samesite="lax",
        secure=settings.auth_cookie_secure or _is_https(request),
        path="/",
    )


def _clear_session_cookie(response: Response) -> None:
    response.delete_cookie(settings.auth_cookie_name, path="/")


def _client_ip(request: Request) -> str:
    remote = request.client.host if request.client else ""
    try:
        remote_ip = ipaddress.ip_address(remote)
    except ValueError:
        return remote

    trusted_networks = []
    for value in settings.auth_trusted_proxy_ips.split(","):
        try:
            trusted_networks.append(ipaddress.ip_network(value.strip(), strict=False))
        except ValueError:
            continue

    def trusted(address) -> bool:
        return any(address in network for network in trusted_networks)

    # Ignore caller-supplied forwarding headers unless the socket peer is an
    # explicitly trusted proxy. Walk from the nearest proxy toward the client
    # so a spoofed value prepended by the caller cannot pick the throttle key.
    if not trusted(remote_ip):
        return str(remote_ip)
    chain = [part.strip() for part in request.headers.get("x-forwarded-for", "").split(",")]
    current = remote_ip
    for value in reversed([part for part in chain if part]):
        if not trusted(current):
            break
        try:
            current = ipaddress.ip_address(value)
        except ValueError:
            break
    return str(current)


def _app_url(path: str = "/") -> str:
    base = settings.auth_app_base_url.rstrip("/")
    return f"{base}{path}"


def _public(user: Optional[dict]) -> Optional[dict]:
    return user


# --------------------------------------------------------------- dependencies
def current_user(request: Request) -> dict:
    """Session-backed user; the only trusted source of identity."""
    user = sessions.session_user(request.cookies.get(settings.auth_cookie_name))
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Please sign in to continue."
        )
    return user


def optional_user(request: Request) -> Optional[dict]:
    return sessions.session_user(request.cookies.get(settings.auth_cookie_name))


def require_feature_user(request: Request) -> Optional[dict]:
    """Used by the feature routers when AUTH_PROTECT_FEATURES is enabled."""
    if not settings.auth_protect_features:
        return None
    return current_user(request)


# ------------------------------------------------------------------ endpoints
@router.get("/config")
def auth_config():
    """Public capability probe so the UI can label the Google button honestly."""
    return {
        "google_enabled": settings.google_oauth_configured,
        "email_delivery_configured": settings.email_delivery_configured,
        "session_days": settings.auth_session_days,
    }


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(payload: RegisterIn, request: Request, response: Response):
    _check_origin(request)
    email = _clean_email(payload.email)
    _throttle(f"register:{_client_ip(request)}")
    if not _valid_email(email):
        raise HTTPException(422, "Enter a valid e-mail address, e.g. you@example.com.")
    problems = strength_errors(payload.password)
    if problems:
        raise HTTPException(422, " ".join(problems))
    if store.find_user_by_email(email) is not None:
        raise HTTPException(409, "An account with this e-mail already exists. Try signing in.")

    try:
        user = store.create_user(
            email=email,
            full_name=payload.full_name.strip() or email.split("@")[0],
            password_hash=hash_password(payload.password),
            provider="password",
        )
    except sqlite3.IntegrityError:
        # Another request created the same account in the meantime.
        raise HTTPException(409, "An account with this e-mail already exists. Try signing in.")
    token = mailer.create_token(user["id"], mailer.PURPOSE_VERIFY, mailer.VERIFY_TTL_MINUTES)
    sent = mailer.send(
        email,
        "Confirm your e-mail address",
        "Welcome! Confirm your e-mail address to finish setting up your account:\n\n"
        f"{mailer.verification_url(token)}\n\n"
        f"This link expires in {mailer.VERIFY_TTL_MINUTES // 60} hours. "
        "If you did not create this account you can ignore this message.",
    )
    session_token = sessions.create_session(
        user["id"], request.headers.get("user-agent", ""), _client_ip(request)
    )
    _set_session_cookie(response, request, session_token)
    return {"user": user, "email_sent": sent}


@router.post("/login")
def login(payload: LoginIn, request: Request, response: Response):
    _check_origin(request)
    email = _clean_email(payload.email)
    throttle_key = f"login:{email or _client_ip(request)}"
    _throttle(throttle_key)
    row = store.find_user_by_email(email)
    if row is None or not row["password_hash"] or not verify_password(
        row["password_hash"], payload.password
    ):
        raise HTTPException(401, "E-mail or password is incorrect.")

    _clear_throttle(throttle_key)
    updates = {"last_login_at": store.iso(store.utcnow())}
    if needs_rehash(row["password_hash"]):
        # Upgrade legacy/mismatched hash formats transparently on sign-in.
        updates["password_hash"] = hash_password(payload.password)
    store.update_user(row["id"], **updates)
    token = sessions.create_session(
        row["id"], request.headers.get("user-agent", ""), _client_ip(request)
    )
    _set_session_cookie(response, request, token)
    user = store.row_to_user(store.find_user_by_id(row["id"]))
    return {"user": user}


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(request: Request, response: Response):
    _check_origin(request)
    sessions.revoke_session(request.cookies.get(settings.auth_cookie_name))
    _clear_session_cookie(response)
    # Returning None keeps FastAPI's declared 204 status while still merging
    # the Set-Cookie header set on the injected response (it clears the
    # browser cookie as well as the server-side session).
    return None


@router.get("/me")
def me(user: dict = Depends(current_user)):
    return {"user": user}


@router.patch("/profile")
def update_profile(payload: ProfileIn, request: Request, user: dict = Depends(current_user)):
    _check_origin(request)
    updated = store.update_user(user["id"], full_name=payload.full_name.strip())
    return {"user": updated}


@router.post("/forgot-password")
def forgot_password(payload: EmailIn, request: Request):
    _check_origin(request)
    _throttle(f"forgot:{_client_ip(request)}")
    email = _clean_email(payload.email)
    if not _valid_email(email):
        raise HTTPException(422, "Enter a valid e-mail address.")
    row = store.find_user_by_email(email)
    sent = False
    if row is not None and row["password_hash"]:
        token = mailer.create_token(row["id"], mailer.PURPOSE_RESET, mailer.RESET_TTL_MINUTES)
        sent = mailer.send(
            email,
            "Reset your password",
            "Use this link to choose a new password:\n\n"
            f"{mailer.reset_url(token)}\n\n"
            f"The link expires in {mailer.RESET_TTL_MINUTES} minutes. "
            "If you did not ask for this, you can ignore this message.",
        )
    # Same answer whether or not the account exists (no account enumeration).
    return {
        "status": "ok",
        "email_sent": sent,
        "email_delivery_configured": settings.email_delivery_configured,
    }


@router.post("/reset-password")
def reset_password(payload: ResetIn, request: Request):
    _check_origin(request)
    _throttle(f"reset:{_client_ip(request)}")
    problems = strength_errors(payload.password)
    if problems:
        raise HTTPException(422, " ".join(problems))
    user_id = mailer.consume_token(payload.token, mailer.PURPOSE_RESET)
    if not user_id:
        raise HTTPException(400, "This reset link is invalid or has expired. Request a new one.")
    store.update_user(user_id, password_hash=hash_password(payload.password))
    sessions.revoke_all_sessions(user_id)
    return {"status": "ok"}


@router.post("/verify-email")
def verify_email(payload: TokenIn, request: Request):
    _check_origin(request)
    user_id = mailer.consume_token(payload.token, mailer.PURPOSE_VERIFY)
    if not user_id:
        raise HTTPException(400, "This confirmation link is invalid or has expired.")
    store.update_user(user_id, email_verified=True)
    return {"status": "ok", "email_verified": True}


@router.get("/verify-email")
def verify_email_link(request: Request, token: str = ""):
    """Target of the link in the verification e-mail."""
    user_id = mailer.consume_token(token, mailer.PURPOSE_VERIFY)
    if not user_id:
        return RedirectResponse(_app_url("/?verify=invalid"), status_code=303)
    store.update_user(user_id, email_verified=True)
    return RedirectResponse(_app_url("/?verify=ok"), status_code=303)


@router.post("/resend-verification")
def resend_verification(request: Request, user: dict = Depends(current_user)):
    _check_origin(request)
    _throttle(f"resend:{user['id']}")
    if user["email_verified"]:
        return {"status": "ok", "email_sent": False, "already_verified": True}
    token = mailer.create_token(user["id"], mailer.PURPOSE_VERIFY, mailer.VERIFY_TTL_MINUTES)
    sent = mailer.send(
        user["email"],
        "Confirm your e-mail address",
        "Confirm your e-mail address to finish setting up your account:\n\n"
        f"{mailer.verification_url(token)}\n",
    )
    return {
        "status": "ok",
        "email_sent": sent,
        "already_verified": False,
        "email_delivery_configured": settings.email_delivery_configured,
    }


# --------------------------------------------------------------------- Google
@router.get("/google/start")
def google_start(request: Request, redirect_to: str = "/", canonical: int = 0):
    if not google.configured():
        return RedirectResponse(_app_url("/?auth_error=google_not_configured"), status_code=303)
    safe_target = redirect_to if redirect_to.startswith("/") else "/"
    # The state cookie is scoped to the host that starts the flow, and Google
    # sends the user back to the registered redirect URI. When the app is
    # opened on another hostname (127.0.0.1 versus localhost, or a preview
    # host), bounce to the canonical origin first so start and callback share
    # one host and the state cookie survives.
    #
    # `canonical=1` marks the bounced request. Honouring it (instead of
    # comparing origins again) guarantees a single hop even when a reverse
    # proxy hides the browser's host from this endpoint; the worst case then is
    # a state-cookie mismatch, which the callback reports instead of looping.
    base = settings.auth_app_base_url.rstrip("/")
    if base and not canonical and _request_origin(request).rstrip("/") != base:
        return RedirectResponse(
            f"{base}/auth/google/start?redirect_to={quote(safe_target, safe='')}&canonical=1",
            status_code=303,
        )
    state, challenge = google.start_flow(safe_target)
    response = RedirectResponse(google.authorize_url(state, challenge), status_code=302)
    response.set_cookie(
        key="etr_oauth_state",
        value=state,
        max_age=900,
        httponly=True,
        samesite="lax",
        secure=settings.auth_cookie_secure or _is_https(request),
        path="/",
    )
    return response


@router.get("/google/callback")
def google_callback(
    request: Request,
    code: str = "",
    state: str = "",
    error: str = "",
):
    """Google redirects here; finish the flow and issue a session."""
    cookie_state = request.cookies.get("etr_oauth_state", "")
    if error:
        # Only echo known OAuth error codes back through the redirect.
        known_errors = {
            "access_denied",
            "server_error",
            "temporarily_unavailable",
            "invalid_request",
            "unauthorized_client",
        }
        code = error if error in known_errors else "failed"
        response = RedirectResponse(_app_url(f"/?auth_error=google_{code}"), status_code=303)
        response.delete_cookie("etr_oauth_state", path="/")
        return response

    if not code or not state or not cookie_state or state != cookie_state:
        response = RedirectResponse(_app_url("/?auth_error=google_state"), status_code=303)
        response.delete_cookie("etr_oauth_state", path="/")
        return response

    verifier = google.consume_state(state)
    if not verifier:
        response = RedirectResponse(_app_url("/?auth_error=google_expired"), status_code=303)
        response.delete_cookie("etr_oauth_state", path="/")
        return response

    try:
        tokens = google.exchange_code(code, verifier)
        profile = google.verify_id_token(tokens["id_token"])
        display_profile = google.fetch_profile(tokens["access_token"])
        if (
            display_profile.get("sub") != profile.get("sub")
            or _clean_email(display_profile.get("email", ""))
            != _clean_email(profile.get("email", ""))
        ):
            raise google.GoogleAuthError("Google returned inconsistent account details.")
        profile.update(
            {
                key: display_profile[key]
                for key in ("name", "picture")
                if display_profile.get(key)
            }
        )
    except google.GoogleAuthError as exc:
        logger.warning("Google sign-in failed: %s", exc)
        response = RedirectResponse(_app_url("/?auth_error=google_failed"), status_code=303)
        response.delete_cookie("etr_oauth_state", path="/")
        return response

    sub = str(profile["sub"])
    email = _clean_email(profile.get("email", ""))
    email_verified = profile.get("email_verified", False)
    if isinstance(email_verified, str):
        email_verified = email_verified.strip().lower() in ("true", "1")
    if not email or not email_verified:
        response = RedirectResponse(_app_url("/?auth_error=google_email"), status_code=303)
        response.delete_cookie("etr_oauth_state", path="/")
        return response

    picture = profile.get("picture", "") or ""
    name = profile.get("name", "") or email.split("@")[0]

    row = store.find_user_by_google_sub(sub)
    if row is not None:
        user = store.update_user(
            row["id"],
            full_name=row["full_name"] or name,
            picture_url=picture or row["picture_url"] or "",
            last_login_at=store.iso(store.utcnow()),
        )
    else:
        existing = store.find_user_by_email(email)
        if existing is not None:
            # Google has verified control of this address, so linking is safe.
            user = store.update_user(
                existing["id"],
                google_sub=sub,
                provider="google",
                email_verified=True,
                picture_url=picture or existing["picture_url"] or "",
                full_name=existing["full_name"] or name,
                last_login_at=store.iso(store.utcnow()),
            )
        else:
            user = store.create_user(
                email=email,
                full_name=name,
                picture_url=picture,
                provider="google",
                google_sub=sub,
                email_verified=True,
            )
            store.update_user(user["id"], last_login_at=store.iso(store.utcnow()))

    token = sessions.create_session(
        user["id"], request.headers.get("user-agent", ""), _client_ip(request)
    )
    response = RedirectResponse(_app_url("/?signed_in=google"), status_code=303)
    _set_session_cookie(response, request, token)
    response.delete_cookie("etr_oauth_state", path="/")
    return response
