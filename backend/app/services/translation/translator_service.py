import re
from typing import Optional, Dict
from .base import Translator, TranslationResult
from .opusmt import OpusMTTranslator
from .nllb import NLLBTranslator
from .fallback_dict import FallbackTranslator
from app.core.config import settings

SUPPORTED_LANGS = ("en", "ru")


class TranslationService:
    """Unified translation service.

    Resolution order: requested engine -> default engine -> offline glossary fallback.
    The glossary fallback is only used when a neural model cannot produce output,
    and is flagged in the response ``meta``.
    """

    def __init__(self, default: str = "opustmt", device: str = "cpu"):
        self.default = default
        self.device = device
        self._translators: Dict[str, Translator] = {}
        self._enabled: Dict[str, bool] = {}
        self._init_translators()

    def _init_translators(self):
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

        self._translators["fallback"] = FallbackTranslator()
        self._enabled["fallback"] = True

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

    def _failed(self, src: str, out: str, src_lang: str) -> bool:
        """True when the primary engine did not actually translate."""
        # Nothing translatable (digits / punctuation / emoji only) -> not a failure.
        if not re.search(r"[A-Za-zА-Яа-яЁё]", src or ""):
            return False
        if (src or "").strip().lower() == (out or "").strip().lower():
            return True
        s = src_lang.lower()
        if s == "en":
            # Expected Cyrillic: Latin-only output means it did not translate.
            return bool(re.search(r"[A-Za-z]", out)) and not re.search(r"[А-Яа-яЁё]", out)
        if s == "ru":
            return bool(re.search(r"[А-Яа-яЁё]", out)) and not re.search(r"[A-Za-z]", out)
        return False

    def translate(self, text: str, src_lang: str = "ru", tgt_lang: str = "en",
                  engine: Optional[str] = None, **kwargs) -> TranslationResult:
        src = (src_lang or "").lower()
        tgt = (tgt_lang or "").lower()

        if src not in SUPPORTED_LANGS or tgt not in SUPPORTED_LANGS or src == tgt:
            return TranslationResult(text=text, confidence=0.0, meta={
                "engine": "none",
                "unsupported": True,
                "error": f"unsupported language pair '{src_lang}->{tgt_lang}'",
                "supported": list(SUPPORTED_LANGS),
            })

        requested = engine or self.default
        eng = requested
        if eng not in self._translators or not self._enabled.get(eng):
            eng = self.default

        translator = self._translators[eng]
        if not translator.supports(src, tgt):
            eng = self.default
            translator = self._translators[eng]

        res = translator.translate(text, src_lang=src, tgt_lang=tgt, **kwargs)
        if res.meta is None:
            res.meta = {}
        res.meta["engine"] = eng
        if requested != eng:
            res.meta["requested_engine"] = requested
            res.meta["engine_note"] = (
                f"engine '{requested}' unavailable; used '{eng}'"
            )

        primary_error = res.meta.get("error")
        needs_fallback = bool(primary_error) or self._failed(text, res.text, src)

        if needs_fallback and eng != "fallback" and text.strip() != "":
            fb = self._translators["fallback"]
            fb_res = fb.translate(text, src_lang=src, tgt_lang=tgt, **kwargs)
            fb_res.meta["primary_engine"] = eng
            fb_res.meta["primary_error"] = primary_error or "primary engine returned input unchanged"
            fb_res.meta["engine"] = "fallback"
            if requested != eng:
                fb_res.meta["requested_engine"] = requested
            return fb_res

        return res

    def get_available_engines(self):
        return [k for k in self._translators if self._enabled.get(k)]
