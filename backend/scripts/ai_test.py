#!/usr/bin/env python3
"""Tests for the optional multi-provider AI ensemble.

No network and no API keys are required: fake providers simulate OpenAI,
Claude and Perplexity, including a provider that loses a protected token.

Run:  cd backend && PYTHONPATH=. python3 scripts/ai_test.py
"""
from __future__ import annotations

import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes import ai as ai_route
from app.services.ai.cache import TTLCache
from app.services.ai.ensemble import AiError, AiNotConfigured, Ensemble
from app.services.ai.ratelimit import SlidingWindowLimiter

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


class FakeProvider:
    """Duck-typed stand-in for providers.Provider."""

    def __init__(self, name, model, reply=None, configured=True, fail=False):
        self.name = name
        self.model = model
        self.reply = reply
        self._configured = configured
        self.fail = fail
        self.calls = 0
        self.prompts = []

    @property
    def configured(self):
        return self._configured

    def describe(self, priority):
        return {
            "name": self.name,
            "model": self.model,
            "configured": self._configured,
            "priority": priority,
        }

    def complete(self, system, user, max_tokens=900, temperature=None):
        self.calls += 1
        self.prompts.append(user)
        if self.fail:
            raise RuntimeError("simulated network failure")
        return self.reply(system, user) if callable(self.reply) else self.reply


def keys_in(user):
    return re.findall(r"AIT\d{4}", user)


def fresh_cache():
    return TTLCache(ttl_seconds=60, maxsize=8)


# --------------------------------------------------------------------------- #
# ensemble behaviour
# --------------------------------------------------------------------------- #

def translate_uses_consensus_and_protects_tokens():
    def keep_keys(system, user):
        return "Напишите на " + " и ".join(keys_in(user)) + " сегодня."

    providers = [
        FakeProvider("openai", "gpt-test", keep_keys),
        FakeProvider("anthropic", "claude-test", keep_keys),
        FakeProvider("perplexity", "sonar-test", "Привет."),  # loses tokens
    ]
    ens = Ensemble(providers=providers, cache=fresh_cache())
    res = ens.translate("Email anna@example.com about 2026.", "en", "ru")

    assert "anna@example.com" in res["translated_text"], res["translated_text"]
    assert res["tokens_preserved"] is True
    assert res["provider"] in ("openai", "anthropic"), res["provider"]
    assert res["providers_used"] == 2  # perplexity lost its token and is excluded

    perp = [c for c in res["candidates"] if c["provider"] == "perplexity"][0]
    assert "lost protected token" in perp["error"], perp
    assert perp["tokens_preserved"] is False

    # The raw e-mail must never leave the backend.
    for p in providers:
        for prompt in p.prompts:
            assert "anna@example.com" not in prompt


def translate_rejects_all_token_loss():
    providers = [
        FakeProvider("openai", "gpt-test", "Привет."),
        FakeProvider("anthropic", "claude-test", "Здравствуйте."),
    ]
    ens = Ensemble(providers=providers, cache=fresh_cache())
    try:
        ens.translate("Email anna@example.com now", "en", "ru")
    except AiError as exc:
        assert "token" in str(exc).lower()
    else:
        raise AssertionError("expected AiError when every provider loses a token")


def translate_scores_sentence_completeness():
    def one_sentence(system, user):
        return "Привет."

    def three_sentences(system, user):
        return "Привет. Как дела? Хорошо."

    providers = [
        FakeProvider("openai", "m", one_sentence),
        FakeProvider("anthropic", "m", three_sentences),
    ]
    ens = Ensemble(providers=providers, cache=fresh_cache())
    res = ens.translate("Hello. How are you? Fine.", "en", "ru")
    assert res["provider"] == "anthropic", res["candidates"]
    assert len(res["text"].split(".")) >= 3


def enhance_masks_tokens_in_source_and_translation():
    captured = {}

    def reply(system, user):
        captured["user"] = user
        return "Улучшено: " + " ".join(sorted(set(keys_in(user))))

    ens = Ensemble(
        providers=[FakeProvider("openai", "m", reply)], cache=fresh_cache()
    )
    res = ens.enhance(
        "Email anna@example.com today.",
        "Напишите на anna@example.com сегодня.",
        "en",
        "ru",
    )
    assert "anna@example.com" in res["improved_text"]
    assert res["tokens_preserved"] is True
    assert "anna@example.com" not in captured["user"]
    # Shared tokens reuse one placeholder instead of two competing ones.
    assert len(set(keys_in(captured["user"]))) == 1, keys_in(captured["user"])


def explain_returns_best_rich_answer():
    short = FakeProvider("openai", "m", "Hello.")
    rich = FakeProvider("anthropic", "m", "Meaning\nHello.\n\nGrammar\nNo grammar here.\n\nWatch out\nStress is on the first syllable.")
    ens = Ensemble(providers=[short, rich], cache=fresh_cache())
    res = ens.explain("Привет", "Hello", "ru", "en")
    assert res["provider"] == "anthropic", res["candidates"]
    assert "Meaning" in res["explanation"]


def cache_avoids_duplicate_api_calls():
    provider = FakeProvider(
        "openai", "m", lambda s, u: "Привет. " + " ".join(keys_in(u))
    )
    ens = Ensemble(providers=[provider], cache=fresh_cache())
    first = ens.translate("Hello", "en", "ru")
    calls_after_first = provider.calls
    second = ens.translate("Hello", "en", "ru")
    assert first["cached"] is False
    assert second["cached"] is True
    assert provider.calls == calls_after_first


