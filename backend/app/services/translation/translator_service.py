import re
from typing import Optional, Dict
from .base import Translator, TranslationResult
from .opusmt import OpusMTTranslator
from .nllb import NLLBTranslator
from .fallback_dict import FallbackTranslator
from app.core.config import settings


class TranslationService:
    """Unified translation service.
    Resolution order: requested engine -> default engine -> offline glossary fallback.
    The fallback is only used when a neural model cannot produce output, and is flagged in meta.
    """

    def __init__(self, default: str = "opustmt", device: str = "cpu"):
        self.default = default
        self.device = device
        self._translators: Dict[str, Translator] = {}
        self._init_translators()

    def _init_translators(self):
        self._translators["opustmt"] = OpusMTTranslator(device=self.device)
        self._translators["nllb"] = NLLBTranslator(
            device=self.device,
            model_name=settings.nllb_model_name,
            warn_noncommercial=settings.warn_nllb_noncommercial,
        )
        self._translators["fallback"] = FallbackTranslator()

    @staticmethod
    def _has_cyrillic(text: str) -> bool:
        return bool(re.search(r"[А-Яа-яЁё]", text or ""))

    @staticmethod
    def _has_latin(text: str) -> bool:
        return bool(re.search(r"[A-Za-z]", text or ""))

    def _failed(self, src: str, out: str, src_lang: str) -> bool:
        """True when the primary engine did not actually translate."""
        if (src or "").strip().lower() == (out or "").strip().lower():
            return True
        s = src_lang.lower()
        if s == "en":
            # Expected Cyrillic. If there is Latin and no Cyrillic, it did not translate.
            return self._has_latin(out) and not self._has_cyrillic(out)
        if s == "ru":
            return self._has_cyrillic(out) and not self._has_latin(out)
        return False

    def translate(self, text: str, src_lang: str = "ru", tgt_lang: str = "en", engine: Optional[str] = None, **kwargs) -> TranslationResult:
        eng = engine or self.default
        if eng not in self._translators:
            eng = self.default
        translator = self._translators[eng]
        if not translator.supports(src_lang, tgt_lang):
            translator = self._translators[self.default]

        res = translator.translate(text, src_lang=src_lang, tgt_lang=tgt_lang, **kwargs)
        if res.meta is None:
            res.meta = {}
        res.meta["engine"] = eng

        primary_error = res.meta.get("error")
        needs_fallback = bool(primary_error) or self._failed(text, res.text, src_lang)

        if needs_fallback and eng != "fallback" and text.strip() != "":
            fb = self._translators["fallback"]
            fb_res = fb.translate(text, src_lang=src_lang, tgt_lang=tgt_lang, **kwargs)
            fb_res.meta["primary_engine"] = eng
            fb_res.meta["primary_error"] = primary_error or "primary engine returned input unchanged"
            fb_res.meta["engine"] = "fallback"
            return fb_res

        return res

    def get_available_engines(self):
        return list(self._translators.keys())
