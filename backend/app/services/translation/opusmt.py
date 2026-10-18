from .base import Translator, TranslationResult
from .token_protector import TokenProtector
from typing import Optional


class OpusMTTranslator(Translator):
    """Opus-MT (Helsinki-NLP) ru<->en. Default engine per locked decision.

    Models are loaded lazily and the translation pipeline is cached, so the
    ~300 MB weights are only read once per process, not on every request.
    """

    def __init__(self, device: str = "cpu"):
        self.device = device
        self._ru_en_pipe = None
        self._en_ru_pipe = None
        self._load_error: Optional[str] = None
        self.protector = TokenProtector(prefix="OPU_")

    def _device_index(self) -> int:
        return -1 if self.device == "cpu" else 0

    def _load_ru_en(self):
        if self._ru_en_pipe is not None:
            return
        try:
            from transformers import pipeline
            self._ru_en_pipe = pipeline(
                "translation",
                model="Helsinki-NLP/opus-mt-ru-en",
                device=self._device_index(),
            )
        except Exception as e:
            self._load_error = f"Failed to load Opus-MT ru-en: {e}"
            raise RuntimeError(self._load_error)

    def _load_en_ru(self):
        if self._en_ru_pipe is not None:
            return
        try:
            from transformers import pipeline
            self._en_ru_pipe = pipeline(
                "translation",
                model="Helsinki-NLP/opus-mt-en-ru",
                device=self._device_index(),
            )
        except Exception as e:
            self._load_error = f"Failed to load Opus-MT en-ru: {e}"
            raise RuntimeError(self._load_error)

    def supports(self, src_lang: str, tgt_lang: str) -> bool:
        s, t = src_lang.lower(), tgt_lang.lower()
        return (s == "ru" and t == "en") or (s == "en" and t == "ru")

    def translate(self, text: str, src_lang: str = "ru", tgt_lang: str = "en", **kwargs) -> TranslationResult:
        if not text or text.strip() == "":
            return TranslationResult(text="", confidence=1.0, meta={"model": "opus-mt"})

        protected, mapping = self.protector.protect(text)
        s, t = src_lang.lower(), tgt_lang.lower()

        try:
            if s == "ru" and t == "en":
                self._load_ru_en()
                out = self._ru_en_pipe(protected, max_length=kwargs.get("max_length", 512))
            elif s == "en" and t == "ru":
                self._load_en_ru()
                out = self._en_ru_pipe(protected, max_length=kwargs.get("max_length", 512))
            else:
                out = None
            translated = out[0]["translation_text"] if out else protected
        except Exception as e:
            translated = protected
            restored, all_restored = self.protector.restore(translated, mapping)
            return TranslationResult(restored, confidence=0.5, meta={
                "error": str(e),
                "model": "opus-mt",
                "all_placeholders_restored": all_restored,
            })

        restored, all_restored = self.protector.restore(translated, mapping)
        meta = {
            "model": "opus-mt",
            "src": src_lang,
            "tgt": tgt_lang,
            "all_placeholders_restored": all_restored,
            "protected_count": len(mapping),
        }
        if not all_restored:
            meta["flag"] = "PLACEHOLDER_LOSS_DETECTED"
        self.protector.clear()
        return TranslationResult(restored, confidence=0.95 if all_restored else 0.85, meta=meta)
