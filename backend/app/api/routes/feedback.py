from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional

from app.services.feedback.corrections import CorrectionService


router = APIRouter(prefix="/feedback", tags=["feedback"])
service = CorrectionService()


class FeedbackRequest(BaseModel):
    message: str = Field(default="", max_length=4000)
    category: str = Field(default="general", max_length=40)
    email: Optional[str] = Field(default=None, max_length=200)
    consent_to_train: bool = False


@router.post("/")
def submit_feedback(req: FeedbackRequest):
    service.submit(req.model_dump())
    return {"status": "ok", "received": True}


@router.get("/")
def feedback_info():
    return {
        "status": "ok",
        "count": service.count(),
        "usage": "POST {message, category, email?, consent_to_train?}",
    }
