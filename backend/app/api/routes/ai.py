"""Optional AI endpoints: multi-provider translation, review and explanation.

All routes work only when at least one provider key is configured; otherwise
they return 503 with actionable setup instructions. Keys stay server-side.
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException, Request, Query
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


class PreferenceRequest(BaseModel):
    provider_mode: str = "auto"
    providers: list[str] = ["openai", "anthropic", "perplexity"]
    translation_mode: str = "accurate"
    level: str = "intermediate"
    explanation_language: str = "en"
    include_grammar: bool = False
    include_examples: bool = True
    history_enabled: bool = False


class CredentialRequest(BaseModel):
    api_key: str = Field(..., min_length=8, max_length=500)
    consent: bool = False


@router.get("/preferences")
def get_ai_preferences(request: Request):
    user = session_user(request.cookies.get(settings.auth_cookie_name))
    if not user:
        raise HTTPException(401, "Sign in to manage AI preferences.")
    prefs = user_store.preferences(user["id"])
    prefs["connected_providers"] = user_store.credential_names(user["id"])
    return prefs


@router.put("/preferences")
def put_ai_preferences(req: PreferenceRequest, request: Request):
    user = session_user(request.cookies.get(settings.auth_cookie_name))
    if not user:
        raise HTTPException(401, "Sign in to manage AI preferences.")
    allowed_providers = {"openai", "anthropic", "perplexity"}
    if req.provider_mode not in {"auto", "custom", "personal"} or not set(req.providers) <= allowed_providers:
        raise HTTPException(422, "Unsupported provider selection.")
    if req.translation_mode not in {"accurate", "natural", "student", "academic", "simple", "context", "grammar"}:
        raise HTTPException(422, "Unsupported translation mode.")
    data = req.model_dump()
    user_store.save_preferences(user["id"], data)
    return {**data, "connected_providers": user_store.credential_names(user["id"])}


@router.put("/credentials/{provider}")
def put_credential(provider: str, req: CredentialRequest, request: Request):
    user = session_user(request.cookies.get(settings.auth_cookie_name))
    if not user:
        raise HTTPException(401, "Sign in to connect a provider.")
    if provider not in {"openai", "anthropic", "perplexity"}:
        raise HTTPException(404, "Unknown provider.")
    if not req.consent:
        raise HTTPException(400, "Explicit provider privacy and billing consent is required.")
    try:
        user_store.ensure_encryption_ready()
        validator = build_providers(provider, {provider: req.api_key.strip()})[0]
        valid, message = validator.validate_key()
        if not valid:
            raise HTTPException(422, message)
        user_store.save_credential(user["id"], provider, req.api_key.strip())
    except RuntimeError as exc:
        raise HTTPException(503, str(exc)) from exc
    return {"provider": provider, "connected": True, "validated": True, "key_returned": False}


@router.delete("/credentials/{provider}")
def delete_credential(provider: str, request: Request, confirm: bool = False):
    user = session_user(request.cookies.get(settings.auth_cookie_name))
    if not user:
        raise HTTPException(401, "Sign in to manage providers.")
    if not confirm:
        raise HTTPException(400, "Set confirm=true to delete this credential.")
    user_store.delete_credential(user["id"], provider)
    return {"provider": provider, "connected": False}


@router.get("/history")
def get_ai_history(request: Request, q: str = Query("", max_length=200), provider: str = "", start: str = "", end: str = ""):
    user = session_user(request.cookies.get(settings.auth_cookie_name))
    if not user:
        raise HTTPException(401, "Sign in to view AI history.")
    return user_store.list_history(user["id"], q, provider, start, end)


@router.delete("/history")
def clear_ai_history(request: Request):
    user = session_user(request.cookies.get(settings.auth_cookie_name))
    if not user:
        raise HTTPException(401, "Sign in to clear AI history.")
    user_store.delete_history(user["id"])
    return {"deleted": True}


@router.delete("/history/{entry_id}")
def delete_ai_history_entry(entry_id: str, request: Request):
    user = session_user(request.cookies.get(settings.auth_cookie_name))
    if not user:
        raise HTTPException(401, "Sign in to delete AI history.")
    user_store.delete_history(user["id"], entry_id)
    return {"deleted": True}


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
def ai_status(request: Request):
    """Provider availability, limits and setup hints (no secrets)."""
    selected, user = _account_ensemble(request)
    result = selected.status()
    result["mode"] = result["mode"] if result["configured"] else "offline"
    if user:
        result["connected_personal"] = user_store.credential_names(user["id"])
        result["preferences"] = user_store.preferences(user["id"])
    return result


@router.post("/translate")
def ai_translate(req: AiTranslateRequest, request: Request):
    """Translate with all configured providers and return the consensus winner."""
    _guard(request, req.text)
    selected, user = _account_ensemble(request)
    prefs = user_store.preferences(user["id"]) if user else {}
    mode = req.translation_mode or prefs.get("translation_mode", "accurate")
    started = __import__("time").perf_counter()
    result = _run(lambda: selected.translate(req.text, src=req.src_lang, tgt=req.tgt_lang, translation_mode=mode))
    if user:
        user_store.add_history(user["id"], req.text, result.get("text", ""), result.get("provider", ""), result.get("model", ""), mode, int((__import__("time").perf_counter()-started)*1000))
    return result


@router.post("/enhance")
def ai_enhance(req: AiEnhanceRequest, request: Request):
    """Review and improve an existing translation, protecting all tokens."""
    _guard(request, req.text, req.translation)
    selected, _ = _account_ensemble(request)
    return _run(lambda: selected.enhance(req.text, req.translation, src=req.src_lang, tgt=req.tgt_lang))


@router.post("/explain")
def ai_explain(req: AiExplainRequest, request: Request):
    """Explain meaning, grammar and cursive reading for a text."""
    _guard(request, req.text)
    selected, user = _account_ensemble(request)
    if user:
        prefs = user_store.preferences(user["id"])
        addenda = [f"Explain at {prefs.get('level', 'intermediate')} university learner level.", f"Write explanations in {prefs.get('explanation_language', 'en')}."]
        if prefs.get("include_grammar"):
            addenda.append("Include relevant grammar and sentence structure analysis.")
        if prefs.get("include_examples"):
            addenda.append("Include at least two useful example sentences.")
        question = "\n".join([req.question or "", *addenda])
    else:
        question = req.question or ""
    return _run(
        lambda: selected.explain(
            req.text,
            req.translation or "",
            src=req.src_lang,
            tgt=req.tgt_lang,
            question=question,
        )
    )


@router.post("/vocab")
def ai_vocab(req: AiVocabRequest, request: Request):
    """Word-by-word vocabulary analysis (EN + Sinhala, POS, grammar, examples)."""
    _guard(request, req.text)
    selected, _ = _account_ensemble(request)
    return _run(lambda: selected.vocabulary(req.text))
