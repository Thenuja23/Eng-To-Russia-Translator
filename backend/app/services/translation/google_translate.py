"""Google Cloud Translation (Basic v2) provider.

The app stays fully usable without an API key: this module is only registered
when ``GOOGLE_TRANSLATE_API_KEY`` (or ``GOOGLE_API_KEY``) is configured.

Accuracy details that matter here:

* Token protection is applied before the request (e-mails, URLs, dates, times,
  numbers, course codes, Russian names) and verified afterwards. If Google
  rewrites or drops a placeholder, we retry the affected chunk and finally fall
  back to translating around the placeholders so the user's data is always
  restored verbatim.
* Sentences are translated in order with the original whitespace preserved, so
  no sentence is dropped when a paragraph is long.
* The API accepts batches (``q`` as a list), so a paragraph costs one request
  instead of one request per sentence. Failed batches are retried per segment.
* Retries use exponential backoff for HTTP 429/5xx/network errors. API keys are
  sent in the ``X-goog-api-key`` header, never in a URL or log line.
"""
from __future__ import annotations

import html
import re
import threading
import time
from typing import Dict, List, Optional, Sequence, Tuple

import httpx

from .base import Translator, TranslationResult
from .chunking import chunk_text, DEFAULT_MAX_CHARS
from .token_protector import TokenProtector
from app.core.config import settings

_PLACEHOLDER_RE = re.compile(r"(GTR)(?:\s*0*)(\d{1,4})", re.IGNORECASE)


