from .normalizer import TextNormalizer
from .langdetect import LanguageDetector
from .segmenter import Segmenter, TextSegment
from .direction import DirectionDetector
from typing import List


class TextPipeline:
    def __init__(self):
        self.normalizer = TextNormalizer()
        self.langdet = LanguageDetector()
        self.segmenter = Segmenter()
        self.dir = DirectionDetector()

    def process(self, text: str) -> List[TextSegment]:
        normalized = self.normalizer.normalize(text)
        segs = self.segmenter.segment(normalized, lang_detector=self.langdet)
        for s in segs:
            s.direction = self.dir.detect(s.text)
        return segs

    def process_all(self, texts: List[str]) -> List[TextSegment]:
        all_segs = []
        for t in texts:
            all_segs.extend(self.process(t))
        return all_segs
