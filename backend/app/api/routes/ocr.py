import os
import httpx
from fastapi import UploadFile, File, HTTPException

@app.post("/ocr")
async def ocr(file: UploadFile = File(...)):
    api_key = os.getenv("OCR_SPACE_API_KEY")
    if not api_key:
        raise HTTPException(503, "OCR is not configured")

    content = await file.read()
    if len(content) > 1_000_000:
        raise HTTPException(413, "Image must be under 1 MB")

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(
                "https://api.ocr.space/parse/image",
                data={"apikey": api_key, "language": "eng", "OCREngine": "2"},
                files={"file": (file.filename, content, file.content_type)},
            )
        r.raise_for_status()
    except httpx.HTTPError as e:
        raise HTTPException(502, f"OCR service error: {e}")

    result = r.json()
    if result.get("IsErroredOnProcessing"):
        raise HTTPException(502, str(result.get("ErrorMessage")))

    text = " ".join(p["ParsedText"] for p in result["ParsedResults"]).strip()
    return {"text": text}