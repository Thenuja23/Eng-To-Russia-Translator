from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import translation, text, feedback, ocr
from app.core.config import settings

app = FastAPI(title=settings.app_name, version=settings.version)

# The browser PWA runs on a different origin (e.g. :5173) than the API (:8000),
# so CORS must be enabled or every fetch is blocked by the browser.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_origin_regex=settings.cors_origin_regex,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

app.include_router(translation.router)
app.include_router(text.router)
app.include_router(feedback.router)
app.include_router(ocr.router)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/")
async def root():
    return {"app": settings.app_name, "version": settings.version, "docs": "/docs"}
