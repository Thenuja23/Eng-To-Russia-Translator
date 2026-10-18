from .base import OCRBase, OCRResult


class TrOCROCR(OCRBase):
    def recognize(self, image_path: str, lang: str = "rus") -> OCRResult:
        # TrOCR structure - compare with CRNN-CTC on locked test set
        return OCRResult(text="", lines=[], confidence=0.0, meta={"source": "trocr"})
