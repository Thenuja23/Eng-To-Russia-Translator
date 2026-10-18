from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class TranslationResult:
    def __init__(self, text: str, confidence: float = 1.0, meta: Optional[Dict[str, Any]] = None):
        self.text = text
        self.confidence = confidence
        self.meta = meta or {}


class Translator(ABC):
    @abstractmethod
    def translate(self, text: str, src_lang: str = "ru", tgt_lang: str = "en", **kwargs) -> TranslationResult:
        pass

    @abstractmethod
    def supports(self, src_lang: str, tgt_lang: str) -> bool:
        pass
