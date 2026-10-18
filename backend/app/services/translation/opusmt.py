import threading
from typing import Optional

from .base import Translator, TranslationResult
from .token_protector import TokenProtector
from .placeholder_safe import translate_preserving_placeholders
from .chunking import chunk_text, DEFAULT_MAX_CHARS
from app.core.config import settings


class OpusMTTranslator(Translator):
    """Opus-MT (Helsinki-NLP) ru<->en. Default engine per locked decision.

    - Models are loaded lazily and the pipeline is cached, so the ~300 MB
      weights are only read once per process, not on every request.
    - A fresh ``TokenProtector`` is used per call (no shared mutable state), so
      concurrent requests cannot corrupt each other's placeholders.
    - Long input is chunked so nothing is silently truncated.
    """

    PREFIX = "OPU_"

    def __init__(self, device: str = "cpu", model_en_ru: str = None, model_ru_en: str = None):
        self.device = device
        self.model_en_ru = model_en_ru or settings.opusmt_en_ru
        self.model_ru_en = model_ru_en or settings.opusmt_ru_en
        self._ru_en_pipe = None
        self._en_ru_pipe = None
        self._load_error = None
        self._lock = threading.Lock()

    def _device_index(self) -> int:
        return -1 if self.device == "cpu" else 0

    def _load(self, src: str, tgt: str):
        with self._lock:
            if src == "ru" and tgt == "en":
                if self._ru_en_pipe is None:
                    from transformers import pipeline
                    self._ru_en_pipe = pipeline(
                        "translation", model=self.model_ru_en, device=self._device_index()
                    )
                return self._ru_en_pipe
            if src == "en" and tgt == "ru":
                if self._en_ru_pipe is None:
                    from transformers import pipeline
                    self._en_ru_pipe = pipeline(
                        "translation", model=self.model_en_ru, device=self._device_index()
                    )
                return self._en_ru_pipe
        return None

    def supports(self, src_lang: str, tgt_lang: str) -> bool:
        s, t = src_lang.lower(), tgt_lang.lower()
        return (s == "ru" and t == "en") or (s == "en" and t == "ru")

    def translate(self, text: str, src_lang: str = "ru", tgt_lang: str = "en", **kwargs) -> TranslationResult:
        if not text or text.strip() == "":
            return TranslationResult(text="", confidence=1.0, meta={"model": "opus-mt"})

        max_length = kwargs.get("max_length", 512)
        max_chars = kwargs.get("max_chars", DEFAULT_MAX_CHARS)
        protector = TokenProtector(prefix=self.PREFIX)  # per-call, thread-safe
        protected, mapping = protector.protect(text)
        s, t = src_lang.lower(), tgt_lang.lower()

        try:
            pipe = self._load(s, t)
        except Exception as e:
            restored, all_restored = protector.restore(protected, mapping)
            return TranslationResult(restored, confidence=0.5, meta={
                "error": f"Failed to load Opus-MT {s}-{t}: {e}",
                "model": "opus-mt",
                "engine": "opustmt",
                "all_placeholders_restored": all_restored,
            })

        if pipe is None:
            return TranslationResult(protected, confidence=0.0, meta={
                "model": "opus-mt", "engine": "opustmt",
                "error": f"Opus-MT does not support {src_lang}->{tgt_lang}",
                "unsupported": True,
            })

        def _run(segment: str) -> str:
            out = pipe(segment, max_length=max_length)
            return out[0]["translation_text"] if out else segment

        strategies = set()
        pieces = []
        try:
            for kind, value in chunk_text(protected, max_chars=max_chars):
                if kind == "sep" or value.strip() == "":
                    pieces.append(value)
                    continue
                piece_keys = [k for k in mapping if k in value]
                translated_piece, strategy = translate_preserving_placeholders(
                    _run, value, piece_keys, prefix=self.PREFIX,
                    is_present=protector.key_present,
                )
                strategies.add(strategy)
                pieces.append(translated_piece)
        except Exception as e:
            restored, all_restored = protector.restore(protected, mapping)
            return TranslationResult(restored, confidence=0.5, meta={
                "error": str(e), "model": "opus-mt", "engine": "opustmt",
                "all_placeholders_restored": all_restored,
            })

        translated = "".join(pieces)
        restored, all_restored = protector.restore(translated, mapping)
        meta = {
            "model": "opus-mt",
            "src": src_lang,
            "tgt": tgt_lang,
            "all_placeholders_restored": all_restored,
            "placeholder_strategy": "segmented" if "segmented" in strategies else "whole",
            "protected_count": len(mapping),
        }
        if not all_restored:
            meta["flag"] = "PLACEHOLDER_LOSS_DETECTED"
        confidence = 0.95 if all_restored else 0.85
        if "segmented" in strategies:
            confidence = min(confidence, 0.9)
        return TranslationResult(restored, confidence=confidence, meta=meta)
