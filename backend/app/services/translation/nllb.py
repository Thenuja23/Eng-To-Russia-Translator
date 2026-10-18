from .base import Translator, TranslationResult
from .token_protector import TokenProtector


class NLLBTranslator(Translator):
    def __init__(self, device: str = "cpu", model_name: str = "facebook/nllb-200-distilled-600M", warn_noncommercial: bool = True):
        self.device = device
        self.model_name = model_name
        self.warn_noncommercial = warn_noncommercial
        self._model = None
        self._tokenizer = None
        self.protector = TokenProtector(prefix="NLB_")
        self._src_codes = {"ru": "rus_Cyrl", "en": "eng_Latn"}
        self._tgt_codes = {"ru": "rus_Cyrl", "en": "eng_Latn"}

    def _load(self):
        if self._model is not None:
            return
        try:
            from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
            self._tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self._model = AutoModelForSeq2SeqLM.from_pretrained(self.model_name)
            if self.device == "cuda":
                self._model = self._model.to("cuda")
        except Exception as e:
            raise RuntimeError(f"Failed to load NLLB {self.model_name}: {e}")

    def supports(self, src_lang: str, tgt_lang: str) -> bool:
        s, t = src_lang.lower(), tgt_lang.lower()
        return (s == "ru" and t == "en") or (s == "en" and t == "ru")

    def translate(self, text: str, src_lang: str = "ru", tgt_lang: str = "en", **kwargs) -> TranslationResult:
        if not text or text.strip() == "":
            return TranslationResult(text="", confidence=1.0, meta={"model": "nllb-200-distilled-600M"})
        protected, mapping = self.protector.protect(text)
        s, t = src_lang.lower(), tgt_lang.lower()
        try:
            self._load()
            from transformers import pipeline
            src_code = self._src_codes.get(s)
            tgt_code = self._tgt_codes.get(t)
            if src_code is None or tgt_code is None:
                translated = protected
            else:
                translator = pipeline("translation", model=self._model, tokenizer=self._tokenizer, src_lang=src_code, tgt_lang=tgt_code, device=-1 if self.device == "cpu" else 0)
                out = translator(protected, max_length=kwargs.get("max_length", 512))
                translated = out[0]["translation_text"] if out else protected
        except Exception as e:
            translated = protected
            restored, all_restored = self.protector.restore(translated, mapping)
            meta_err = {
                "error": str(e),
                "model": "nllb-200-distilled-600M",
                "license": "non-commercial",
                "flag_licence": True if self.warn_noncommercial else False,
                "all_placeholders_restored": all_restored,
            }
            return TranslationResult(restored, confidence=0.5 if not all_restored else 0.8, meta=meta_err)

        restored, all_restored = self.protector.restore(translated, mapping)
        meta = {
            "model": "nllb-200-distilled-600M",
            "src": src_lang,
            "tgt": tgt_lang,
            "src_code": self._src_codes.get(s),
            "tgt_code": self._tgt_codes.get(t),
            "license": "non-commercial",
            "flag_licence": True if self.warn_noncommercial else False,
            "all_placeholders_restored": all_restored,
            "protected_count": len(mapping),
        }
        if not all_restored:
            meta["flag"] = "PLACEHOLDER_LOSS_DETECTED"
        self.protector.clear()
        return TranslationResult(restored, confidence=0.95 if all_restored else 0.85, meta=meta)
