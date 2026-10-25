"""Multi-provider AI consensus engine.

The product needs "one smart model" from several vendors. Instead of picking a
single provider, every configured provider (OpenAI, Anthropic Claude,
Perplexity) answers the same prompt in parallel, and the answers are scored:

* protected tokens must survive verbatim (hard requirement),
* candidates are rewarded for agreeing with the other providers (consensus),
* for keeping every source sentence,
* for using the right script,
* and (when reviewing an existing translation) for staying close to it.

The best candidate wins. All candidates are returned so the UI can show the
comparison — that transparency is what makes the ensemble trustworthy.
"""
from __future__ import annotations

import difflib
import hashlib
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Set, Tuple

from app.core.config import settings
from app.services.translation.token_protector import TokenProtector

from . import prompts
from .cache import TTLCache
from .providers import Provider, ProviderError, build_providers

_CYR = re.compile(r"[А-Яа-яЁё]")
_LAT = re.compile(r"[A-Za-z]")
_SENTENCE = re.compile(r"[.!?…]+")


class AiNotConfigured(RuntimeError):
    """No provider has an API key."""


class AiError(RuntimeError):
    """Providers were configured but none returned a usable answer."""


@dataclass
class Candidate:
    provider: str
    model: str
    text: str = ""
    raw: str = ""
    score: float = 0.0
    agreement: float = 0.0
    latency_ms: int = 0
    error: str = ""
    tokens_ok: bool = True

    @property
    def ok(self) -> bool:
        return not self.error and bool((self.text or "").strip())


def _clean(text: str) -> str:
    """Strip code fences and "here is the translation" style preambles."""
    t = (text or "").strip()
    t = re.sub(r"^```[A-Za-z]*\s*", "", t)
    t = re.sub(r"\s*```$", "", t)
    t = re.sub(
        r"^(?:here(?:'s| is)[^\n:]{0,80}:|"
        r"(?:improved |corrected |final )?(?:translation|russian|english)(?: text)?:)\s*",
        "",
        t,
        flags=re.IGNORECASE,
    )
    if len(t) >= 2 and t[0] == t[-1] and t[0] in "\"'":
        t = t[1:-1]
    return t.strip()


