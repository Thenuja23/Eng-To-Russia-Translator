from dataclasses import dataclass
from typing import List, Dict, Any


@dataclass
class TextSegment:
    text: str
    lang: str = "unknown"
    direction: str = "auto"
    meta: Dict[str, Any] = None

    def __post_init__(self):
        if self.meta is None:
            self.meta = {}


class Segmenter:
    def segment(self, text: str, lang_detector=None) -> List[TextSegment]:
        if not text:
            return []
        # Split by meaningful boundaries
        # For now, preserve paragraphs/lines as segments
        segments = []
        paragraphs = text.split('\n\n')
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            lang = lang_detector.detect(para) if lang_detector else 'unknown'
            segments.append(TextSegment(text=para, lang=lang))
        return segments
