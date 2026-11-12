"""Password hashing and strength rules (standard library only)."""
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


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=_SCRYPT_N,
        r=_SCRYPT_R,
        p=_SCRYPT_P,
        dklen=_KEY_LEN,
    )
    return "scrypt${}${}${}${}${}".format(
        _SCRYPT_N, _SCRYPT_R, _SCRYPT_P, salt.hex(), digest.hex()
    )


def verify_password(stored: str, password: str) -> bool:
    if not stored or not stored.startswith("scrypt$"):
        return False
    try:
        _, n, r, p, salt_hex, digest_hex = stored.split("$")
        digest = hashlib.scrypt(
            (password or "").encode("utf-8"),
            salt=bytes.fromhex(salt_hex),
            n=int(n),
            r=int(r),
            p=int(p),
            dklen=len(bytes.fromhex(digest_hex)),
        )
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(digest.hex(), digest_hex)


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
