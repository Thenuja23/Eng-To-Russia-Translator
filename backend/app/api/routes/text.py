from fastapi import APIRouter, HTTPException
from app.services.text_input.pipeline import TextPipeline
from app.schemas.text import TextProcessRequest, TextProcessResponse, TextSegment
from app.core.config import settings


router = APIRouter(prefix="/text", tags=["text"])


@router.post("/process", response_model=TextProcessResponse)
def process_text(req: TextProcessRequest):
    if len(req.text) > settings.max_text_chars:
        raise HTTPException(
            status_code=413,
            detail=f"text too long: {len(req.text)} chars (max {settings.max_text_chars})",
        )
    if not req.text.strip():
        return TextProcessResponse(segments=[])
    pipeline = TextPipeline()
    segs = pipeline.process(req.text)
    return TextProcessResponse(segments=[
        TextSegment(text=s.text, lang=s.lang, direction=s.direction, meta=s.meta) for s in segs
    ])
