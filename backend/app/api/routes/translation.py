from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any

from app.services.translation.translator_service import TranslationService
from app.core.config import settings


router = APIRouter(prefix="/translation", tags=["translation"])


class TranslateRequest(BaseModel):
    text: str
    src_lang: str = "ru"
    tgt_lang: str = "en"
    engine: Optional[str] = None


class TranslateResponse(BaseModel):
    translated_text: str
    confidence: float
    meta: Dict[str, Any]


service = TranslationService(default=settings.default_translator, device=settings.device)


# NOTE: sync `def` on purpose — FastAPI runs sync handlers in a threadpool so the
# CPU-bound model inference does not block the event loop for other requests.
@router.post("/", response_model=TranslateResponse)
def translate(req: TranslateRequest):
    if len(req.text) > settings.max_text_chars:
        raise HTTPException(
            status_code=413,
            detail=f"text too long: {len(req.text)} chars (max {settings.max_text_chars})",
        )
    res = service.translate(req.text, src_lang=req.src_lang, tgt_lang=req.tgt_lang, engine=req.engine)
    return TranslateResponse(translated_text=res.text, confidence=res.confidence, meta=res.meta)


@router.get("/engines")
def engines():
    return {"engines": service.get_available_engines(), "default": settings.default_translator}
