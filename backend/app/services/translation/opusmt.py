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

    # No underscore: MarianMT reliably copies ``ZXQ0001`` as one token, while
    # ``ZXQ_0001`` is normalised (case damage) or split apart, which used to
    # force the lower-quality segmented fallback on almost every sentence
    # containing an e-mail, date or code. OPU is avoided because the model
    # sometimes transliterates it to Cyrillic ("УПУ") depending on context.
    PREFIX = "ZXQ"
    ALTERNATE_PREFIXES = ("ALT", "QWE")

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

    def _translate_once(
        self,
        run,
        text: str,
        prefix: str,
        max_chars: int,
    ):
        """Translate once with one placeholder format.

        Returns ``(restored, all_restored, strategy, protected_count)``.
        """
        protector = TokenProtector(prefix=prefix)  # per-call, thread-safe
        protected, mapping = protector.protect(text)
        strategies = set()
        pieces = []
        for kind, value in chunk_text(protected, max_chars=max_chars):
            if kind == "sep" or value.strip() == "":
                pieces.append(value)
                continue
            piece_keys = [k for k in mapping if k in value]
            translated_piece, strategy = translate_preserving_placeholders(
                run,
                value,
                piece_keys,
                prefix=prefix,
                is_present=protector.key_present,
            )
            strategies.add(strategy)
            pieces.append(translated_piece)

        translated = "".join(pieces)
        restored, all_restored = protector.restore(translated, mapping)
        strategy = "segmented" if "segmented" in strategies else "whole"
        return restored, all_restored, strategy, len(mapping)

    def translate(self, text: str, src_lang: str = "ru", tgt_lang: str = "en", **kwargs) -> TranslationResult:
        if not text or text.strip() == "":
            return TranslationResult(text="", confidence=1.0, meta={"model": "opus-mt"})

        max_length = kwargs.get("max_length", 512)
        max_chars = kwargs.get("max_chars", DEFAULT_MAX_CHARS)
        s, t = src_lang.lower(), tgt_lang.lower()

        try:
            pipe = self._load(s, t)
        except Exception as e:
            return TranslationResult(text, confidence=0.0, meta={
                "error": f"Failed to load Opus-MT {s}-{t}: {e}",
                "model": "opus-mt",
                "engine": "opustmt",
            })

        if pipe is None:
            return TranslationResult(text, confidence=0.0, meta={
                "model": "opus-mt", "engine": "opustmt",
                "error": f"Opus-MT does not support {src_lang}->{tgt_lang}",
                "unsupported": True,
            })

        # Beam search consistently beats greedy decoding on MarianMT, especially
        # for inflection-heavy Russian. 1 restores the old greedy behaviour.
        num_beams = int(kwargs.get("num_beams", settings.opusmt_num_beams) or 1)
        num_beams = max(1, min(8, num_beams))

        def _run(segment: str) -> str:
            generate_kwargs = {"max_length": max_length, "num_beams": num_beams}
            if num_beams > 1:
                generate_kwargs["early_stopping"] = True
            out = pipe(segment, **generate_kwargs)
            return out[0]["translation_text"] if out else segment

        # MarianMT transliterates some acronym-like placeholders (OPU -> УПУ)
        # depending on context. Try a few rare prefixes before accepting the
        # lower-fluency segmented fallback. Most sentences succeed on the first
        # attempt; only token-heavy failures pay for extra passes.
        prefixes = [self.PREFIX] + [
            candidate for candidate in self.ALTERNATE_PREFIXES
            if candidate != self.PREFIX
        ]
        attempts = []
        first_error = None
        for prefix in prefixes:
            try:
                restored, all_restored, strategy, count = self._translate_once(
                    _run, text, prefix, max_chars
                )
            except Exception as e:  # noqa: BLE001
                if first_error is None:
                    first_error = str(e)
                continue
            attempt = {
                "text": restored,
                "all_restored": all_restored,
                "strategy": strategy,
                "prefix": prefix,
                "count": count,
            }
            attempts.append(attempt)
            if all_restored and strategy == "whole":
                break

        if not attempts:
            return TranslationResult(text, confidence=0.0, meta={
                "error": first_error or "Opus-MT translation failed",
                "model": "opus-mt",
                "engine": "opustmt",
            })

        # Prefer a complete whole-text translation; otherwise keep the first
        # segmented result (all attempts guarantee the protected values, but the
        # primary attempt is the most predictable).
        best = next(
            (item for item in attempts if item["all_restored"] and item["strategy"] == "whole"),
            None,
        )
        if best is None:
            best = next((item for item in attempts if item["all_restored"]), attempts[0])

        meta = {
            "model": "opus-mt",
            "src": src_lang,
            "tgt": tgt_lang,
            "all_placeholders_restored": best["all_restored"],
            "placeholder_strategy": best["strategy"],
            "placeholder_prefix": best["prefix"],
            "protected_count": best["count"],
            "attempts": [
                {"prefix": item["prefix"], "strategy": item["strategy"]}
                for item in attempts
            ],
        }
        if not best["all_restored"]:
            meta["flag"] = "PLACEHOLDER_LOSS_DETECTED"
        confidence = 0.95 if best["all_restored"] else 0.85
        if best["strategy"] == "segmented":
            confidence = min(confidence, 0.9)
        return TranslationResult(best["text"], confidence=confidence, meta=meta)
