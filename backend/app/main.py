from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import auth, translation, text, feedback, ocr, ai, vocab
from app.core.config import settings
from app.services.auth import db as auth_store
from app.services.auth import sessions


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Accounts, sessions and one-time tokens live in SQLite.
    auth_store.init_db()
    yield


app = FastAPI(title=settings.app_name, version=settings.version, lifespan=lifespan)

# The browser PWA runs on a different origin in some deployments, so CORS must
# be enabled. Credentials are allowed because the session is an HttpOnly cookie;
# the frontend normally talks to this API through the same-origin proxy.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_origin_regex=settings.cors_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Endpoints that expose the learning features. They stay public by default so
# the API can be used as a utility, but setting AUTH_PROTECT_FEATURES=true makes
# the server itself reject anonymous callers (the UI always requires sign-in).
FEATURE_PREFIXES = ("/translation", "/text", "/feedback", "/ocr", "/ai", "/vocab")


@app.middleware("http")
async def enforce_sessions_for_features(request, call_next):
    if (
        settings.auth_protect_features
        and request.method != "OPTIONS"
        and request.url.path.startswith(FEATURE_PREFIXES)
    ):
        user = sessions.session_user(request.cookies.get(settings.auth_cookie_name))
        if user is None:
            return JSONResponse(
                {"detail": "Please sign in to continue."}, status_code=401
            )
    return await call_next(request)


app.include_router(auth.router)
app.include_router(translation.router)
app.include_router(text.router)
app.include_router(feedback.router)
app.include_router(ocr.router)
app.include_router(ai.router)
app.include_router(vocab.router)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/")
async def root():
    return {"app": settings.app_name, "version": settings.version, "docs": "/docs"}
