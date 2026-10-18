from pydantic import BaseModel
from typing import List, Optional, Dict, Any


class TextSegment(BaseModel):
    text: str
    lang: str = "unknown"
    direction: str = "auto"
    meta: Optional[Dict[str, Any]] = None


class TextProcessRequest(BaseModel):
    text: str


class TextProcessResponse(BaseModel):
    segments: List[TextSegment]
