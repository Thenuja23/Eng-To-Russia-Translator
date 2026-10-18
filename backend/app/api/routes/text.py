from fastapi import APIRouter
from app.services.text_input.pipeline import TextPipeline
from app.schemas.text import TextProcessRequest, TextProcessResponse, TextSegment


router = APIRouter(prefix="/text", tags=["text"])


@router.post("/process", response_model=TextProcessResponse)
async def process_text(req: TextProcessRequest):
    pipeline = TextPipeline()
    segs = pipeline.process(req.text)
    return TextProcessResponse(segments=[
        TextSegment(text=s.text, lang=s.lang, direction=s.direction, meta=s.meta) for s in segs
    ])