class GoogleTranslateTranslator(Translator):
    """Translate en<->ru with Google Cloud Translation v2."""

    PREFIX = "GTR"
    MAX_BATCH_SEGMENTS = 100
    MAX_BATCH_CHARS = 20_000

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: Optional[float] = None,
        retries: Optional[int] = None,
        max_chars: Optional[int] = None,
    ):
        self.api_key = (
            (api_key if api_key is not None else settings.google_translate_key) or ""
        ).strip()
        self.base_url = (
            base_url or settings.google_translate_base_url
        ).rstrip("/")
        self.timeout = (
            timeout
            if timeout is not None
            else float(settings.google_translate_timeout_seconds)
        )
        self.retries = (
            retries if retries is not None else int(settings.google_translate_retries)
        )
        self.max_chars = int(
            max_chars
            or settings.google_translate_max_chars
            or DEFAULT_MAX_CHARS
        )
        self._client: Optional[httpx.Client] = None
        self._client_lock = threading.Lock()

    # ------------------------------------------------------------------ #
    # capability helpers
    # ------------------------------------------------------------------ #

    @property
    def configured(self) -> bool:
        return bool(self.api_key)

    def supports(self, src_lang: str, tgt_lang: str) -> bool:
        s, t = (src_lang or "").lower(), (tgt_lang or "").lower()
        return {s, t} == {"en", "ru"} and s != t

    def _get_client(self) -> httpx.Client:
        if self._client is None:
            with self._client_lock:
                if self._client is None:
                    self._client = httpx.Client(
                        timeout=httpx.Timeout(self.timeout, connect=min(8.0, self.timeout)),
                        headers={"User-Agent": "russian-cursive-assistant/1.0"},
                    )
        return self._client

    # ------------------------------------------------------------------ #
    # HTTP
    # ------------------------------------------------------------------ #

    def _request_batch(
        self, pieces: Sequence[str], src: str, tgt: str
    ) -> List[str]:
        """Translate a batch of text segments, preserving their order."""
        if not pieces:
            return []
        if not self.configured:
            raise RuntimeError("GOOGLE_TRANSLATE_API_KEY is not configured")

        payload = {
            "q": list(pieces),
            "source": src,
            "target": tgt,
            "format": "text",
        }
        headers = {
            "X-goog-api-key": self.api_key,
            "Content-Type": "application/json",
        }
        last_error: Optional[str] = None
        for attempt in range(max(0, self.retries) + 1):
            try:
                response = self._get_client().post(
                    self.base_url, json=payload, headers=headers
                )
            except httpx.TimeoutException:
                last_error = "Google Translate timed out"
            except httpx.HTTPError as exc:
                last_error = f"Google Translate network error: {exc}"
            else:
                if response.status_code == 200:
                    try:
                        data = response.json()
                        translations = (
                            data.get("data", {}).get("translations", []) or []
                        )
                        texts = [
                            html.unescape(str(item.get("translatedText", "")))
                            for item in translations
                        ]
                    except Exception as exc:  # noqa: BLE001
                        raise RuntimeError(
                            f"Google Translate returned invalid JSON: {exc}"
                        )
                    if len(texts) != len(pieces):
                        raise RuntimeError(
                            "Google Translate returned "
                            f"{len(texts)} translations for {len(pieces)} segments"
                        )
                    return texts

                # Keep the API key out of any surfaced error.
                detail = (response.text or "").strip().replace(self.api_key, "***")
                last_error = (
                    f"Google Translate HTTP {response.status_code}: "
                    f"{detail[:240] or 'no detail'}"
                )
                if response.status_code not in (429, 500, 502, 503, 504):
                    raise RuntimeError(last_error)
                retry_after = response.headers.get("Retry-After")
                if retry_after and retry_after.isdigit():
                    time.sleep(min(5.0, float(retry_after)))

            if attempt < self.retries:
                time.sleep(0.35 * (2 ** attempt))

        raise RuntimeError(last_error or "Google Translate request failed")

    # ------------------------------------------------------------------ #
    # placeholder safety
    # ------------------------------------------------------------------ #

    @staticmethod
    def _repair_placeholders(text: str) -> str:
        """Google occasionally lowercases or spaces out GTR_0001 style tokens."""

        def _canonical(match: "re.Match") -> str:
            return f"GTR{int(match.group(2)):04d}"

        return _PLACEHOLDER_RE.sub(_canonical, text or "")

    def _has_all(self, text: str, keys: Sequence[str], protector: TokenProtector) -> bool:
        repaired = self._repair_placeholders(text)
        return all(protector.key_present(repaired, key) for key in keys)

    def _translate_segmented(
        self,
        unit: str,
        keys: Sequence[str],
        protector: TokenProtector,
        src: str,
        tgt: str,
    ) -> str:
        """Last-resort translation around placeholders.

        Every placeholder is copied through verbatim; only the natural-language
        fragments between them are sent to Google. Fluency is lower than a whole
        sentence, but user data can never be lost.
        """
        pattern = re.compile(rf"({re.escape(self.PREFIX)}\d{{4}})")
        parts = pattern.split(unit)
        out: List[str] = []
        for part in parts:
            if not part:
                continue
            if pattern.fullmatch(part):
                out.append(part)
                continue
            if not part.strip():
                out.append(part)
                continue
            lead = part[: len(part) - len(part.lstrip())]
            trail = part[len(part.rstrip()) :]
            core = part.strip()
            translated = self._request_batch([core], src, tgt)[0]
            out.append(lead + translated + trail)
        return "".join(out)

    def _translate_unit(
        self,
        unit: str,
        translated: str,
        keys: Sequence[str],
        protector: TokenProtector,
        src: str,
        tgt: str,
    ) -> Tuple[str, str]:
        if not keys:
            return translated, "whole"
        repaired = self._repair_placeholders(translated)
        if self._has_all(repaired, keys, protector):
            return repaired, "whole"

        # Retry this single segment; batching is sometimes what confuses the
        # model about placeholder boundaries.
        retry = self._request_batch([unit], src, tgt)[0]
        repaired_retry = self._repair_placeholders(retry)
        if self._has_all(repaired_retry, keys, protector):
            return repaired_retry, "retry"

        # Guarantee correctness over fluency.
        segmented = self._translate_segmented(unit, keys, protector, src, tgt)
        return self._repair_placeholders(segmented), "segmented"

    # ------------------------------------------------------------------ #
    # public API
    # ------------------------------------------------------------------ #

    def translate(
        self, text: str, src_lang: str = "ru", tgt_lang: str = "en", **kwargs
    ) -> TranslationResult:
        src, tgt = (src_lang or "").lower(), (tgt_lang or "").lower()
        if not (text or "").strip():
            return TranslationResult(
                text="", confidence=1.0, meta={"engine": "google", "model": "google-v2"}
            )
        if not self.supports(src, tgt):
            return TranslationResult(
                text=text,
                confidence=0.0,
                meta={
                    "engine": "google",
                    "model": "google-v2",
                    "error": f"Unsupported language pair '{src_lang}->{tgt_lang}'",
                    "unsupported": True,
                },
            )
        if not self.configured:
            return TranslationResult(
                text=text,
                confidence=0.0,
                meta={
                    "engine": "google",
                    "model": "google-v2",
                    "error": "GOOGLE_TRANSLATE_API_KEY is not configured",
                    "not_configured": True,
                },
            )

        try:
            return self._translate_text(text, src, tgt, kwargs)
        except Exception as exc:  # noqa: BLE001
            # Never leak a stack trace to the route; the service will fall back
            # to the offline engine and report this error in meta.
            return TranslationResult(
                text=text,
                confidence=0.0,
                meta={
                    "engine": "google",
                    "model": "google-v2",
                    "error": f"Google Translate failed: {type(exc).__name__}: {exc}",
                },
            )

    def _translate_text(
        self, text: str, src: str, tgt: str, kwargs: Dict[str, object]
    ) -> TranslationResult:
        max_chars = int(kwargs.get("max_chars") or self.max_chars)
        protector = TokenProtector(prefix=self.PREFIX)  # per call -> thread-safe
        protected, mapping = protector.protect(text)
        units = chunk_text(protected, max_chars=max_chars)

        translatable = [
            index
            for index, (kind, value) in enumerate(units)
            if kind == "text" and value.strip()
        ]
        translated_by_index: Dict[int, str] = {}
        strategies = set()
        batches = 0

        position = 0
        while position < len(translatable):
            batch_indices: List[int] = []
            batch_chars = 0
            while position < len(translatable):
                index = translatable[position]
                value = units[index][1]
                if batch_indices and (
                    len(batch_indices) >= self.MAX_BATCH_SEGMENTS
                    or batch_chars + len(value) > self.MAX_BATCH_CHARS
                ):
                    break
                batch_indices.append(index)
                batch_chars += len(value)
                position += 1

            pieces = [units[index][1] for index in batch_indices]
            batches += 1
            try:
                results = self._request_batch(pieces, src, tgt)
            except Exception:
                # Isolate a bad segment instead of losing the whole batch.
                results = [
                    self._request_batch([piece], src, tgt)[0] for piece in pieces
                ]

            for index, result in zip(batch_indices, results):
                keys = [key for key in mapping if key in units[index][1]]
                translated_unit, strategy = self._translate_unit(
                    units[index][1], result, keys, protector, src, tgt
                )
                strategies.add(strategy)
                translated_by_index[index] = translated_unit

        # Reassemble in the original order, including every whitespace separator.
        pieces_out: List[str] = []
        for index, (kind, value) in enumerate(units):
            if kind == "sep":
                pieces_out.append(value)
            else:
                pieces_out.append(translated_by_index.get(index, value))

        translated = "".join(pieces_out)
        translated = self._repair_placeholders(translated)
        restored, all_restored = protector.restore(translated, mapping)

        # Light touch clean-up; never touch protected values.
        restored = re.sub(r"[ \t]{2,}", " ", restored)
        restored = re.sub(r"[ \t]+([,.;:!?])", r"\1", restored)

        strategy = "segmented" if "segmented" in strategies else (
            "retry" if "retry" in strategies else "whole"
        )
        confidence = 0.98
        if "retry" in strategies:
            confidence = 0.93
        if "segmented" in strategies:
            confidence = 0.88
        meta = {
            "engine": "google",
            "model": "google-translate-v2",
            "src": src,
            "tgt": tgt,
            "protected_count": len(mapping),
            "all_placeholders_restored": all_restored,
            "placeholder_strategy": strategy,
            "chunks": len(translatable),
            "batches": batches,
        }
        if not all_restored:
            confidence = 0.75
            meta["flag"] = "PLACEHOLDER_LOSS_DETECTED"
        return TranslationResult(restored, confidence=confidence, meta=meta)
