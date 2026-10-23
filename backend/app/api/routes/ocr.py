from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
import io
import re
import threading
from PIL import Image

router = APIRouter()

_CYR = re.compile(r"[А-Яа-яЁё]")

# EasyOCR's detector/recognition models are heavy (hundreds of MB) and take
# seconds to load, so the Reader is built once per process and shared behind a
# lock. pytesseract is tried first when the binary is installed.
_READER = None
_READER_LOCK = threading.Lock()
_READER_ERROR = None


def _get_reader():
    global _READER, _READER_ERROR
    if _READER is not None or _READER_ERROR is not None:
        return _READER
    with _READER_LOCK:
        if _READER is None and _READER_ERROR is None:
            try:
                import easyocr
                _READER = easyocr.Reader(["ru", "en"], gpu=False, verbose=False)
            except Exception as e:  # noqa: BLE001
                _READER_ERROR = str(e)
    return _READER


class OCRResponse(BaseModel):
    text: str
    engine: str = "unknown"


def _preprocess(img):
    """Upscale small photos, flatten to grayscale, boost contrast.

    Phone photos of handwriting are usually small, dim and low-contrast;
    EasyOCR does much better on an upscaled grayscale version.
    """
    try:
        import cv2
        import numpy as np
    except Exception:  # noqa: BLE001
        return img
    arr = np.array(img)
    h, w = arr.shape[:2]
    if max(h, w) < 1600:  # upscale to give the recogniser more pixels
        scale = 1600 / max(h, w)
        arr = cv2.resize(arr, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
    gray = cv2.normalize(gray, None, 0, 255, cv2.NORM_MINMAX)
    # gentle sharpening helps thin cursive strokes
    sharpened = cv2.addWeighted(gray, 1.4, cv2.GaussianBlur(gray, (0, 0), 1.0), -0.4, 0)
    return Image.fromarray(sharpened).convert("RGB")


def _score(text):
    """Prefer results with more Cyrillic characters (what this app cares about)."""
    return len(_CYR.findall(text or ""))


# Tesseract is much faster and far more accurate than EasyOCR on *printed*
# text — including Latin/digit tokens such as course codes and e-mail
# addresses, which the mixed Cyrillic+Latin EasyOCR model reliably confuses
# (CS101 -> "CS1Ol", "anna@example.com" -> "anna@example com"). A confident
# Tesseract pass therefore wins immediately; handwriting photos usually yield
# low confidence and fall through to the EasyOCR ensemble.
_TESS_MIN_CONF = 55.0


def _ocr_with_pytesseract(img):
    """Return (text, mean word confidence 0-100)."""
    import pytesseract

    data = pytesseract.image_to_data(
        img, lang="rus+eng", output_type=pytesseract.Output.DICT
    )
    lines = {}
    confs = []
    for i, word in enumerate(data.get("text", [])):
        word = (word or "").strip()
        if not word:
            continue
        try:
            conf = float(data["conf"][i])
        except (TypeError, ValueError, KeyError, IndexError):
            conf = -1.0
        if conf < 0:  # -1 marks non-text elements
            continue
        key = (data["block_num"][i], data["par_num"][i], data["line_num"][i])
        lines.setdefault(key, []).append(word)
        confs.append(conf)
    text = "\n".join(" ".join(words) for _, words in sorted(lines.items()))
    return text, (sum(confs) / len(confs) if confs else 0.0)


def _ocr_with_easyocr(img):
    import numpy as np
    reader = _get_reader()
    if reader is None:
        raise RuntimeError(f"easyocr unavailable: {_READER_ERROR}")
    lines = reader.readtext(np.array(img), detail=0)
    return "\n".join(lines), None


@router.post("/ocr", response_model=OCRResponse)
async def ocr(file: UploadFile = File(...)):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(400, "file must be an image")
    try:
        data = await file.read()
        img = Image.open(io.BytesIO(data)).convert("RGB")
    except Exception as e:  # noqa: BLE001
        raise HTTPException(500, f"failed to read image: {e}")

    # OCR the original and a preprocessed copy, keep whichever yields the most
    # Cyrillic text (cursive recognition is noisy; a cheap ensemble helps).
    variants = [("original", img)]
    prepared = _preprocess(img)
    if prepared is not None and prepared is not img:
        variants.append(("preprocessed", prepared))

    best = ("", "none")
    errors = []
    ran_ok = 0
    for variant_name, variant in variants:
        for engine, fn in (("pytesseract", _ocr_with_pytesseract), ("easyocr", _ocr_with_easyocr)):
            try:
                text, conf = fn(variant)
                text = text or ""
            except Exception as e:  # noqa: BLE001
                errors.append(f"{engine}({variant_name}): {e}")
                continue
            ran_ok += 1
            if _score(text) > _score(best[0]) or (best[0] == "" and text.strip()):
                best = (text, f"{engine}/{variant_name}")
            if engine == "pytesseract":
                # Confident print text: Tesseract is the better engine, stop.
                if text.strip() and (conf or 0.0) >= _TESS_MIN_CONF:
                    return OCRResponse(text=text.strip(), engine=f"{engine}/{variant_name}")
            # good enough early exit: two or more Cyrillic words recognised
            elif _score(text) >= 10:
                return OCRResponse(text=text.strip(), engine=f"{engine}/{variant_name}")

    if best[0].strip():
        return OCRResponse(text=best[0].strip(), engine=best[1])
    if ran_ok == 0:
        raise HTTPException(500, "OCR unavailable: " + " | ".join(errors[:4]))
    # The engines ran fine but the image contains no text (blank/blurred page).
    return OCRResponse(text="", engine="none")
