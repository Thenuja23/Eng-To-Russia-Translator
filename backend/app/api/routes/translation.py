from fastapi import APIRouter
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


@router.post("/", response_model=TranslateResponse)
async def translate(req: TranslateRequest):
    res = service.translate(req.text, src_lang=req.src_lang, tgt_lang=req.tgt_lang, engine=req.engine)
    return TranslateResponse(translated_text=res.text, confidence=res.confidence, meta=res.meta)


@router.get("/engines")
async def engines():
    return {"engines": service.get_available_engines(), "default": settings.default_translator}
