"""Optional AI endpoints: multi-provider translation, review and explanation.

All routes work only when at least one provider key is configured; otherwise
they return 503 with actionable setup instructions. Keys stay server-side.
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from app.core.config import settings
from app.services.ai.ensemble import AiError, AiNotConfigured, Ensemble
from app.services.ai.ratelimit import SlidingWindowLimiter
from app.services.ai import user_store
from app.services.ai.providers import build_providers
from app.services.auth.sessions import session_user

router = APIRouter(prefix="/ai", tags=["ai"])

ensemble = Ensemble()
limiter = SlidingWindowLimiter(settings.ai_max_requests_per_minute)


class AiTranslateRequest(BaseModel):
    text: str = Field(..., min_length=1)
    src_lang: str = "en"
    tgt_lang: str = "ru"
    translation_mode: str = "accurate"


class AiEnhanceRequest(BaseModel):
    text: str = Field(..., min_length=1)
    translation: str = Field(..., min_length=1)
    src_lang: str = "en"
    tgt_lang: str = "ru"


class AiExplainRequest(BaseModel):
    text: str = Field(..., min_length=1)
    translation: Optional[str] = None
    src_lang: str = "en"
    tgt_lang: str = "ru"
    question: Optional[str] = None


class AiVocabRequest(BaseModel):
    text: str = Field(..., min_length=1)


def _guard(request: Request, *texts: str) -> None:
    if not settings.ai_enabled:
        raise HTTPException(
            status_code=503,
            detail="AI features are disabled on this server (AI_ENABLED=false).",
        )
    for text in texts:
        if len(text or "") > settings.ai_max_chars:
            raise HTTPException(
                status_code=413,
                detail=(
                    f"Text too long for AI ({len(text)} characters; limit "
                    f"{settings.ai_max_chars})."
                ),
            )
    client = request.client.host if request.client else "unknown"
    allowed, retry_after = limiter.check(f"ai:{client}")
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail=f"Too many AI requests. Try again in {retry_after:.0f}s.",
        )


def _run(fn):
    try:
        return fn()
    except AiNotConfigured as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except AiError as exc:
        raise HTTPException(status_code=502, detail=str(exc))


def _account_ensemble(request: Request) -> tuple[Ensemble, dict | None]:
    user = session_user(request.cookies.get(settings.auth_cookie_name))
    if not user:
        # Preserve public API compatibility for deployments that allow anonymous API calls.
        return ensemble, None
    prefs = user_store.preferences(user["id"])
    personal = user_store.get_credentials(user["id"]) if user_store.credential_names(user["id"]) else {}
    mode = prefs.get("provider_mode", "auto")
    selected = prefs.get("providers", ["openai", "anthropic", "perplexity"])
    if mode == "personal":
        credentials = personal
    elif mode == "custom":
        credentials = {k: personal[k] for k in selected if k in personal}
        # Custom selections use personal keys only to avoid an unexpected bill.
    else:
        credentials = {**{k: getattr(settings, f"{k}_api_key") for k in selected if getattr(settings, f"{k}_api_key", None)}, **personal}
    if mode in ("custom", "personal"):
        order = ",".join(selected)
    else:
        order = ",".join(selected)
    models = {k: getattr(settings, f"{k}_model") for k in ("openai", "anthropic", "perplexity")}
    providers = build_providers(order, credentials, models)
    providers = [p for p in providers if p.name in selected]
    return Ensemble(providers=providers), user


@router.get("/status")
def ai_status():
    """Provider availability, limits and setup hints (no secrets)."""
    return ensemble.status()


@router.post("/translate")
def ai_translate(req: AiTranslateRequest, request: Request):
    """Translate with all configured providers and return the consensus winner."""
    _guard(request, req.text)
    return _run(
        lambda: ensemble.translate(
            req.text, src=req.src_lang, tgt=req.tgt_lang
        )
    )


@router.post("/enhance")
def ai_enhance(req: AiEnhanceRequest, request: Request):
    """Review and improve an existing translation, protecting all tokens."""
    _guard(request, req.text, req.translation)
    return _run(
        lambda: ensemble.enhance(
            req.text, req.translation, src=req.src_lang, tgt=req.tgt_lang
        )
    )


@router.post("/explain")
def ai_explain(req: AiExplainRequest, request: Request):
    """Explain meaning, grammar and cursive reading for a text."""
    _guard(request, req.text)
    return _run(
        lambda: ensemble.explain(
            req.text,
            req.translation or "",
            src=req.src_lang,
            tgt=req.tgt_lang,
            question=req.question or "",
        )
    )


@router.post("/vocab")
def ai_vocab(req: AiVocabRequest, request: Request):
    """Word-by-word vocabulary analysis (EN + Sinhala, POS, grammar, examples)."""
    _guard(request, req.text)
    return _run(lambda: ensemble.vocabulary(req.text))
