"""End-to-end checks for the authentication flows.

Run from the backend directory:

    PYTHONPATH=. .venv/bin/python scripts/auth_flows_test.py

It uses a temporary SQLite database, so it never touches real accounts.
Google's code exchange is the only step that needs real credentials; the
redirect, cancellation and state-mismatch paths are covered here.
"""
from __future__ import annotations

import os
import tempfile
from urllib.parse import unquote

TMP_DB = os.path.join(tempfile.mkdtemp(prefix="etr-auth-"), "auth.db")
os.environ["AUTH_DB_PATH"] = TMP_DB

from fastapi.testclient import TestClient  # noqa: E402
from starlette.requests import Request  # noqa: E402

from app.core.config import settings  # noqa: E402
from app.api.routes.auth import _client_ip  # noqa: E402
from app.main import app  # noqa: E402
from app.services.auth import db as store  # noqa: E402

settings.auth_db_path = TMP_DB
settings.auth_google_client_id = None
settings.auth_google_client_secret = None
settings.auth_protect_features = False
settings.auth_app_base_url = "http://localhost:3000"
settings.auth_smtp_host = None

PASSED = []
FAILED = []


def check(name: str, condition: bool, detail: str = "") -> None:
    (PASSED if condition else FAILED).append(f"{name}{' — ' + detail if detail and not condition else ''}")
    print(("PASS  " if condition else "FAIL  ") + name + (f"  [{detail}]" if detail and not condition else ""))


def latest_token(purpose: str) -> str:
    """Read the newest unused token for a purpose, as a tester with DB access."""
    import hashlib

    def digest(value: str) -> str:
        return hashlib.sha256(value.encode()).hexdigest()

    # Tokens are stored hashed, so mint a fresh one through the service and use
    # the plaintext it returns (exactly what the e-mail would contain).
    from app.services.auth import mailer

    with store.connect() as connection:
        row = connection.execute(
            "SELECT * FROM auth_tokens WHERE purpose = ? AND used_at IS NULL "
            "ORDER BY created_at DESC LIMIT 1",
            (purpose,),
        ).fetchone()
    return row, digest


