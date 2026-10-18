import os
from typing import List
from .encodings import EncodingDetector
from .pipeline import TextPipeline


class FileIngest:
    def __init__(self):
        self.enc = EncodingDetector()
        self.pipeline = TextPipeline()

    def ingest_txt(self, path: str) -> List:
        try:
            with open(path, "rb") as f:
                data = f.read()
            enc = self.enc.detect(data)
            text = data.decode(enc, errors="replace")
            return self.pipeline.process(text)
        except Exception as e:
            return []

    def ingest_docx(self, path: str) -> List:
        try:
            from docx import Document
            doc = Document(path)
            texts = []
            for para in doc.paragraphs:
                texts.append(para.text)
            full = "\n\n".join(texts)
            return self.pipeline.process(full)
        except Exception:
            return []

    def ingest_pptx(self, path: str) -> List:
        try:
            from pptx import Presentation
            prs = Presentation(path)
            texts = []
            for slide in prs.slides:
                for shape in slide.shapes:
                    if hasattr(shape, "text"):
                        texts.append(shape.text)
            full = "\n\n".join(texts)
            return self.pipeline.process(full)
        except Exception:
            return []

    def ingest_pdf(self, path: str) -> List:
        try:
            import PyPDF2
            texts = []
            with open(path, "rb") as f:
                pdf = PyPDF2.PdfReader(f)
                for page in pdf.pages:
                    try:
                        t = page.extract_text() or ""
                        if len(t.strip()) < 20:
                            # per-page scan fallback if under ~20 chars
                            texts.append("[SCAN_FALLBACK_NEEDED]")
                        else:
                            texts.append(t)
                    except Exception:
                        texts.append("")
            full = "\n\n".join(texts)
            return self.pipeline.process(full)
        except Exception:
            return []

    def ingest(self, path: str) -> List:
        ext = os.path.splitext(path)[1].lower()
        if ext == ".txt":
            return self.ingest_txt(path)
        if ext == ".docx":
            return self.ingest_docx(path)
        if ext == ".pptx":
            return self.ingest_pptx(path)
        if ext == ".pdf":
            return self.ingest_pdf(path)
        return []