def not_configured_raises():
    provider = FakeProvider("openai", "m", "x", configured=False)
    ens = Ensemble(providers=[provider], cache=fresh_cache())
    try:
        ens.translate("Hello", "en", "ru")
    except AiNotConfigured as exc:
        assert "OPENAI_API_KEY" in str(exc)
    else:
        raise AssertionError("expected AiNotConfigured")


def status_reports_capabilities():
    ens = Ensemble(
        providers=[
            FakeProvider("openai", "gpt-test", "x"),
            FakeProvider("anthropic", "claude-test", "x", configured=False),
            FakeProvider("perplexity", "sonar-test", "x"),
        ],
        cache=fresh_cache(),
    )
    status = ens.status()
    assert status["configured"] == 2
    assert status["mode"] == "ensemble"
    assert [p["name"] for p in status["providers"]] == [
        "openai",
        "anthropic",
        "perplexity",
    ]
    assert status["setup"] == []


def failed_provider_is_reported_not_fatal():
    providers = [
        FakeProvider("openai", "m", fail=True),
        FakeProvider("anthropic", "m", lambda s, u: "Привет"),
    ]
    ens = Ensemble(providers=providers, cache=fresh_cache())
    res = ens.translate("Hello", "en", "ru")
    assert res["provider"] == "anthropic"
    errors = [c["error"] for c in res["candidates"] if c["error"]]
    assert errors and "simulated network failure" in errors[0]


# --------------------------------------------------------------------------- #
# HTTP endpoints
# --------------------------------------------------------------------------- #

def endpoint_suite():
    app = FastAPI()
    app.include_router(ai_route.router)

    def keep_keys(system, user):
        return "Напишите на " + " и ".join(keys_in(user)) + " сегодня."

    good = Ensemble(
        providers=[
            FakeProvider("openai", "gpt-test", keep_keys),
            FakeProvider("anthropic", "claude-test", keep_keys),
        ],
        cache=fresh_cache(),
    )
    ai_route.ensemble = good
    ai_route.limiter = SlidingWindowLimiter(100)

    client = TestClient(app)

    status = client.get("/ai/status")
    assert status.status_code == 200, status.text
    body = status.json()
    assert body["mode"] == "ensemble"
    assert len(body["providers"]) == 2

    tr = client.post(
        "/ai/translate",
        json={"text": "Email anna@example.com today", "src_lang": "en", "tgt_lang": "ru"},
    )
    assert tr.status_code == 200, tr.text
    data = tr.json()
    assert "anna@example.com" in data["translated_text"]
    assert data["tokens_preserved"] is True
    assert len(data["candidates"]) == 2

    ex = client.post(
        "/ai/explain",
        json={"text": "Привет", "translation": "Hello", "src_lang": "ru", "tgt_lang": "en"},
    )
    assert ex.status_code == 200, ex.text
    assert ex.json()["explanation"]

    enh = client.post(
        "/ai/enhance",
        json={
            "text": "Email anna@example.com today",
            "translation": "Напишите на anna@example.com сегодня",
            "src_lang": "en",
            "tgt_lang": "ru",
        },
    )
    assert enh.status_code == 200, enh.text
    assert "anna@example.com" in enh.json()["improved_text"]

    # Too-long text -> 413 (guard before any provider call).
    long = client.post("/ai/translate", json={"text": "a" * 5000})
    assert long.status_code == 413, long.text

    # No providers configured -> 503 with setup guidance.
    ai_route.ensemble = Ensemble(providers=[], cache=fresh_cache())
    off = client.post("/ai/translate", json={"text": "Hello"})
    assert off.status_code == 503, off.text
    assert "OPENAI_API_KEY" in off.json()["detail"]

    # Rate limiting -> 429.
    ai_route.ensemble = good
    ai_route.limiter = SlidingWindowLimiter(1, window_seconds=60)
    assert client.post("/ai/translate", json={"text": "Hello"}).status_code == 200
    limited = client.post("/ai/translate", json={"text": "Hello"})
    assert limited.status_code == 429, limited.text
    assert "Too many AI requests" in limited.json()["detail"]
    ai_route.limiter = SlidingWindowLimiter(100)


def limiter_window():
    lim = SlidingWindowLimiter(2, window_seconds=60)
    assert lim.check("ip")[0] is True
    assert lim.check("ip")[0] is True
    allowed, retry = lim.check("ip")
    assert allowed is False and retry > 0
    assert lim.check("other-ip")[0] is True


# --------------------------------------------------------------------------- #

def main():
    print("=" * 70)
    print("AI ENSEMBLE TEST SUITE (mock providers, no network)")
    print("=" * 70)
    check("translate uses consensus and protects tokens", translate_uses_consensus_and_protects_tokens)
    check("translate rejects total token loss", translate_rejects_all_token_loss)
    check("sentence completeness influences the winner", translate_scores_sentence_completeness)
    check("enhance masks tokens in both texts", enhance_masks_tokens_in_source_and_translation)
    check("explain returns the richest answer", explain_returns_best_rich_answer)
    check("cache avoids duplicate provider calls", cache_avoids_duplicate_api_calls)
    check("missing keys raise AiNotConfigured", not_configured_raises)
    check("status reports provider capabilities", status_reports_capabilities)
    check("failing provider is reported, not fatal", failed_provider_is_reported_not_fatal)
    check("HTTP endpoints", endpoint_suite)
    check("rate limiter window", limiter_window)

    print("-" * 70)
    print(f"{PASSED} passed, {FAILED} failed")
    if FAILED:
        for name, exc in FAILURES:
            print(f"  FAILED: {name}: {exc}")
        return 1
    print("ALL AI CHECKS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