def main() -> int:
    def request_with_ip(remote: str, forwarded: str) -> Request:
        return Request(
            {
                "type": "http",
                "http_version": "1.1",
                "method": "GET",
                "scheme": "http",
                "path": "/",
                "query_string": b"",
                "headers": [(b"x-forwarded-for", forwarded.encode())],
                "server": ("test", 80),
                "client": (remote, 1234),
            }
        )

    original_trusted_proxies = settings.auth_trusted_proxy_ips
    settings.auth_trusted_proxy_ips = ""
    direct_ip = _client_ip(request_with_ip("203.0.113.10", "198.51.100.7"))
    check("untrusted X-Forwarded-For cannot spoof the throttle IP", direct_ip == "203.0.113.10")
    settings.auth_trusted_proxy_ips = "10.0.0.0/8"
    proxied_ip = _client_ip(
        request_with_ip("10.0.0.4", "198.51.100.7, 203.0.113.8")
    )
    check("trusted proxy chain ignores caller-prepended spoof", proxied_ip == "203.0.113.8")
    settings.auth_trusted_proxy_ips = original_trusted_proxies

    with TestClient(app) as client:
        # ---------------------------------------------------------- public API
        config = client.get("/auth/config")
        check("config endpoint is public", config.status_code == 200)
        check("google reports unconfigured", config.json()["google_enabled"] is False)

        check("me without a session is 401", client.get("/auth/me").status_code == 401)

        # ------------------------------------------------------------- register
        weak = client.post(
            "/auth/register",
            json={"full_name": "Test", "email": "weak@example.com", "password": "short"},
        )
        check("weak password rejected", weak.status_code == 422, weak.text)

        bad_email = client.post(
            "/auth/register",
            json={"full_name": "Test", "email": "not-an-email", "password": "Password123"},
        )
        check("invalid e-mail rejected", bad_email.status_code == 422, bad_email.text)

        created = client.post(
            "/auth/register",
            json={"full_name": "Ayesha Perera", "email": "Ayesha@Example.com", "password": "Password123"},
        )
        check("registration succeeds", created.status_code == 201, created.text)
        user = created.json()["user"]
        check("e-mail normalised to lowercase", user["email"] == "ayesha@example.com", user.get("email"))
        check("new account starts unverified", user["email_verified"] is False)
        check("no password hash is returned", "password_hash" not in user)
        check("session cookie set", "etr_session" in client.cookies)
        check("email_sent is false without SMTP", created.json()["email_sent"] is False)

        me = client.get("/auth/me")
        check("me works with the session cookie", me.status_code == 200 and me.json()["user"]["id"] == user["id"])

        # Duplicate registration, with a clean client so it is a different caller.
        with TestClient(app) as other:
            duplicate = other.post(
                "/auth/register",
                json={"full_name": "A", "email": "ayesha@example.com", "password": "Password123"},
            )
        check("duplicate e-mail rejected", duplicate.status_code == 409, duplicate.text)

        same_origin_probe = TestClient(app)
        same_origin = same_origin_probe.post(
            "/auth/login",
            json={"email": "ayesha@example.com", "password": "Password123"},
            headers={"Origin": "http://testserver"},
        )
        check("same-origin posts are accepted", same_origin.status_code == 200, same_origin.text)

        # Cross-site form posts are refused.
        with TestClient(app) as evil:
            blocked = evil.post(
                "/auth/login",
                json={"email": "ayesha@example.com", "password": "Password123"},
                headers={"Origin": "http://evil.example"},
            )
        check("foreign Origin rejected", blocked.status_code == 403, blocked.text)

        # ------------------------------------------------------------ e-mail verify
        row, digest = latest_token("verify")
        check("verification token stored", row is not None)
        check("tokens are hashed at rest", row is not None and row["token_hash"] != "plaintext")
        if row is not None:
            with store.connect() as connection:
                connection.execute(
                    "UPDATE auth_tokens SET token_hash = ? WHERE id = ?",
                    (digest("known-verification-token"), row["id"]),
                )
            verified = client.post("/auth/verify-email", json={"token": "known-verification-token"})
            check("verification token accepted", verified.status_code == 200, verified.text)
            again = client.post("/auth/verify-email", json={"token": "known-verification-token"})
            check("verification token is single-use", again.status_code == 400, again.text)
            check("account marked verified", client.get("/auth/me").json()["user"]["email_verified"] is True)

        # ---------------------------------------------------------------- logout
        check("logout returns 204", client.post("/auth/logout").status_code == 204)
        check("me is 401 after logout", client.get("/auth/me").status_code == 401)

        # ----------------------------------------------------------------- login
        wrong = client.post("/auth/login", json={"email": "ayesha@example.com", "password": "WrongPass1"})
        check("wrong password rejected", wrong.status_code == 401, wrong.text)
        unknown = client.post("/auth/login", json={"email": "nobody@example.com", "password": "Password123"})
        check("unknown account rejected generically", unknown.status_code == 401, unknown.text)

        good = client.post("/auth/login", json={"email": "ayesha@example.com", "password": "Password123"})
        check("login succeeds", good.status_code == 200, good.text)
        check("last login recorded", bool(good.json()["user"]["last_login_at"]))
        session_cookie = client.cookies.get("etr_session")
        check("session cookie is opaque", bool(session_cookie) and len(session_cookie) > 20)
        with store.connect() as connection:
            stored = connection.execute("SELECT id FROM sessions").fetchall()
        check(
            "raw session token is not stored",
            all(row_id["id"] != session_cookie for row_id in stored),
        )

        # ------------------------------------------------------- profile update
        renamed = client.patch("/auth/profile", json={"full_name": "Ayesha P."})
        check("profile update works", renamed.status_code == 200 and renamed.json()["user"]["full_name"] == "Ayesha P.")
        check(
            "profile update requires a session",
            TestClient(app).patch("/auth/profile", json={"full_name": "X"}).status_code == 401,
        )

        # ------------------------------------------------------ forgot / reset
        ghost = client.post("/auth/forgot-password", json={"email": "nobody@example.com"})
        check("forgot-password answers for unknown accounts", ghost.status_code == 200)
        real = client.post("/auth/forgot-password", json={"email": "ayesha@example.com"})
        check("forgot-password creates a token", real.status_code == 200 and real.json()["status"] == "ok")

        reset_row, reset_digest = latest_token("reset")
        check("reset token stored", reset_row is not None)
        if reset_row is not None:
            with store.connect() as connection:
                connection.execute(
                    "UPDATE auth_tokens SET token_hash = ? WHERE id = ?",
                    (reset_digest("known-reset-token"), reset_row["id"]),
                )
            weak_reset = client.post(
                "/auth/reset-password", json={"token": "known-reset-token", "password": "abc"}
            )
            check("reset enforces password rules", weak_reset.status_code == 422, weak_reset.text)

            reset = client.post(
                "/auth/reset-password",
                json={"token": "known-reset-token", "password": "NewPassword456"},
            )
            check("reset succeeds", reset.status_code == 200, reset.text)
            check("reset invalidates other sessions", client.get("/auth/me").status_code == 401)
            reused = client.post(
                "/auth/reset-password",
                json={"token": "known-reset-token", "password": "Another789"},
            )
            check("reset token is single-use", reused.status_code == 400, reused.text)

            old_login = client.post(
                "/auth/login", json={"email": "ayesha@example.com", "password": "Password123"}
            )
            check("old password no longer works", old_login.status_code == 401, old_login.text)
            new_login = client.post(
                "/auth/login", json={"email": "ayesha@example.com", "password": "NewPassword456"}
            )
            check("new password works", new_login.status_code == 200, new_login.text)

        # ------------------------------------------------------ expired session
        with store.connect() as connection:
            connection.execute("UPDATE sessions SET expires_at = ?", (store.iso(store.utcnow()),))
        expired_probe = TestClient(app)
        expired_probe.cookies.set(settings.auth_cookie_name, session_cookie)
        check("expired session is rejected", expired_probe.get("/auth/me").status_code == 401)

        # --------------------------------------------------------- Google OAuth
        client.cookies.clear()
        unconfigured = client.get("/auth/google/start", follow_redirects=False)
        check(
            "google start explains missing credentials",
            unconfigured.status_code == 303
            and "auth_error=google_not_configured" in unconfigured.headers.get("location", ""),
            str(unconfigured.headers.get("location")),
        )

        settings.auth_google_client_id = "test-client-id.apps.googleusercontent.com"
        settings.auth_google_client_secret = "test-secret"
        # Use the configured public origin so this exercises the Google
        # authorization redirect itself instead of the canonical-host bounce.
        start = client.get(
            "http://localhost:3000/auth/google/start", follow_redirects=False
        )
        location = start.headers.get("location", "")
        check("google start redirects to Google", start.status_code == 302 and location.startswith("https://accounts.google.com"), location)
        check("google request uses PKCE", "code_challenge_method=S256" in location)
        check(
            "google request carries our redirect URI",
            "/auth/google/callback" in unquote(location),
            unquote(location),
        )
        check("oauth state cookie set", "etr_oauth_state" in client.cookies)

        cancelled = client.get(
            "/auth/google/callback", params={"error": "access_denied", "state": "whatever"},
            follow_redirects=False,
        )
        check(
            "cancelled Google sign-in handled",
            cancelled.status_code == 303 and "google_access_denied" in cancelled.headers.get("location", ""),
            str(cancelled.headers.get("location")),
        )

        mismatch = client.get(
            "/auth/google/callback", params={"code": "abc", "state": "tampered"},
            follow_redirects=False,
        )
        check(
            "tampered OAuth state rejected",
            mismatch.status_code == 303 and "google_state" in mismatch.headers.get("location", ""),
            str(mismatch.headers.get("location")),
        )

        settings.auth_google_client_id = None
        settings.auth_google_client_secret = None

        # ------------------------------------------- optional feature protection
        settings.auth_protect_features = True
        public_probe = TestClient(app)
        check(
            "feature endpoints can require a session",
            public_probe.get("/vocab/status").status_code == 401,
        )
        client.cookies.clear()
        login_again = client.post(
            "/auth/login", json={"email": "ayesha@example.com", "password": "NewPassword456"}
        )
        check(
            "signed-in user can still call features",
            login_again.status_code == 200 and client.get("/vocab/status").status_code == 200,
        )
        settings.auth_protect_features = False

    print()
    print(f"{len(PASSED)} passed, {len(FAILED)} failed")
    if FAILED:
        print("\nFailures:")
        for item in FAILED:
            print(" -", item)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
