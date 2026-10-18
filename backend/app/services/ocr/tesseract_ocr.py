from .base import OCRBase, OCRResult, OCRLine, OCRElement
from typing import Optional
import os


class TesseractOCR(OCRBase):
    """Printed OCR: Tesseract with rus.traineddata (baseline).
    Gracefully degrades if pytesseract/opencv not installed.
    """

    def __init__(self):
        self.available = False
        try:
            import pytesseract
            self.available = True
        except Exception:
            self.available = False

    def recognize(self, image_path: str, lang: str = "rus") -> OCRResult:
        if not self.available:
            return OCRResult(text="", lines=[], confidence=0.0, meta={"error": "pytesseract not installed"})
        if not os.path.exists(image_path):
            return OCRResult(text="", lines=[], confidence=0.0, meta={"error": "image not found"})
        try:
            import cv2
            import pytesseract
            from pytesseract import Output

            img = cv2.imread(image_path)
            if img is None:
                return OCRResult(text="", lines=[], confidence=0.0, meta={"error": "cannot read image"})

            data = pytesseract.image_to_data(img, lang=lang, output_type=Output.DICT)
            lines_map = {}
            for i in range(len(data["text"])):
                text = data["text"][i]
                if text.strip() == "":
                    continue
                conf = float(data["conf"][i]) if data["conf"][i] != "-1" else 0.0
                line_num = data["line_num"][i]
                x, y, w, h = data["left"][i], data["top"][i], data["width"][i], data["height"][i]
                if line_num not in lines_map:
                    lines_map[line_num] = OCRLine(text=text, bbox=[x, y, w, h], confidence=conf, words=[])
                else:
                    # append word
                    lines_map[line_num].text += " " + text
                    lines_map[line_num].words.append(OCRElement(text=text, bbox=[x, y, w, h], confidence=conf))
                    # update bbox roughly
                    if conf > lines_map[line_num].confidence:
                        lines_map[line_num].confidence = conf

            # ensure words list populated properly
            # rebuild words per line properly
            lines = []
            for ln in sorted(lines_map.keys()):
                lines.append(lines_map[ln])
            full_text = "\n".join(l.text for l in lines)
            avg_conf = sum(l.confidence for l in lines) / len(lines) if lines else 0.0
            return OCRResult(text=full_text, lines=lines, confidence=avg_conf, meta={"source": "tesseract", "lang": lang})
        except Exception as e:
            return OCRResult(text="", lines=[], confidence=0.0, meta={"error": str(e)})
