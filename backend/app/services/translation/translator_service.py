"""Unified translation service with offline, Google and hybrid engines.

Resolution rules
----------------
* ``engine`` omitted -> ``settings.default_translator`` (Opus-MT by default).
* ``engine="auto"``  -> Google when a key is configured, else the default.
* ``engine="hybrid"``-> run Google and the local model, then keep the better
  result using token, script, length, sentence and repetition checks.
* Explicit offline engines (``opustmt`` / ``nllb``) never call Google, so the
  offline promise is respected.
* Any failure falls through to the other configured engines and finally to the
  honest offline glossary. Every fallback is flagged in ``meta``.

The service also caches successful results (a paid Google call should not be
repeated for the same debounced keystroke) and exposes engine diagnostics for
the UI.
"""
from __future__ import annotations

import re
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Optional, Sequence, Tuple

from .base import Translator, TranslationResult
from .opusmt import OpusMTTranslator
from .nllb import NLLBTranslator
from .fallback_dict import FallbackTranslator
from .google_translate import GoogleTranslateTranslator
from .token_protector import TokenProtector
from .cache import TranslationCache
from app.core.config import settings

SUPPORTED_LANGS = ("en", "ru")

CYR_RE = re.compile(r"[А-Яа-яЁё]")
LAT_RE = re.compile(r"[A-Za-z]")
WORD_RE = re.compile(r"[A-Za-zА-Яа-яЁё][A-Za-zА-Яа-яЁё'’.-]*")

_ENGINE_LABELS = {
    "auto": "Auto (recommended)",
    "hybrid": "Best quality (Google + offline)",
    "google": "Google Translate (online)",
    "opustmt": "Offline (Opus-MT)",
    "nllb": "Offline (NLLB, experimental)",
    "fallback": "Offline glossary (limited)",
}


