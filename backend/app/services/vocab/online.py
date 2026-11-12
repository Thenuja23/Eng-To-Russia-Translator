"""Optional online meaning lookup for words outside the built-in dictionary.

A learner who photographs a page will meet words the curated dictionary does
not contain. When the server has outbound network access we ask a free
translation service for a short gloss (Russian → English, then English →
Sinhala). The lookup is best-effort: no key is required, failures are silent,
results are cached, and the UI labels them as online meanings.
"""
from __future__ import annotations

import re
import threading
import time
from typing import Dict, Tuple

import httpx

from app.core.config import settings

_API = "https://api.mymemory.translated.net/get"
_TTL_SECONDS = 24 * 60 * 60
_MAX_ENTRIES = 2000

_cache: Dict[str, Tuple[float, str]] = {}
_lock = threading.Lock()


def _cached(key: str) -> str:
    with _lock:
        hit = _cache.get(key)
    if not hit:
        return ""
    stored_at, value = hit
    if time.time() - stored_at > _TTL_SECONDS:
        with _lock:
            _cache.pop(key, None)
        return ""
    return value


def _store(key: str, value: str) -> None:
    with _lock:
        if len(_cache) > _MAX_ENTRIES:
            _cache.clear()
        _cache[key] = (time.time(), value)


def _translate(text: str, langpair: str) -> str:
    key = f"{langpair}:{text.lower()}"
    cached = _cached(key)
    if cached:
        return cached
    try:
        with httpx.Client(timeout=settings.vocab_lookup_timeout_seconds) as client:
            response = client.get(_API, params={"q": text, "langpair": langpair})
        if response.status_code >= 400:
            return ""
        data = response.json()
    except Exception:  # noqa: BLE001 - the lookup is optional
        return ""

    value = (((data or {}).get("responseData") or {}).get("translatedText") or "").strip()
    if not value:
        return ""
    lowered = value.lower()
    if "mymemory warning" in lowered or "quota" in lowered:
        return ""
    if lowered == text.lower():
        return ""
    _store(key, value)
    return value


# A translated Sinhala gloss must actually be in Sinhala script; the free
# service sometimes answers with a placeholder or a Latin code name instead.
_SINHALA = re.compile(r"[\u0D80-\u0DFF]")
_LATIN_WORD = re.compile(r"[A-Za-z]{2,}")


def lookup(word: str) -> Tuple[str, str]:
    """Return (english gloss, sinhala gloss). Empty strings mean "unknown"."""
    clean = (word or "").strip()
    if not clean:
        return "", ""
    english = _translate(clean, "ru|en")
    if not english or not _LATIN_WORD.search(english) or len(english) > 80:
        return "", ""
    sinhala = _translate(english, "en|si")
    if not _SINHALA.search(sinhala):
        sinhala = ""
    return english, sinhala


def enabled() -> bool:
    return bool(settings.vocab_online_lookup)
