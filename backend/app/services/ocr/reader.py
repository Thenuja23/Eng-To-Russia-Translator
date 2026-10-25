"""Multi-pass OCR reader: vote, repair and refine for maximum accuracy.

Strategy (applied on every image regardless of "print" vs "photo"):

1. Normalise the photo (EXIF, scale, perspective, deskew, shadow removal).
2. Generate several recognition views (sharpened/normalised/binarised).
3. Run Tesseract with a PSM ensemble (6 = block of text, 4 = single column,
   3 = fully automatic) and EasyOCR with beam search on the strongest views.
4. Vote per line: prefer the variant with better confidence + more Cyrillic,
   cross-check common mistakes, and re-read weak lines at line-level.
5. Repair tokens (emails, URLs, course codes), fix Cyrillic/Latin look-alikes,
   collapse stray spaces and drop obvious noise.
6. Return the cleaned text with the engine that produced it and diagnostics.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np
from PIL import Image

from . import engines
from . import postprocess
from . import preprocess

CYR = re.compile(r"[А-Яа-яЁё]")
ALNUM = re.compile(r"[A-Za-zА-Яа-яЁё0-9]")


@dataclass
class Candidate:
    text: str
    cleaned: str
    confidence: float
    engine: str
    detail: str
    line_count: int
    cyrillic: int
    latin: int
    length: int


class OCRReader:
    def __init__(self, thorough: bool = True):
        self.thorough = thorough
        # PSM values that handle most Russian pages/notes well.
        self.tess_psms = [6, 4, 3]

    def read(self, image_bytes: bytes) -> Dict[str, Any]:
        image = preprocess.load_image(image_bytes)
        variants = preprocess.build_variants(image, thorough=self.thorough)

        results = self._run_engines(variants)
        if not results:
            return {"text": "", "engine": "none", "confidence": 0.0, "lines": [], "candidates": []}

        candidates = self._candidates(results)
        if not candidates:
            # Engines ran but every result looked like noise (blank page, blur,
            # finger over the lens). That is an empty read, not a server error.
            return {
                "text": "",
                "engine": "none",
                "confidence": 0.0,
                "lines": [],
                "candidates": [],
            }
        best = self._vote(candidates)
        refined = self._refine_lines(best, results)
        cleaned = postprocess.clean_text(refined.text)
        if postprocess.looks_like_noise(cleaned):
            cleaned = postprocess.clean_text(best.cleaned)

        # If nothing useful remains but engines ran, return empty text (not an
        # error) so the UI can show a gentle "no text found" message.
        if postprocess.looks_like_noise(cleaned):
            return {
                "text": "",
                "engine": best.engine,
                "confidence": round(best.confidence, 1),
                "lines": [],
                "candidates": [self._cand_dict(c) for c in candidates],
            }

        return {
            "text": cleaned,
            "engine": best.engine,
            "confidence": round(best.confidence, 1),
            "lines": refined.lines,
            "candidates": [self._cand_dict(c) for c in candidates],
        }

    # ------------------------------------------------------------------ #
    # engine execution
    # ------------------------------------------------------------------ #

    def _run_engines(self, variants) -> List[engines.EngineResult]:
        results: List[engines.EngineResult] = []

        for variant in variants:
            arr = variant.image
            # Tesseract: different page segment modes catch different layouts.
            for psm in self.tess_psms:
                res = engines.run_tesseract(arr, psm=psm, variant=variant.name)
                if res.ok:
                    results.append(res)
            # EasyOCR: strongest on the cleaned grayscale/binary views.
            if variant.kind == "binary" or variant.name in ("sharpened", "normalized"):
                res = engines.run_easyocr(arr, variant=variant.name)
                if res.ok:
                    results.append(res)

        return results

    # ------------------------------------------------------------------ #
    # voting
    # ------------------------------------------------------------------ #

    def _candidates(self, results: List[engines.EngineResult]) -> List[Candidate]:
        candidates = []
        for res in results:
            cleaned = postprocess.clean_text(res.text)
            if postprocess.looks_like_noise(cleaned):
                continue
            lines = [l for l in cleaned.split("\n") if l.strip()]
            candidates.append(
                Candidate(
                    text=res.text,
                    cleaned=cleaned,
                    confidence=max(0.0, min(100.0, res.confidence)),
                    engine=res.detail or res.engine,
                    detail=res.detail,
                    line_count=len(lines),
                    cyrillic=len(CYR.findall(cleaned)),
                    latin=len(re.findall(r"[A-Za-z]", cleaned)),
                    length=len(cleaned),
                )
            )
        return candidates

    def _vote(self, candidates: List[Candidate]) -> Candidate:
        if not candidates:
            raise RuntimeError("no valid candidates")

        def score(candidate: Candidate) -> float:
            total_letters = candidate.cyrillic + candidate.latin
            cyr_ratio = candidate.cyrillic / total_letters if total_letters else 0.0
            # Weight Cyrillic heavily for Russian text, but don't punish
            # mixed Latin tokens (e-mails/course codes).
            value = (
                candidate.confidence * 1.00
                + candidate.cyrillic * 0.85
                + candidate.line_count * 2.5
                + cyr_ratio * 14.0
                + min(candidate.length, 500) * 0.02
            )
            # Penalise results that look like mixed-script noise.
            if postprocess.has_mixed_scripts(candidate.cleaned):
                value -= 12.0
            return value

        return max(candidates, key=score)

    # ------------------------------------------------------------------ #
    # refinement
    # ------------------------------------------------------------------ #

    def _refine_lines(
        self, best: Candidate, results: List[engines.EngineResult]
    ) -> engines.EngineResult:
        """Re-read weak Tesseract lines with single-line segmentation."""
        base = None
        for res in results:
            if res.detail == best.detail and res.lines:
                base = res
                break
        if base is None or not base.lines or base.engine != "tesseract":
            # Build a synthetic result from the best cleaned text.
            return engines.EngineResult(
                engine=best.engine,
                text=best.cleaned,
                confidence=best.confidence,
            )

        image = base.image
        lines_out = []
        for line in base.lines:
            if line.confidence >= 72.0 and len(line.text.strip()) >= 2:
                lines_out.append(line)
                continue
            refined = engines.refine_line_tesseract(image, line)
            if refined and refined.ok and refined.confidence > line.confidence:
                # Replace with the re-read line (keep its cleaned text).
                if refined.lines:
                    line = refined.lines[0]
            lines_out.append(line)

        text = "\n".join(l.text for l in lines_out)
        return engines.EngineResult(
            engine=f"{best.engine}+refined",
            text=text,
            confidence=engines._weighted_confidence(
                [word for line in lines_out for word in line.words]
            )
            or best.confidence,
            lines=lines_out,
            image=image,
        )

    @staticmethod
    def _cand_dict(c: Candidate) -> Dict[str, Any]:
        return {
            "engine": c.engine,
            "confidence": round(c.confidence, 1),
            "lines": c.line_count,
            "cyrillic": c.cyrillic,
        }
