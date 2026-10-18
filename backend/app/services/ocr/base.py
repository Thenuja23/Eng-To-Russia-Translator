from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class OCRElement:
    def __init__(self, text: str, bbox: Optional[List[int]] = None, confidence: float = 0.0):
        self.text = text
        self.bbox = bbox or []  # [x, y, w, h]
        self.confidence = confidence


class OCRLine:
    def __init__(self, text: str, bbox: Optional[List[int]] = None, confidence: float = 0.0, words: Optional[List[OCRElement]] = None):
        self.text = text
        self.bbox = bbox or []
        self.confidence = confidence
        self.words = words or []


class OCRResult:
    def __init__(self, text: str, lines: List[OCRLine], confidence: float = 0.0, meta: Optional[Dict[str, Any]] = None):
        self.text = text
        self.lines = lines
        self.confidence = confidence
        self.meta = meta or {}


class OCRBase(ABC):
    @abstractmethod
    def recognize(self, image_path: str, lang: str = "rus") -> OCRResult:
        pass
