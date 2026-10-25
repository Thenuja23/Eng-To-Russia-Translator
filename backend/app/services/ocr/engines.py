"""Recognition engines used by the OCR reader.

Both engines return the same small structure (text, lines, confidence, word
boxes), which lets the reader compare them fairly and refine weak lines.
"""
from __future__ import annotations

import re
import threading
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np

TESS_LANG = "rus+eng"
TESS_OEM = 1


@dataclass
class WordBox:
    text: str
    confidence: float
    bbox: Tuple[int, int, int, int]  # x, y, w, h


@dataclass
class TextLine:
    text: str
    confidence: float
    bbox: Tuple[int, int, int, int]
    words: List[WordBox] = field(default_factory=list)


@dataclass
class EngineResult:
    engine: str
    text: str = ""
    confidence: float = 0.0
    lines: List[TextLine] = field(default_factory=list)
    detail: str = ""
    error: str = ""
    image: Any = None  # ndarray used for this pass (for line refinement)
    variant: str = ""
    psm: int = 0

    @property
    def ok(self) -> bool:
        return not self.error and bool(self.text.strip())


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #

def _weighted_confidence(words: Sequence[WordBox]) -> float:
    weighted = 0.0
    weights = 0.0
    for word in words:
        weight = max(1, len(word.text))
        weighted += max(0.0, min(100.0, word.confidence)) * weight
        weights += weight
    return weighted / weights if weights else 0.0


def _bbox_of(words: Sequence[WordBox]) -> Tuple[int, int, int, int]:
    if not words:
        return (0, 0, 0, 0)
    x0 = min(w.bbox[0] for w in words)
    y0 = min(w.bbox[1] for w in words)
    x1 = max(w.bbox[0] + w.bbox[2] for w in words)
    y1 = max(w.bbox[1] + w.bbox[3] for w in words)
    return (x0, y0, max(1, x1 - x0), max(1, y1 - y0))