def _sim(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    return difflib.SequenceMatcher(None, a.lower(), b.lower()).ratio()


def _sentence_count(text: str) -> int:
    return len([s for s in _SENTENCE.split(text or "") if s.strip()]) or 1


def _script_score(text: str, tgt: str) -> float:
    t = (tgt or "").lower()
    if t == "ru":
        return 1.0 if _CYR.search(text) else 0.0
    if t == "en":
        return 1.0 if _LAT.search(text) else 0.0
    return 1.0


class Ensemble:
    def __init__(
        self,
        providers: Optional[Sequence[Provider]] = None,
        cache: Optional[TTLCache] = None,
    ):
        self.providers: List[Provider] = list(providers) if providers is not None else build_providers()
        self.cache = cache or TTLCache(
            ttl_seconds=settings.ai_cache_ttl_seconds, maxsize=256
        )

    # ------------------------------------------------------------------ #
    # status
    # ------------------------------------------------------------------ #
    @property
    def configured_providers(self) -> List[Provider]:
        return [p for p in self.providers if p.configured]

    def status(self) -> dict:
        configured = self.configured_providers
        if len(configured) > 1:
            mode = "ensemble"
        elif configured:
            mode = "single"
        else:
            mode = "offline"
        return {
            "enabled": settings.ai_enabled,
            "configured": len(configured),
            "mode": mode,
            "providers": [p.describe(i) for i, p in enumerate(self.providers)],
            "limits": {
                "max_chars": settings.ai_max_chars,
                "requests_per_minute": settings.ai_max_requests_per_minute,
            },
            "cache_entries": len(self.cache),
            "cache_ttl_seconds": settings.ai_cache_ttl_seconds,
            "setup": []
            if configured
            else [
                "Add OPENAI_API_KEY, ANTHROPIC_API_KEY and/or PERPLEXITY_API_KEY "
                "to backend/.env",
                "Restart the backend to load the keys",
            ],
        }

    # ------------------------------------------------------------------ #
    # public tasks
    # ------------------------------------------------------------------ #
    def translate(self, text: str, src: str = "en", tgt: str = "ru") -> dict:
        self._require_text(text)
        cache_key = self._cache_key("translate", [text, src, tgt])
        cached = self.cache.get(cache_key)
        if cached is not None:
            return {**cached, "cached": True}

        protector, protected, mapping = self._protect(text, prefix="AIT")
        candidates = self._fanout(
            prompts.translate_system(src, tgt),
            prompts.translate_user(protected, src, tgt),
        )
        self._restore_candidates(candidates, [(protector, mapping)])

        valid = [c for c in candidates if c.ok]
        if not valid:
            raise AiError(self._failure_summary(candidates))

        self._score(valid, source=text, tgt=tgt)
        best = max(valid, key=lambda c: c.score)
        result = self._result(candidates, best, "translate", {
            "translated_text": best.text,
            "src": src,
            "tgt": tgt,
        })
        self.cache.set(cache_key, result)
        return result

    def enhance(
        self, text: str, translation: str, src: str = "en", tgt: str = "ru"
    ) -> dict:
        self._require_text(text)
        self._require_text(translation, "translation")
        cache_key = self._cache_key("enhance", [text, translation, src, tgt])
        cached = self.cache.get(cache_key)
        if cached is not None:
            return {**cached, "cached": True}

        # Protect tokens in the source, then reuse the same placeholders inside
        # the existing translation (shared values) and protect any extra token
        # that only appears in the translation. The reused source keys must be
        # skipped, otherwise the AIX protector would treat AIT0001 as a plain
        # course code and nest a second placeholder around it.
        src_protector, protected_src, src_map = self._protect(text, prefix="AIT")
        working = translation
        for key, value in src_map.items():
            working = working.replace(value, key)
        tr_protector, protected_tr, tr_map = self._protect(
            working, prefix="AIX", ignore=set(src_map.keys())
        )

        candidates = self._fanout(
            prompts.enhance_system(src, tgt),
            prompts.enhance_user(protected_src, protected_tr),
        )
        self._restore_candidates(
            candidates, [(src_protector, src_map), (tr_protector, tr_map)]
        )

        valid = [c for c in candidates if c.ok]
        if not valid:
            raise AiError(self._failure_summary(candidates))

        self._score(valid, source=text, tgt=tgt, base=translation)
        best = max(valid, key=lambda c: c.score)
        result = self._result(candidates, best, "enhance", {
            "improved_text": best.text,
            "translated_text": best.text,
            "src": src,
            "tgt": tgt,
            "base_translation": translation,
        })
        self.cache.set(cache_key, result)
        return result

    def explain(
        self,
        text: str,
        translation: str = "",
        src: str = "en",
        tgt: str = "ru",
        question: str = "",
    ) -> dict:
        self._require_text(text)
        cache_key = self._cache_key("explain", [text, translation, src, tgt, question])
        cached = self.cache.get(cache_key)
        if cached is not None:
            return {**cached, "cached": True}

        candidates = self._fanout(
            prompts.explain_system(src, tgt),
            prompts.explain_user(text, translation, src, tgt, question),
        )
        valid = [c for c in candidates if c.ok]
        if not valid:
            raise AiError(self._failure_summary(candidates))

        for c in valid:
            words = min(len(c.text.split()), 260) / 260.0
            structure = min(c.text.count("\n"), 6) * 0.08
            c.score = words + structure

        best = max(valid, key=lambda c: c.score)
        result = self._result(candidates, best, "explain", {
            "explanation": best.text,
            "source": text,
        })
        self.cache.set(cache_key, result)
        return result

    # ------------------------------------------------------------------ #
    # internals
    # ------------------------------------------------------------------ #
    def _fanout(self, system: str, user: str) -> List[Candidate]:
        usable = self.configured_providers
        if not usable:
            raise AiNotConfigured(self._setup_message())

        results: List[Candidate] = []
        with ThreadPoolExecutor(max_workers=len(usable)) as pool:
            futures = [
                pool.submit(self._run_one, provider, system, user)
                for provider in usable
            ]
            for future in as_completed(futures):
                results.append(future.result())
        return results

    @staticmethod
    def _run_one(provider: Provider, system: str, user: str) -> Candidate:
        started = time.perf_counter()
        try:
            raw = provider.complete(system, user)
            return Candidate(
                provider=provider.name,
                model=provider.model,
                raw=raw,
                text=_clean(raw),
                latency_ms=int((time.perf_counter() - started) * 1000),
            )
        except Exception as exc:  # noqa: BLE001 - surfaced per provider
            return Candidate(
                provider=provider.name,
                model=provider.model,
                latency_ms=int((time.perf_counter() - started) * 1000),
                error=str(exc),
            )

    @staticmethod
    def _protect(
        text: str, prefix: str = "AIT", ignore: Optional[Set[str]] = None
    ) -> Tuple[TokenProtector, str, Dict[str, str]]:
        protector = TokenProtector(prefix=prefix)
        protected, mapping = protector.protect(text or "", ignore=ignore)
        return protector, protected, mapping

    @staticmethod
    def _restore_candidates(
        candidates: Sequence[Candidate],
        pairs: Sequence[Tuple[TokenProtector, Dict[str, str]]],
    ) -> None:
        for cand in candidates:
            if not cand.ok:
                continue
            text = cand.text
            missing: List[str] = []
            ok = True
            for protector, mapping in pairs:
                if not mapping:
                    continue
                for key in mapping:
                    if not protector.key_present(text, key):
                        missing.append(key)
                text, all_restored = protector.restore(text, mapping)
                ok = ok and all_restored
            absent = [
                value
                for _, mapping in pairs
                for value in mapping.values()
                if value not in text
            ]
            cand.text = text
            cand.tokens_ok = ok and not missing and not absent
            if not cand.tokens_ok:
                cand.error = "lost protected token(s): " + (
                    ", ".join(missing) if missing else "value altered"
                )

    @staticmethod
    def _score(
        candidates: Sequence[Candidate],
        source: str,
        tgt: str,
        base: Optional[str] = None,
    ) -> None:
        texts = [c.text for c in candidates]
        src_sentences = _sentence_count(source)
        for i, cand in enumerate(candidates):
            others = [texts[j] for j in range(len(texts)) if j != i]
            consensus = (
                sum(_sim(cand.text, other) for other in others) / len(others)
                if others
                else 1.0
            )
            completeness = min(1.0, _sentence_count(cand.text) / src_sentences)
            script = _script_score(cand.text, tgt)
            if base is not None:
                cand.score = (
                    0.45 * consensus
                    + 0.20 * completeness
                    + 0.15 * script
                    + 0.20 * _sim(cand.text, base)
                )
            else:
                cand.score = 0.55 * consensus + 0.25 * completeness + 0.20 * script
            cand.agreement = consensus

    def _result(
        self,
        candidates: Sequence[Candidate],
        best: Candidate,
        mode: str,
        extra: Optional[dict] = None,
    ) -> dict:
        payload = {
            "text": best.text,
            "provider": best.provider,
            "model": best.model,
            "agreement": round(best.agreement, 3),
            "tokens_preserved": best.tokens_ok,
            "mode": mode,
            "cached": False,
            "providers_used": len([c for c in candidates if not c.error]),
            "candidates": [
                self._candidate_dict(c)
                for c in sorted(candidates, key=lambda c: c.score, reverse=True)
            ],
        }
        if extra:
            payload.update(extra)
        return payload

    @staticmethod
    def _candidate_dict(c: Candidate) -> dict:
        return {
            "provider": c.provider,
            "model": c.model,
            "text": c.text,
            "score": round(c.score, 3),
            "agreement": round(c.agreement, 3),
            "latency_ms": c.latency_ms,
            "tokens_preserved": c.tokens_ok,
            "error": c.error,
        }

    def _cache_key(self, mode: str, parts: Sequence[str]) -> str:
        names = ",".join(f"{p.name}:{p.model}" for p in self.configured_providers)
        raw = "|".join([mode, names] + [str(p) for p in parts])
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    @staticmethod
    def _require_text(text: str, field_name: str = "text") -> None:
        if not (text or "").strip():
            raise AiError(f"{field_name} is empty")

    def _setup_message(self) -> str:
        names = ", ".join(p.name for p in self.providers)
        return (
            "No AI provider is configured. Add OPENAI_API_KEY, ANTHROPIC_API_KEY "
            f"and/or PERPLEXITY_API_KEY to backend/.env and restart the backend. "
            f"Known providers: {names}."
        )

    @staticmethod
    def _failure_summary(candidates: Sequence[Candidate]) -> str:
        parts = [f"{c.provider}: {c.error}" for c in candidates if c.error]
        return "No usable AI answer. " + ("; ".join(parts[:4]) if parts else "")