class TranslationService:
    def __init__(self, default: str = "opustmt", device: str = "cpu"):
        self.default = (default or "opustmt").strip().lower()
        self.device = device
        self._translators: Dict[str, Translator] = {}
        self._enabled: Dict[str, bool] = {}
        self._cache = TranslationCache(
            ttl_seconds=settings.translation_cache_ttl_seconds,
            max_entries=settings.translation_cache_max_entries,
        )
        self._init_translators()

    # ------------------------------------------------------------------ #
    # setup / diagnostics
    # ------------------------------------------------------------------ #

    def _init_translators(self) -> None:
        self._translators["opustmt"] = OpusMTTranslator(device=self.device)
        self._enabled["opustmt"] = True

        # NLLB is a 2.4 GB, non-commercially licensed model -> opt-in only.
        if settings.enable_nllb:
            self._translators["nllb"] = NLLBTranslator(
                device=self.device,
                model_name=settings.nllb_model_name,
                warn_noncommercial=settings.warn_nllb_noncommercial,
            )
            self._enabled["nllb"] = True

        # Google is only registered when a key exists. Without it the app stays
        # fully offline and the UI hides the cloud options.
        if settings.google_translate_configured:
            self._translators["google"] = GoogleTranslateTranslator()
            self._enabled["google"] = True

        self._translators["fallback"] = FallbackTranslator()
        self._enabled["fallback"] = True

    def get_available_engines(self) -> List[str]:
        return [key for key in self._translators if self._enabled.get(key)]

    def get_engine_details(self) -> List[Dict[str, Any]]:
        google = "google" in self._translators and self._enabled.get("google", False)
        nllb = "nllb" in self._translators and self._enabled.get("nllb", False)
        auto_resolved = "google" if google else self.default
        details: List[Dict[str, Any]] = [
            {
                "id": "auto",
                "label": _ENGINE_LABELS["auto"],
                "available": True,
                "online": google,
                "resolved": auto_resolved,
                "description": (
                    "Uses Google Translate when configured, otherwise the offline model."
                ),
            },
            {
                "id": "hybrid",
                "label": _ENGINE_LABELS["hybrid"],
                "available": google,
                "online": google,
                "description": (
                    "Runs Google and the offline model, then keeps the better, "
                    "token-safe result."
                    if google
                    else "Set GOOGLE_TRANSLATE_API_KEY on the backend to enable it."
                ),
            },
            {
                "id": "google",
                "label": _ENGINE_LABELS["google"],
                "available": google,
                "online": True,
                "description": (
                    "Google Cloud Translation (Basic v2)."
                    if google
                    else "Set GOOGLE_TRANSLATE_API_KEY on the backend to enable it."
                ),
            },
            {
                "id": "opustmt",
                "label": _ENGINE_LABELS["opustmt"],
                "available": True,
                "online": False,
                "description": "Runs entirely on this machine with MarianMT.",
            },
        ]
        if nllb:
            details.append(
                {
                    "id": "nllb",
                    "label": _ENGINE_LABELS["nllb"],
                    "available": True,
                    "online": False,
                    "description": "Large multilingual model; non-commercial licence.",
                }
            )
        details.append(
            {
                "id": "fallback",
                "label": _ENGINE_LABELS["fallback"],
                "available": True,
                "online": False,
                "description": "Small word lookup used only if every model fails.",
            }
        )
        return details

    # ------------------------------------------------------------------ #
    # language / failure helpers
    # ------------------------------------------------------------------ #

    def _unsupported(self, text: str, src_lang: str, tgt_lang: str) -> Optional[TranslationResult]:
        src, tgt = (src_lang or "").lower(), (tgt_lang or "").lower()
        if src not in SUPPORTED_LANGS or tgt not in SUPPORTED_LANGS or src == tgt:
            return TranslationResult(text=text, confidence=0.0, meta={
                "engine": "none",
                "unsupported": True,
                "error": f"Unsupported language pair '{src_lang}->{tgt_lang}'",
                "supported": list(SUPPORTED_LANGS),
            })
        return None

    @staticmethod
    def _has_translatable_text(text: str) -> bool:
        """True when the input contains words beyond protected data.

        A message that is only an e-mail, URL, date, number or course code is
        already valid output. Treating it as an engine failure would send the
        user to the limited glossary and show a misleading "install Opus-MT"
        warning even though the neural model is present.
        """
        value = text or ""
        try:
            _, mapping = TokenProtector().protect(value)
        except Exception:  # noqa: BLE001 - protection is best-effort here
            mapping = {}
        remainder = value
        for protected_value in mapping.values():
            remainder = remainder.replace(protected_value, " ")
        return bool(re.search(r"[A-Za-zА-Яа-яЁё]", remainder))

    def _failed(self, src_text: str, out: str, src_lang: str) -> bool:
        """True when an engine did not really translate the input."""
        if not re.search(r"[A-Za-zА-Яа-яЁё]", src_text or ""):
            return False  # digits / punctuation / emoji only -> nothing to do
        if not self._has_translatable_text(src_text):
            return False  # only protected data (e-mail / URL / code) -> nothing to do
        out = (out or "").strip()
        if not out:
            return True
        if (src_text or "").strip().lower() == out.lower():
            return True
        src = (src_lang or "").lower()
        if src == "en":
            return not CYR_RE.search(out)  # expected Russian
        if src == "ru":
            return not LAT_RE.search(out)  # expected English
        return False

    def _resolve(self, requested: str) -> str:
        requested = (requested or "").strip().lower()
        if requested in ("", "default", "auto"):
            return "google" if "google" in self._translators else self.default
        if requested == "hybrid":
            return "hybrid" if "google" in self._translators else self.default
        if requested not in self._translators or not self._enabled.get(requested):
            return self.default
        return requested

    # ------------------------------------------------------------------ #
    # engine execution
    # ------------------------------------------------------------------ #

    def _run_engine(
        self, engine: str, text: str, src: str, tgt: str, **kwargs
    ) -> TranslationResult:
        translator = self._translators.get(engine)
        if translator is None or not self._enabled.get(engine):
            return TranslationResult(
                text=text,
                confidence=0.0,
                meta={"engine": engine, "error": f"engine '{engine}' is not available"},
            )
        if not translator.supports(src, tgt):
            return TranslationResult(
                text=text,
                confidence=0.0,
                meta={
                    "engine": engine,
                    "unsupported": True,
                    "error": f"engine '{engine}' does not support {src}->{tgt}",
                },
            )
        try:
            result = translator.translate(text, src_lang=src, tgt_lang=tgt, **kwargs)
        except Exception as exc:  # noqa: BLE001
            return TranslationResult(
                text=text,
                confidence=0.0,
                meta={"engine": engine, "error": f"{type(exc).__name__}: {exc}"},
            )
        if result.meta is None:
            result.meta = {}
        result.meta["engine"] = engine
        if result.meta.get("error") or self._failed(text, result.text, src):
            result.meta["failed"] = True
        return result

    @staticmethod
    def _is_bad(result: TranslationResult) -> bool:
        meta = result.meta or {}
        return bool(meta.get("error") or meta.get("failed"))

    # ------------------------------------------------------------------ #
    # hybrid quality voting
    # ------------------------------------------------------------------ #

    def _quality_score(
        self,
        source: str,
        result: TranslationResult,
        tgt: str,
        engine: str,
    ) -> Tuple[float, List[str]]:
        text = (result.text or "").strip()
        if not text:
            return -1_000_000.0, ["empty"]
        meta = result.meta or {}
        reasons: List[str] = []
        score = max(0.0, min(100.0, float(result.confidence or 0.0))) * 0.5

        # 1. Token protection is a hard requirement.
        if meta.get("all_placeholders_restored") is False:
            score -= 80.0
            reasons.append("placeholder_loss")
        else:
            score += 15.0

        # 2. The target language's script must be present.
        has_target = bool(CYR_RE.search(text)) if tgt == "ru" else bool(LAT_RE.search(text))
        if has_target:
            score += 15.0
        else:
            score -= 40.0
            reasons.append("wrong_script")

        # 3. Source-script leakage (ignore protected codes/emails/names).
        tokens = [
            token for token in WORD_RE.findall(text)
            if not re.search(r"[@.]", token) and not re.search(r"\d", token)
        ]
        if tokens:
            wrong = 0
            for token in tokens:
                latin = bool(LAT_RE.search(token))
                cyr = bool(CYR_RE.search(token))
                if tgt == "ru" and latin and not cyr:
                    wrong += 1
                elif tgt == "en" and cyr and not latin:
                    wrong += 1
            ratio = wrong / len(tokens)
            if ratio > 0.45:
                score -= min(25.0, 55.0 * (ratio - 0.45))
                reasons.append("source_script_leak")

        # 4. Length sanity. EN->RU expands, RU->EN contracts.
        source_len = max(1, len((source or "").strip()))
        ratio = len(text) / float(source_len)
        expected = 1.12 if tgt == "ru" else 0.78
        if ratio < max(0.3, expected * 0.4) or ratio > expected * 2.8:
            score -= 12.0
            reasons.append("length_outlier")
        else:
            score += 5.0

        # 5. Sentence completeness (the old Opus-MT failure mode).
        source_sentences = len(re.findall(r"[.!?…]", source or ""))
        output_sentences = len(re.findall(r"[.!?…]", text))
        if source_sentences and output_sentences < source_sentences:
            score -= 10.0
            reasons.append("sentence_loss")
        elif source_sentences:
            score += 3.0

        # 6. Repetition loops.
        words = [w.lower() for w in re.findall(r"[A-Za-zА-Яа-яЁё]+", text)]
        if len(words) >= 8:
            grams = [tuple(words[i:i + 3]) for i in range(len(words) - 2)]
            if grams:
                duplicate_ratio = 1.0 - (len(set(grams)) / float(len(grams)))
                if duplicate_ratio > 0.25:
                    score -= 10.0 * min(1.0, duplicate_ratio)
                    reasons.append("repetition")

        # Google is the stronger model on this pair, but only by a small prior;
        # concrete checks above can still beat it.
        if engine == "google":
            score += 4.0
        return score, reasons

    def _translate_hybrid(
        self, text: str, src: str, tgt: str, **kwargs
    ) -> TranslationResult:
        local_engine = "nllb" if "nllb" in self._translators else "opustmt"
        engines = [engine for engine in ("google", local_engine) if engine in self._translators]
        if not engines:
            return TranslationResult(
                text=text,
                confidence=0.0,
                meta={"engine": "hybrid", "error": "no neural engine available"},
            )

        results: Dict[str, TranslationResult] = {}
        with ThreadPoolExecutor(max_workers=len(engines)) as pool:
            futures = {
                pool.submit(self._run_engine, engine, text, src, tgt, **kwargs): engine
                for engine in engines
            }
            for future in as_completed(futures):
                engine = futures[future]
                try:
                    results[engine] = future.result()
                except Exception as exc:  # noqa: BLE001
                    results[engine] = TranslationResult(
                        text=text,
                        confidence=0.0,
                        meta={"engine": engine, "error": str(exc)},
                    )

        scored: List[Tuple[float, str, TranslationResult, List[str]]] = []
        for engine, result in results.items():
            if self._is_bad(result):
                continue
            value, reasons = self._quality_score(text, result, tgt, engine)
            scored.append((value, engine, result, reasons))

        if not scored:
            errors = "; ".join(
                f"{engine}: {(result.meta or {}).get('error', 'failed')}"
                for engine, result in results.items()
            )
            return TranslationResult(
                text=text,
                confidence=0.0,
                meta={"engine": "hybrid", "error": errors or "all engines failed"},
            )

        scored.sort(key=lambda item: item[0], reverse=True)
        best_score, best_engine, best_result, reasons = scored[0]
        meta = dict(best_result.meta or {})
        meta["engine"] = "hybrid"
        meta["chosen_engine"] = best_engine
        meta["quality_score"] = round(best_score, 1)
        meta["quality_reasons"] = reasons
        meta["alternatives"] = [
            {
                "engine": engine,
                "score": round(value, 1),
                "confidence": round(float(result.confidence or 0.0), 3),
            }
            for value, engine, result, _ in scored
        ]
        if best_engine != "google" and "google" in results:
            meta["note"] = "Offline result chosen over Google by quality checks."
        return TranslationResult(
            best_result.text, confidence=best_result.confidence, meta=meta
        )

    # ------------------------------------------------------------------ #
    # cache
    # ------------------------------------------------------------------ #

    @staticmethod
    def _cache_options(kwargs: Dict[str, Any]) -> Dict[str, Any]:
        return {
            key: kwargs[key]
            for key in ("max_length", "max_chars", "num_beams")
            if key in kwargs
        }

    def _cache_get(self, key: str) -> Optional[TranslationResult]:
        item = self._cache.get(key)
        if not item:
            return None
        meta = dict(item.get("meta") or {})
        meta["cached"] = True
        return TranslationResult(
            text=item.get("text", ""),
            confidence=float(item.get("confidence", 0.0)),
            meta=meta,
        )

    def _cache_set(
        self, key: str, result: TranslationResult
    ) -> None:
        meta = result.meta or {}
        if meta.get("error") or meta.get("failed"):
            return
        if meta.get("primary_error"):
            # A transient cloud failure should be retried on the next request,
            # not frozen into the cache for the whole TTL.
            return
        if meta.get("all_placeholders_restored") is False:
            return
        self._cache.set(
            key,
            {
                "text": result.text,
                "confidence": result.confidence,
                "meta": dict(meta),
            },
        )

    # ------------------------------------------------------------------ #
    # public API
    # ------------------------------------------------------------------ #

    def translate(
        self,
        text: str,
        src_lang: str = "ru",
        tgt_lang: str = "en",
        engine: Optional[str] = None,
        **kwargs,
    ) -> TranslationResult:
        src = (src_lang or "").lower()
        tgt = (tgt_lang or "").lower()

        unsupported = self._unsupported(text, src, tgt)
        if unsupported is not None:
            return unsupported

        requested = (engine or self.default or "").strip().lower()
        cache_key = TranslationCache.make_key(
            requested, src, tgt, text or "", self._cache_options(kwargs)
        )
        cached = self._cache_get(cache_key)
        if cached is not None:
            return cached

        resolved = self._resolve(requested)
        attempted: List[str] = []
        first_error = ""
        primary_engine = resolved

        if resolved == "hybrid" and "google" in self._translators:
            result = self._translate_hybrid(text, src, tgt, **kwargs)
            attempted.extend(
                [e for e in ("google", "nllb" if "nllb" in self._translators else "opustmt") if e in self._translators]
            )
            primary_engine = "hybrid"
            if not self._is_bad(result):
                if requested not in ("", "default", "auto", "hybrid"):
                    result.meta["requested_engine"] = requested
                self._cache_set(cache_key, result)
                return result
            first_error = (result.meta or {}).get("error", "")
        else:
            result = self._run_engine(resolved, text, src, tgt, **kwargs)
            attempted.append(resolved)
            if not self._is_bad(result):
                if requested not in ("", "default", "auto") and requested != resolved:
                    result.meta["requested_engine"] = requested
                    result.meta["engine_note"] = (
                        f"engine '{requested}' unavailable; used '{resolved}'"
                    )
                self._cache_set(cache_key, result)
                return result
            first_error = (result.meta or {}).get("error", "")

        # Fallback chain. Explicit offline requests never touch the network.
        allow_online = requested in ("", "default", "auto", "hybrid", "google")
        order: List[str] = []
        if allow_online and "google" in self._translators:
            order.append("google")
        order.extend([self.default, "opustmt"])
        order.append("fallback")

        for candidate in order:
            if candidate in attempted or candidate not in self._translators:
                continue
            if not self._enabled.get(candidate):
                continue
            attempted.append(candidate)
            fallback_result = self._run_engine(candidate, text, src, tgt, **kwargs)
            if self._is_bad(fallback_result):
                if not first_error:
                    first_error = (fallback_result.meta or {}).get("error", "")
                continue
            fallback_result.meta["primary_engine"] = primary_engine
            if first_error:
                fallback_result.meta["primary_error"] = first_error
            fallback_result.meta["requested_engine"] = requested or "default"
            fallback_result.meta["engine_note"] = (
                f"primary engine '{primary_engine}' failed; used '{candidate}'"
            )
            self._cache_set(cache_key, fallback_result)
            return fallback_result

        # Everything failed: return the best available result (usually the
        # glossary) with a clear warning instead of raising a 500.
        final = self._run_engine("fallback", text, src, tgt, **kwargs)
        if final.meta is None:
            final.meta = {}
        final.meta["engine"] = "fallback"
        final.meta["primary_engine"] = primary_engine
        final.meta["primary_error"] = first_error or "all translation engines failed"
        final.meta["engine_note"] = "no translation engine succeeded; offline glossary used"
        return final
