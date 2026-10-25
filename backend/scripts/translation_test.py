#!/usr/bin/env python3
"""Tests for Google Translate, Auto/Hybrid selection, fallback and caching.

No network access and no API key are needed: fake providers simulate Google and
the local Opus-MT engine, including placeholder loss and network errors.

Run:  cd backend && PYTHONPATH=. python3 scripts/translation_test.py
"""
from __future__ import annotations

import os
import re
import sys
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes import translation as translation_route
from app.services.translation.base import TranslationResult
from app.services.translation.google_translate import GoogleTranslateTranslator
from app.services.translation.token_protector import TokenProtector
from app.services.translation.translator_service import TranslationService

PASSED = 0
FAILED = 0
FAILURES = []


def check(name, fn):
    global PASSED, FAILED
    try:
        fn()
    except Exception as exc:  # noqa: BLE001
        FAILED += 1
        FAILURES.append((name, exc))
        print(f"FAIL  {name}\n      {type(exc).__name__}: {exc}")
    else:
        PASSED += 1
        print(f"PASS  {name}")


# --------------------------------------------------------------------------- #
# fakes
# --------------------------------------------------------------------------- #

class FakeGoogle(GoogleTranslateTranslator):
    """Google stand-in. Keeps placeholders unless ``drop`` is requested."""

    def __init__(self, drop=False, fail=False, text_fn=None):
        super().__init__(api_key="fake-key")
        self.calls = []
        self.drop = drop
        self.fail = fail
        self.text_fn = text_fn

    def _request_batch(self, pieces, src, tgt):
        self.calls.append(list(pieces))
        if self.fail:
            raise RuntimeError("simulated Google outage")
        out = []
        for piece in pieces:
            if self.text_fn is not None:
                translated = self.text_fn(piece, src, tgt)
            else:
                prefix = "ПЕРЕВОД " if src == "en" else "TRANSLATED "
                translated = prefix + piece
            if self.drop:
                translated = re.sub(r"GTR0*\d+", "", translated)
            out.append(translated)
        return out


class FakeLocal:
    """Offline engine stand-in."""

    def __init__(self, text_fn=None, fail=False):
        self.text_fn = text_fn or (lambda text: "ПРИВЕТ " + text)
        self.fail = fail
        self.calls = 0

    def supports(self, src_lang, tgt_lang):
        return True

    def translate(self, text, src_lang="ru", tgt_lang="en", **kwargs):
        self.calls += 1
        if self.fail:
            return TranslationResult(
                text=text,
                confidence=0.0,
                meta={"engine": "opustmt", "error": "simulated local failure"},
            )
        return TranslationResult(
            text=self.text_fn(text),
            confidence=0.9,
            meta={"engine": "opustmt", "all_placeholders_restored": True},
        )


def make_service(google=None, local=None):
    service = TranslationService()
    if google is not None:
        service._translators["google"] = google
        service._enabled["google"] = True
    if local is not None:
        service._translators["opustmt"] = local
        service._enabled["opustmt"] = True
    return service


# --------------------------------------------------------------------------- #
# Google client
# --------------------------------------------------------------------------- #

def test_google_basic_and_tokens():
    google = FakeGoogle()
    text = "Email anna@example.com before 15.10.2026 about CS-101."
    result = google.translate(text, "en", "ru")
    assert result.meta["engine"] == "google"
    assert result.meta["all_placeholders_restored"] is True
    for value in ("anna@example.com", "15.10.2026", "CS-101"):
        assert value in result.text, result.text


def test_google_batches_sentences():
    google = FakeGoogle()
    google.translate("Hello. Thank you. Goodbye.", "en", "ru")
    assert len(google.calls) == 1, google.calls
    assert len(google.calls[0]) == 3, google.calls


def test_google_recovers_lost_placeholders():
    google = FakeGoogle(drop=True)
    text = "Email anna@example.com before 15.10.2026 about CS-101."
    result = google.translate(text, "en", "ru")
    assert result.meta["placeholder_strategy"] == "segmented", result.meta
    assert result.meta["all_placeholders_restored"] is True
    for value in ("anna@example.com", "15.10.2026", "CS-101"):
        assert value in result.text, result.text


def test_google_failure_is_reported_not_raised():
    result = FakeGoogle(fail=True).translate("Hello world", "en", "ru")
    assert "error" in result.meta
    assert "simulated Google outage" in result.meta["error"]


def test_google_not_configured():
    result = GoogleTranslateTranslator(api_key="").translate("Hello", "en", "ru")
    assert result.meta.get("not_configured") is True
    assert "GOOGLE_TRANSLATE_API_KEY" in result.meta["error"]


