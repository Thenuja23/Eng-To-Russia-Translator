from .base import Translator, TranslationResult
from .token_protector import TokenProtector
from .placeholder_safe import translate_preserving_placeholders
from .chunking import chunk_text, DEFAULT_MAX_CHARS
import threading


class NLLBTranslator(Translator):
    """NLLB-200 distilled 600M. Non-commercial licence -> flagged in ``meta``.

    Disabled by default (see ``settings.enable_nllb``) because the weights are
    a 2.4 GB download.
    """

    # Match Opus-MT: underscore-free placeholders survive tokenisation better.
    PREFIX = "NLB"

    def __init__(self, device: str = "cpu", model_name: str = "facebook/nllb-200-distilled-600M", warn_noncommercial: bool = True):
        self.device = device
        self.model_name = model_name
        self.warn_noncommercial = warn_noncommercial
        self._model = None
        self._tokenizer = None
        self._lock = threading.Lock()
        self._src_codes = {"ru": "rus_Cyrl", "en": "eng_Latn"}
        self._tgt_codes = {"ru": "rus_Cyrl", "en": "eng_Latn"}

    def _load(self):
        with self._lock:
            if self._model is not None:
                return
            from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
            self._tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self._model = AutoModelForSeq2SeqLM.from_pretrained(self.model_name)
            if self.device == "cuda":
                self._model = self._model.to("cuda")

    def supports(self, src_lang: str, tgt_lang: str) -> bool:
        s, t = src_lang.lower(), tgt_lang.lower()
        return (s == "ru" and t == "en") or (s == "en" and t == "ru")

    def translate(self, text: str, src_lang: str = "ru", tgt_lang: str = "en", **kwargs) -> TranslationResult:
        if not text or text.strip() == "":
            return TranslationResult(text="", confidence=1.0, meta={"model": "nllb-200-distilled-600M"})

        max_length = kwargs.get("max_length", 512)
        max_chars = kwargs.get("max_chars", DEFAULT_MAX_CHARS)
        protector = TokenProtector(prefix=self.PREFIX)
        protected, mapping = protector.protect(text)
        s, t = src_lang.lower(), tgt_lang.lower()

        try:
            self._load()
            from transformers import pipeline
            src_code = self._src_codes.get(s)
            tgt_code = self._tgt_codes.get(t)
            translator = pipeline(
                "translation", model=self._model, tokenizer=self._tokenizer,
                src_lang=src_code, tgt_lang=tgt_code,
                device=-1 if self.device == "cpu" else 0,
            )
        except Exception as e:
            restored, all_restored = protector.restore(protected, mapping)
            return TranslationResult(restored, confidence=0.5, meta={
                "error": f"Failed to load NLLB {self.model_name}: {e}",
                "model": "nllb-200-distilled-600M",
                "engine": "nllb",
                "license": "non-commercial",
                "flag_licence": bool(self.warn_noncommercial),
                "all_placeholders_restored": all_restored,
            })

        def _run(segment: str) -> str:
            out = translator(segment, max_length=max_length)
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
                "error": str(e),
                "model": "nllb-200-distilled-600M",
                "engine": "nllb",
                "license": "non-commercial",
                "flag_licence": bool(self.warn_noncommercial),
                "all_placeholders_restored": all_restored,
            })

        restored, all_restored = protector.restore("".join(pieces), mapping)
        meta = {
            "model": "nllb-200-distilled-600M",
            "src": src_lang,
            "tgt": tgt_lang,
            "src_code": self._src_codes.get(s),
            "tgt_code": self._tgt_codes.get(t),
            "license": "non-commercial",
            "flag_licence": bool(self.warn_noncommercial),
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