def _split_line_by_y(words: List[WordBox]) -> List[List[WordBox]]:
    """Guard against Tesseract putting far-apart rows under one line id."""
    if len(words) < 2:
        return [words]
    heights = sorted(w.bbox[3] for w in words)
    median_h = heights[len(heights) // 2] or 1
    ordered = sorted(words, key=lambda w: w.bbox[1])
    groups: List[List[WordBox]] = []
    for word in ordered:
        cy = word.bbox[1] + word.bbox[3] / 2.0
        placed = False
        for group in groups:
            gy = np.mean([w.bbox[1] + w.bbox[3] / 2.0 for w in group])
            if abs(cy - gy) <= median_h * 0.8:
                group.append(word)
                placed = True
                break
        if not placed:
            groups.append([word])
    return groups


def _lines_from_words(words: List[WordBox]) -> List[TextLine]:
    if not words:
        return []
    lines = []
    for group in _split_line_by_y(words):
        group.sort(key=lambda w: w.bbox[0])
        text = " ".join(w.text for w in group)
        lines.append(
            TextLine(
                text=text,
                confidence=_weighted_confidence(group),
                bbox=_bbox_of(group),
                words=group,
            )
        )
    lines.sort(key=lambda line: (line.bbox[1], line.bbox[0]))
    return lines


# --------------------------------------------------------------------------- #
# Tesseract
# --------------------------------------------------------------------------- #

def run_tesseract(
    image: np.ndarray,
    psm: int = 6,
    lang: str = TESS_LANG,
    oem: int = TESS_OEM,
    variant: str = "",
) -> EngineResult:
    result = EngineResult(engine="tesseract", image=image, variant=variant, psm=psm)
    try:
        import pytesseract
        from pytesseract import Output
    except Exception as exc:  # noqa: BLE001
        result.error = f"pytesseract unavailable: {exc}"
        return result

    config = (
        f"--oem {oem} --psm {psm} --dpi 300 "
        "-c preserve_interword_spaces=1"
    )
    try:
        data = pytesseract.image_to_data(
            image, lang=lang, config=config, output_type=Output.DICT
        )
    except Exception as exc:  # noqa: BLE001
        result.error = f"tesseract failed: {exc}"
        return result

    grouped: Dict[Tuple[int, int, int], List[WordBox]] = {}
    for i, raw in enumerate(data.get("text", [])):
        word = (raw or "").strip()
        if not word:
            continue
        try:
            confidence = float(data["conf"][i])
        except (TypeError, ValueError, KeyError, IndexError):
            confidence = -1.0
        if confidence < 0:
            continue
        try:
            x = int(data["left"][i])
            y = int(data["top"][i])
            w = int(data["width"][i])
            h = int(data["height"][i])
            key = (
                int(data["block_num"][i]),
                int(data["par_num"][i]),
                int(data["line_num"][i]),
            )
        except (TypeError, ValueError, KeyError, IndexError):
            continue
        grouped.setdefault(key, []).append(
            WordBox(text=word, confidence=confidence, bbox=(x, y, w, h))
        )

    lines: List[TextLine] = []
    for key in sorted(grouped):
        words = grouped[key]
        words.sort(key=lambda wb: wb.bbox[0])
        for group in _split_line_by_y(words):
            group.sort(key=lambda wb: wb.bbox[0])
            lines.append(
                TextLine(
                    text=" ".join(wb.text for wb in group),
                    confidence=_weighted_confidence(group),
                    bbox=_bbox_of(group),
                    words=group,
                )
            )

    lines = [line for line in lines if line.text.strip()]
    result.lines = lines
    result.text = "\n".join(line.text for line in lines)
    result.confidence = _weighted_confidence(
        [word for line in lines for word in line.words]
    )
    result.detail = f"psm{psm}/{variant or 'image'}"
    return result


def refine_line_tesseract(
    image: np.ndarray, line: TextLine, pad: int = 10
) -> Optional[EngineResult]:
    """Re-read one weak line with single-line segmentation (PSM 7)."""
    x, y, w, h = line.bbox
    if w < 8 or h < 8:
        return None
    h_img, w_img = image.shape[:2]
    x0 = max(0, x - pad)
    y0 = max(0, y - pad)
    x1 = min(w_img, x + w + pad)
    y1 = min(h_img, y + h + pad)
    crop = image[y0:y1, x0:x1]
    if crop.size == 0:
        return None
    try:
        import cv2

        scale = max(1.0, 48.0 / max(1, h))
        if scale > 1.2:
            crop = cv2.resize(
                crop, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC
            )
        crop = cv2.copyMakeBorder(crop, 12, 12, 12, 12, cv2.BORDER_CONSTANT, value=255)
    except Exception:  # noqa: BLE001
        pass
    result = run_tesseract(crop, psm=7, oem=TESS_OEM, variant="line-refine")
    if result.ok and result.confidence > 0:
        return result
    return None


# --------------------------------------------------------------------------- #
# EasyOCR
# --------------------------------------------------------------------------- #

_EASY = None
_EASY_ERROR: Optional[str] = None
_EASY_LOCK = threading.Lock()


def _get_easy_reader():
    global _EASY, _EASY_ERROR
    if _EASY is not None or _EASY_ERROR is not None:
        return _EASY
    with _EASY_LOCK:
        if _EASY is None and _EASY_ERROR is None:
            try:
                import easyocr

                _EASY = easyocr.Reader(["ru", "en"], gpu=False, verbose=False)
            except Exception as exc:  # noqa: BLE001
                _EASY_ERROR = str(exc)
    return _EASY


def _easy_line_groups(detections: Sequence[Any]) -> List[List[Dict[str, Any]]]:
    items: List[Dict[str, Any]] = []
    for detection in detections:
        try:
            box, text, confidence = detection
        except (TypeError, ValueError):
            continue
        text = (text or "").strip()
        if not text:
            continue
        points = np.asarray(box, dtype=float).reshape(-1, 2)
        x0, y0 = points.min(axis=0)
        x1, y1 = points.max(axis=0)
        items.append(
            {
                "text": text,
                "confidence": float(confidence) * 100.0,
                "x0": float(x0),
                "x1": float(x1),
                "y0": float(y0),
                "y1": float(y1),
                "height": max(1.0, float(y1 - y0)),
            }
        )

    items.sort(key=lambda item: (item["y0"], item["x0"]))
    groups: List[List[Dict[str, Any]]] = []
    for item in items:
        best_group = None
        best_overlap = 0.0
        for group in groups:
            gy0 = min(g["y0"] for g in group)
            gy1 = max(g["y1"] for g in group)
            overlap = min(gy1, item["y1"]) - max(gy0, item["y0"])
            reference = min(item["height"], max(1.0, gy1 - gy0))
            ratio = overlap / reference if reference else 0.0
            if ratio > best_overlap:
                best_overlap = ratio
                best_group = group
        if best_group is not None and best_overlap >= 0.45:
            best_group.append(item)
        else:
            groups.append([item])

    for group in groups:
        group.sort(key=lambda g: g["x0"])
    groups.sort(key=lambda group: min(g["y0"] for g in group))
    return groups


def run_easyocr(image: np.ndarray, variant: str = "") -> EngineResult:
    result = EngineResult(engine="easyocr", image=image, variant=variant)
    reader = _get_easy_reader()
    if reader is None:
        result.error = f"easyocr unavailable: {_EASY_ERROR}"
        return result
    try:
        detections = reader.readtext(
            np.asarray(image),
            detail=1,
            paragraph=False,
            decoder="beamsearch",
            beamWidth=5,
            batch_size=1,
        )
    except Exception as exc:  # noqa: BLE001
        result.error = f"easyocr failed: {exc}"
        return result

    lines: List[TextLine] = []
    for group in _easy_line_groups(detections):
        parts: List[str] = []
        for index, item in enumerate(group):
            if index == 0:
                parts.append(item["text"])
                continue
            gap = item["x0"] - group[index - 1]["x1"]
            # Tiny gaps are fragments of the same word.
            if gap < 0.22 * item["height"]:
                parts[-1] += item["text"]
            else:
                parts.append(item["text"])
        text = " ".join(parts).strip()
        if not text:
            continue
        confidence = float(
            np.average(
                [item["confidence"] for item in group],
                weights=[max(1, len(item["text"])) for item in group],
            )
        )
        bbox = (
            int(min(item["x0"] for item in group)),
            int(min(item["y0"] for item in group)),
            int(max(item["x1"] for item in group) - min(item["x0"] for item in group)),
            int(max(item["y1"] for item in group) - min(item["y0"] for item in group)),
        )
        lines.append(TextLine(text=text, confidence=confidence, bbox=bbox))

    result.lines = lines
    result.text = "\n".join(line.text for line in lines)
    result.confidence = (
        float(np.average([line.confidence for line in lines],
                         weights=[max(1, len(line.text)) for line in lines]))
        if lines
        else 0.0
    )
    result.detail = f"easyocr/{variant or 'image'}"
    return result