def test_google_http_retry_and_key_header():
    class Response:
        def __init__(self, status, payload=None, text="", headers=None):
            self.status_code = status
            self._payload = payload or {}
            self.text = text
            self.headers = headers or {}

        def json(self):
            return self._payload

    class Client:
        def __init__(self, responses):
            self.responses = list(responses)
            self.calls = []

        def post(self, url, json=None, headers=None):
            self.calls.append({"url": url, "json": json, "headers": headers})
            return self.responses.pop(0)

    google = GoogleTranslateTranslator(api_key="secret-key")
    client = Client(
        [
            Response(429, text="quota", headers={"Retry-After": "0"}),
            Response(200, payload={"data": {"translations": [{"translatedText": "Привет"}]}}),
        ]
    )
    google._client = client
    with patch("app.services.translation.google_translate.time.sleep", lambda *_: None):
        out = google._request_batch(["Hello"], "en", "ru")
    assert out == ["Привет"]
    assert len(client.calls) == 2
    assert client.calls[0]["headers"]["X-goog-api-key"] == "secret-key"
    assert client.calls[0]["json"]["q"] == ["Hello"]
    assert client.calls[0]["json"]["format"] == "text"


def test_google_error_does_not_leak_key():
    class Response:
        status_code = 400
        text = "bad request"
        headers = {}

        def json(self):
            return {}

    class Client:
        def post(self, *args, **kwargs):
            return Response()

    google = GoogleTranslateTranslator(api_key="super-secret")
    google._client = Client()
    try:
        google._request_batch(["Hello"], "en", "ru")
    except RuntimeError as exc:
        assert "super-secret" not in str(exc), str(exc)
    else:
        raise AssertionError("expected RuntimeError")


# --------------------------------------------------------------------------- #
# service: auto / hybrid / fallback / cache
# --------------------------------------------------------------------------- #

def test_auto_prefers_google():
    service = make_service(google=FakeGoogle(), local=FakeLocal())
    result = service.translate("Hello world", "en", "ru", engine="auto")
    assert result.meta["engine"] == "google", result.meta


def test_hybrid_rejects_repetitive_google_output():
    # Google repeats itself (a real failure mode of neural MT) while the
    # offline result is complete. The quality vote must choose the offline one.
    google = FakeGoogle(
        text_fn=lambda piece, src, tgt: "Привет. Привет. Привет. Привет. Привет."
    )
    local = FakeLocal(text_fn=lambda text: "Привет. Спасибо. До свидания. До встречи.")
    service = make_service(google=google, local=local)
    result = service.translate(
        "Hello. Thank you. Goodbye. See you.", "en", "ru", engine="hybrid"
    )
    assert result.meta["engine"] == "hybrid", result.meta
    assert result.meta["chosen_engine"] == "opustmt", result.meta
    assert "Спасибо" in result.text, result.text


def test_hybrid_keeps_google_when_it_is_better():
    google = FakeGoogle(text_fn=lambda piece, src, tgt: "Привет. Спасибо.")
    local = FakeLocal(text_fn=lambda text: "Привет.")
    service = make_service(google=google, local=local)
    result = service.translate("Hello. Thank you.", "en", "ru", engine="hybrid")
    assert result.meta["chosen_engine"] == "google", result.meta
    assert "Спасибо" in result.text, result.text


def test_explicit_offline_never_calls_google():
    google = FakeGoogle()
    local = FakeLocal()
    service = make_service(google=google, local=local)
    result = service.translate("Hello", "en", "ru", engine="opustmt")
    assert result.meta["engine"] == "opustmt"
    assert google.calls == [], google.calls
    assert local.calls == 1


def test_auto_falls_back_to_offline_when_google_fails():
    google = FakeGoogle(fail=True)
    local = FakeLocal()
    service = make_service(google=google, local=local)
    result = service.translate("A brand new sentence", "en", "ru", engine="auto")
    assert result.meta["engine"] == "opustmt", result.meta
    assert "primary_error" in result.meta
    assert "simulated Google outage" in result.meta["primary_error"]


def test_unknown_engine_falls_back_with_note():
    service = make_service(google=FakeGoogle(), local=FakeLocal())
    result = service.translate("Hello", "en", "ru", engine="does-not-exist")
    assert result.meta["engine"] == "opustmt", result.meta
    assert result.meta["requested_engine"] == "does-not-exist"


def test_translation_cache_avoids_duplicate_google_calls():
    google = FakeGoogle()
    service = make_service(google=google, local=FakeLocal())
    first = service.translate("Cached sentence", "en", "ru", engine="auto")
    second = service.translate("Cached sentence", "en", "ru", engine="auto")
    assert first.meta.get("cached") is not True
    assert second.meta.get("cached") is True
    assert len(google.calls) == 1, google.calls


