from .tesseract_ocr import TesseractOCR
from app.services.preprocessing.pipeline import PreprocessingPipeline


class OCRPipeline:
    def __init__(self, ocr_engine=None):
        self.ocr = ocr_engine or TesseractOCR()
        self.preproc = PreprocessingPipeline()

    def recognize(self, image_path: str, lang: str = "rus", preprocess: bool = True):
        # In real implementation, preprocess image first
        result = self.ocr.recognize(image_path, lang=lang)
        result.meta["preprocessed"] = preprocess
        return result
