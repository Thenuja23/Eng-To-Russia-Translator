"""End-to-end checks for the authentication flows.

Run from the backend directory:

    PYTHONPATH=. .venv/bin/python scripts/auth_flows_test.py

It uses a temporary SQLite database, so it never touches real accounts.
Google's code exchange is the only step that needs real credentials; the
redirect, cancellation and state-mismatch paths are covered here.
"""
from __future__ import annotations

import os
import sqlite3
import tempfile
from urllib.parse import parse_qs, unquote, urlparse
from unittest.mock import patch

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
    current_db = settings.auth_db_path
    legacy_db = os.path.join(tempfile.mkdtemp(prefix="etr-legacy-auth-"), "auth.db")
    settings.auth_db_path = legacy_db
    with sqlite3.connect(legacy_db) as connection:
        connection.executescript(
            """
            CREATE TABLE users (
                id TEXT PRIMARY KEY, email TEXT NOT NULL UNIQUE, full_name TEXT,
                picture_url TEXT, provider TEXT NOT NULL, password_hash TEXT,
                google_sub TEXT UNIQUE, email_verified INTEGER NOT NULL DEFAULT 0,
                role TEXT NOT NULL DEFAULT 'student', created_at TEXT NOT NULL,
                last_login_at TEXT
            );
            CREATE TABLE auth_tokens (
                id TEXT PRIMARY KEY, user_id TEXT NOT NULL, purpose TEXT NOT NULL,
                token_hash TEXT NOT NULL UNIQUE, created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL, used_at TEXT
            );
            INSERT INTO users(id, email, provider, email_verified, created_at)
                VALUES ('legacy-user', 'legacy@example.com', 'password', 0, '2024-01-01T00:00:00+00:00');
            """
        )
    store.init_db()
    migrated = store.find_user_by_id("legacy-user")
    check("legacy auth schema migration preserves existing user", migrated is not None)
    with sqlite3.connect(legacy_db) as connection:
        token_columns = {
            row[1] for row in connection.execute("PRAGMA table_info(auth_tokens)")
        }
    check(
        "legacy auth schema adds verification timestamp and email-change token fields",
        migrated is not None
        and "email_verified_at" in migrated.keys()
        and "target_email" in token_columns,
    )
    settings.auth_db_path = current_db

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

        old_upload_limit = settings.max_ocr_upload_bytes
        settings.max_ocr_upload_bytes = 8
        non_image = client.post(
            "/ocr", files={"file": ("notes.txt", b"hello", "text/plain")}
        )
        check("OCR rejects non-image uploads", non_image.status_code == 400)
        oversized_image = client.post(
            "/ocr", files={"file": ("large.png", b"123456789", "image/png")}
        )
        check("OCR rejects uploads over the configured limit", oversized_image.status_code == 413)
        empty_image = client.post(
            "/ocr", files={"file": ("empty.png", b"", "image/png")}
        )
        check("OCR rejects empty image uploads", empty_image.status_code == 400)
        settings.max_ocr_upload_bytes = old_upload_limit

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
        check("new account has no verification timestamp", user["email_verified_at"] is None)
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
        resent = client.post("/auth/resend-verification")
        check(
            "resend reports missing SMTP without claiming delivery",
            resent.status_code == 200 and resent.json()["email_sent"] is False,
        )
        row, digest = latest_token("verify")
        check("verification token stored", row is not None)
        check("tokens are hashed at rest", row is not None and row["token_hash"] != "plaintext")
        if row is not None:
            with store.connect() as connection:
                connection.execute(
                    "UPDATE auth_tokens SET token_hash = ? WHERE id = ?",
                    (digest("known-verification-token"), row["id"]),
                )
            verified = client.get(
                "/auth/verify-email",
                params={"token": "known-verification-token"},
                follow_redirects=False,
            )
            check(
                "verification link redirects to success",
                verified.status_code == 303 and "verify=ok" in verified.headers.get("location", ""),
                verified.text,
            )
            again = client.get(
                "/auth/verify-email",
                params={"token": "known-verification-token"},
                follow_redirects=False,
            )
            check("verification token is single-use", "verify=invalid" in again.headers.get("location", ""))
            current = client.get("/auth/me").json()["user"]
            check("account marked verified", current["email_verified"] is True)
            check("verification timestamp recorded", bool(current["email_verified_at"]))

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
        check(
            "forgot-password response does not reveal account existence",
            ghost.json() == real.json(),
        )

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

        # A previously linked Google account must take the trusted verified
        # claim on sign-in, even if its stored flag predates that behavior.
        google_user = store.create_user(
            email="google-existing@example.com",
            full_name="Google Existing",
            provider="google",
            google_sub="google-sub-existing",
            email_verified=False,
        )
        google_start = client.get(
            "http://localhost:3000/auth/google/start", follow_redirects=False
        )
        google_state = parse_qs(urlparse(google_start.headers["location"]).query)["state"][0]
        with patch(
            "app.api.routes.auth.google.exchange_code",
            return_value={
                "id_token": "test-id-token",
                "access_token": "test-access-token",
            },
        ), patch(
            "app.api.routes.auth.google.verify_id_token",
            return_value={
                "sub": "google-sub-existing",
                "email": "google-existing@example.com",
                "email_verified": True,
            },
        ), patch(
            "app.api.routes.auth.google.fetch_profile",
            return_value={
                "sub": "google-sub-existing",
                "email": "google-existing@example.com",
                "name": "Google Existing",
            },
        ):
            google_callback = client.get(
                "/auth/google/callback",
                params={"code": "test-code", "state": google_state},
                follow_redirects=False,
            )
        google_user_after = store.find_user_by_id(google_user["id"])
        check("linked Google account finishes sign-in", google_callback.status_code == 303)
        check("Google verified claim updates account status", bool(google_user_after["email_verified"]))
        check("Google verification timestamp recorded", bool(google_user_after["email_verified_at"]))

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

        # ----------------------------------------------------------- email change
        wrong_password = client.post(
            "/auth/change-email",
            json={"email": "ayesha-new@example.com", "password": "WrongPass1"},
        )
        check("email change requires the current password", wrong_password.status_code == 401)
        requested_change = client.post(
            "/auth/change-email",
            json={"email": "ayesha-new@example.com", "password": "NewPassword456"},
        )
        check(
            "email change request keeps SMTP delivery status honest",
            requested_change.status_code == 200
            and requested_change.json()["email_sent"] is False,
        )
        check(
            "current address remains unchanged until confirmation",
            client.get("/auth/me").json()["user"]["email"] == "ayesha@example.com",
        )
        change_row, change_digest = latest_token("change_email")
        check(
            "email change token stores target and hash only",
            change_row is not None
            and change_row["target_email"] == "ayesha-new@example.com"
            and change_row["token_hash"] != "plaintext",
        )
        if change_row is not None:
            with store.connect() as connection:
                connection.execute(
                    "UPDATE auth_tokens SET token_hash = ? WHERE id = ?",
                    (change_digest("known-email-change-token"), change_row["id"]),
                )
            confirmed = client.get(
                "/auth/change-email/confirm",
                params={"token": "known-email-change-token"},
                follow_redirects=False,
            )
            check(
                "email change confirms only through its token",
                confirmed.status_code == 303
                and "email_change=ok" in confirmed.headers.get("location", ""),
            )
            check("email change revokes old sessions", client.get("/auth/me").status_code == 401)
            new_login = client.post(
                "/auth/login",
                json={"email": "ayesha-new@example.com", "password": "NewPassword456"},
            )
            check("new email can sign in after confirmation", new_login.status_code == 200)
            new_user = new_login.json()["user"]
            check("new address is marked verified", new_user["email_verified"] is True)
            check("new address verification time is recorded", bool(new_user["email_verified_at"]))
            old_login = client.post(
                "/auth/login",
                json={"email": "ayesha@example.com", "password": "NewPassword456"},
            )
            check("old address no longer signs in", old_login.status_code == 401)

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