def test_failed_google_is_not_cached():
    google = FakeGoogle(fail=True)
    local = FakeLocal()
    service = make_service(google=google, local=local)
    first = service.translate("No cache on failure", "en", "ru", engine="auto")
    second = service.translate("No cache on failure", "en", "ru", engine="auto")
    assert first.meta.get("cached") is not True
    assert second.meta.get("cached") is not True
    assert len(google.calls) >= 4, google.calls  # both requests retried Google


def test_engine_details_include_google_status():
    service = make_service(google=FakeGoogle(), local=FakeLocal())
    details = {item["id"]: item for item in service.get_engine_details()}
    assert details["auto"]["resolved"] == "google"
    assert details["google"]["available"] is True
    assert details["hybrid"]["available"] is True
    assert details["opustmt"]["available"] is True
    assert details["fallback"]["available"] is True


def test_token_protector_tolerates_case_space_and_padding():
    protector = TokenProtector(prefix="ZXQ")
    mapping = {"ZXQ0001": "anna@example.com", "ZXQ0002": "15:30"}
    restored, ok = protector.restore("email zxq 0001 at ZXQ 002", mapping)
    assert ok
    assert restored == "email anna@example.com at 15:30"


def test_token_protector_avoids_tolerant_collision():
    protector = TokenProtector(prefix="ZXQ")
    protected, mapping = protector.protect(
        "Email anna@example.com about ZXQ0001"
    )
    # The user's literal look-alike must survive and the generated key must
    # skip the tolerant form (ZXQ 0001, zxq0001, ZXQ001, ...).
    assert "ZXQ0001" not in mapping
    assert mapping.get("ZXQ0002") == "anna@example.com", mapping
    restored, ok = protector.restore(protected, mapping)
    assert ok
    assert "anna@example.com" in restored
    assert "ZXQ0001" in restored


def test_token_protector_keeps_plain_course_codes():
    protector = TokenProtector(prefix="ZXQ")
    _, mapping = protector.protect("My course CS101 starts with COVID19")
    assert "CS101" in mapping.values(), mapping
    assert "COVID19" in mapping.values(), mapping
    # A normal capitalised word with digits must still be translatable.
    _, plain_words = protector.protect("Hello123")
    assert not plain_words, plain_words


# --------------------------------------------------------------------------- #
# route
# --------------------------------------------------------------------------- #

def test_engines_route_shape():
    app = FastAPI()
    app.include_router(translation_route.router)
    client = TestClient(app)
    response = client.get("/translation/engines")
    assert response.status_code == 200
    body = response.json()
    assert "opustmt" in body["engines"]
    assert isinstance(body["details"], list)
    assert "google_configured" in body
    assert all("available" in item for item in body["details"])


def main():
    tests = [
        ("Google basic translation + token protection", test_google_basic_and_tokens),
        ("Google batches sentences into one request", test_google_batches_sentences),
        ("Google recovers lost placeholders via segmented retry", test_google_recovers_lost_placeholders),
        ("Google failure is reported, not raised", test_google_failure_is_reported_not_raised),
        ("Google without a key reports setup guidance", test_google_not_configured),
        ("Google retries 429 and sends the key in a header", test_google_http_retry_and_key_header),
        ("Google error text never leaks the API key", test_google_error_does_not_leak_key),
        ("Auto mode prefers Google", test_auto_prefers_google),
        ("Hybrid rejects repetitive Google output", test_hybrid_rejects_repetitive_google_output),
        ("Hybrid keeps Google when it is better", test_hybrid_keeps_google_when_it_is_better),
        ("Explicit offline mode never calls Google", test_explicit_offline_never_calls_google),
        ("Auto falls back to offline on Google failure", test_auto_falls_back_to_offline_when_google_fails),
        ("Unknown engine falls back with a note", test_unknown_engine_falls_back_with_note),
        ("Translation cache avoids duplicate Google calls", test_translation_cache_avoids_duplicate_google_calls),
        ("Failed Google calls are not cached", test_failed_google_is_not_cached),
        ("Engine details expose Google availability", test_engine_details_include_google_status),
        ("Token restore tolerates case/space/padding", test_token_protector_tolerates_case_space_and_padding),
        ("Token keys avoid tolerant collisions", test_token_protector_avoids_tolerant_collision),
        ("Token protector keeps plain course codes", test_token_protector_keeps_plain_course_codes),
        ("GET /translation/engines includes details", test_engines_route_shape),
    ]
    for name, fn in tests:
        check(name, fn)

    print()
    print(f"{PASSED} passed, {FAILED} failed")
    if FAILURES:
        print("\nFailures:")
        for name, exc in FAILURES:
            print(f"- {name}: {type(exc).__name__}: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
