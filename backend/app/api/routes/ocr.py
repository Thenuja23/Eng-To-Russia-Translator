from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.core.config import settings
from app.services.ocr.reader import OCRReader

router = APIRouter()

_READER = OCRReader(thorough=True)


class OCRResponse(BaseModel):
    text: str
    engine: str = "unknown"
    confidence: Optional[float] = None


@router.post("/ocr", response_model=OCRResponse)
async def ocr(file: UploadFile = File(...)):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(400, "file must be an image")
    try:
        # Read one byte beyond the configured cap so large uploads are rejected
        # without buffering an unbounded request into memory.
        data = await file.read(settings.max_ocr_upload_bytes + 1)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(500, f"failed to read upload: {e}")
    if len(data) > settings.max_ocr_upload_bytes:
        raise HTTPException(413, "image is too large")
    if not data:
        raise HTTPException(400, "empty image")

    try:
        result = _READER.read(data)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(500, f"OCR unavailable: {e}")

    text = (result.get("text") or "").strip()
    engine = result.get("engine") or "none"
    confidence = result.get("confidence")

    if not text:
        # The engines ran but found no readable text — return 200 with empty
        # text so the UI can prompt the user to try a clearer photo, without
        # treating a blank page as a server error.
        return OCRResponse(text="", engine=engine)

    return OCRResponse(text=text, engine=engine, confidence=confidence)
