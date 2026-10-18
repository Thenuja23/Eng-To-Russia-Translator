from fastapi import FastAPI
from app.api.routes import translation, text

app = FastAPI(title="Russian Cursive Learning & Reading Assistant", version="0.1.0")

app.include_router(translation.router)
app.include_router(text.router)

@app.get("/health")
async def health():
    return {"status": "ok"}
