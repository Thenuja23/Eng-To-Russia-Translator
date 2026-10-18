from fastapi import APIRouter

router = APIRouter(prefix="/feedback", tags=["feedback"])

@router.post("/")
async def submit_feedback():
    return {"status": "ok"}
