"""Real authentication: e-mail/password accounts, sessions and Google OAuth.

Security notes
--------------
* Passwords are hashed with scrypt (salted, per user) and never stored or
  returned in plain text.
* Sessions are opaque random tokens. The browser gets one HttpOnly, SameSite=Lax
  cookie; the database stores only a SHA-256 hash of the token.
* Google sign-in is the server-side authorization-code flow with PKCE. The
  client secret stays on the backend and the browser never sees a provider token.
* Users, roles and ids always come from the session, never from the request body.
"""
from __future__ import annotations

import logging
import re
import time
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field

from app.core.config import settings
from app.services.auth import db as store
from app.services.auth import google, mailer, sessions
from app.services.auth.passwords import hash_password, strength_errors, verify_password

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

    forwarded = (request.headers.get("x-forwarded-proto") or "").split(",")[0].strip()
    host = (
        (request.headers.get("x-forwarded-host") or "").split(",")[0].strip()
        or request.headers.get("host", "")
    )
    scheme = forwarded or request.url.scheme
    if host and origin == f"{scheme}://{host}":
        return
    allowed = settings.cors_origin_list
    if origin in allowed:
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
    forwarded = (request.headers.get("x-forwarded-proto") or "").split(",")[0].strip()
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
    forwarded = (request.headers.get("x-forwarded-for") or "").split(",")[0].strip()
    return forwarded or (request.client.host if request.client else "")


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

    user = store.create_user(
        email=email,
        full_name=payload.full_name.strip() or email.split("@")[0],
        password_hash=hash_password(payload.password),
        provider="password",
    )
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
    _throttle(f"login:{email or _client_ip(request)}")
    row = store.find_user_by_email(email)
    if row is None or not row["password_hash"] or not verify_password(
        row["password_hash"], payload.password
    ):
        raise HTTPException(401, "E-mail or password is incorrect.")

    store.update_user(row["id"], last_login_at=store.iso(store.utcnow()))
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
    return Response(status_code=status.HTTP_204_NO_CONTENT)


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
def google_start(request: Request, redirect_to: str = "/"):
    if not google.configured():
        return RedirectResponse(_app_url("/?auth_error=google_not_configured"), status_code=303)
    safe_target = redirect_to if redirect_to.startswith("/") else "/"
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
        response = RedirectResponse(_app_url(f"/?auth_error=google_{error}"), status_code=303)
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
        profile = google.fetch_profile(tokens["access_token"])
    except google.GoogleAuthError as exc:
        logger.warning("Google sign-in failed: %s", exc)
        response = RedirectResponse(_app_url("/?auth_error=google_failed"), status_code=303)
        response.delete_cookie("etr_oauth_state", path="/")
        return response

    sub = str(profile["sub"])
    email = _clean_email(profile.get("email", ""))
    if not email or not profile.get("email_verified", True):
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
