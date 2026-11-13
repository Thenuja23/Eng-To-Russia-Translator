"""Password hashing and strength rules (standard library only).

Primary scheme is scrypt, which is memory-hard and preferred. Some Python
builds (notably macOS system Python linked against LibreSSL) do not ship
``hashlib.scrypt``; for those we fall back to PBKDF2-HMAC-SHA256 with a high
iteration count. Both formats are tagged, so existing hashes keep verifying
and a database can be moved between environments.
"""
from __future__ import annotations

import hashlib
import hmac
import secrets
from typing import List

_SCRYPT_N = 2 ** 14
_SCRYPT_R = 8
_SCRYPT_P = 1
_KEY_LEN = 64
_MAX_LENGTH = 128

# OWASP's 2023+ recommendation for PBKDF2-HMAC-SHA256.
_PBKDF2_ITERATIONS = 600_000
_PBKDF2_DKLEN = 32

_SCRYPT_PREFIX = "scrypt$"
_PBKDF2_PREFIX = "pbkdf2_sha256$"


def scrypt_available() -> bool:
    """True when the running OpenSSL exposes scrypt to hashlib."""
    return hasattr(hashlib, "scrypt")


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    if scrypt_available():
        digest = hashlib.scrypt(
            (password or "").encode("utf-8"),
            salt=salt,
            n=_SCRYPT_N,
            r=_SCRYPT_R,
            p=_SCRYPT_P,
            dklen=_KEY_LEN,
        )
        return "scrypt${}${}${}${}${}".format(
            _SCRYPT_N, _SCRYPT_R, _SCRYPT_P, salt.hex(), digest.hex()
        )

    digest = hashlib.pbkdf2_hmac(
        "sha256",
        (password or "").encode("utf-8"),
        salt,
        _PBKDF2_ITERATIONS,
        dklen=_PBKDF2_DKLEN,
    )
    return f"{_PBKDF2_PREFIX}{_PBKDF2_ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(stored: str, password: str) -> bool:
    if not stored:
        return False
    try:
        if stored.startswith(_SCRYPT_PREFIX):
            if not scrypt_available():
                # Cannot verify a scrypt hash on a build without scrypt. This
                # only happens when the database was created elsewhere; new
                # hashes use PBKDF2 on such builds.
                return False
            _, n, r, p, salt_hex, digest_hex = stored.split("$")
            digest = hashlib.scrypt(
                (password or "").encode("utf-8"),
                salt=bytes.fromhex(salt_hex),
                n=int(n),
                r=int(r),
                p=int(p),
                dklen=len(bytes.fromhex(digest_hex)),
            )
            return hmac.compare_digest(digest.hex(), digest_hex)

        if stored.startswith(_PBKDF2_PREFIX):
            _, iterations, salt_hex, digest_hex = stored.split("$")
            digest = hashlib.pbkdf2_hmac(
                "sha256",
                (password or "").encode("utf-8"),
                bytes.fromhex(salt_hex),
                int(iterations),
                dklen=len(bytes.fromhex(digest_hex)),
            )
            return hmac.compare_digest(digest.hex(), digest_hex)
    except (ValueError, TypeError):
        return False
    return False


def needs_rehash(stored: str) -> bool:
    """True when a stored hash should be upgraded to the preferred scheme.

    A PBKDF2 hash on a build that supports scrypt is upgraded on the next
    successful sign-in; malformed or unknown formats are also replaced.
    """
    if not stored:
        return True
    if stored.startswith(_SCRYPT_PREFIX):
        return not scrypt_available()
    if stored.startswith(_PBKDF2_PREFIX):
        return scrypt_available()
    return True


def strength_errors(password: str) -> List[str]:
    """Plain-language reasons a password is not acceptable yet."""
    value = password or ""
    errors: List[str] = []
    if len(value) < 8:
        errors.append("Use at least 8 characters.")
    if len(value) > _MAX_LENGTH:
        errors.append("Use at most 128 characters.")
    if not any(ch.isalpha() for ch in value):
        errors.append("Include at least one letter.")
    if not any(ch.isdigit() for ch in value):
        errors.append("Include at least one number.")
    if value.lower() in {"password", "password1", "12345678", "qwerty123"}:
        errors.append("This password is too common.")
    return errors


def strength_score(password: str) -> int:
    """0-4 score used by the frontend meter."""
    value = password or ""
    if not value:
        return 0
    score = 0
    if len(value) >= 8:
        score += 1
    if len(value) >= 12:
        score += 1
    if any(ch.isdigit() for ch in value) and any(ch.isalpha() for ch in value):
        score += 1
    if any(not ch.isalnum() for ch in value) or any(ch.isupper() for ch in value):
        score += 1
    return min(4, score)
