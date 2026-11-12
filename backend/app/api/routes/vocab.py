"""Vocabulary analysis endpoint.

The learner's text arrives from the microphone, an uploaded picture or the
keyboard. This route returns one card per Russian word.

Order of preference:

1. the AI ensemble, when at least one provider key is configured — it gives the
   richest analysis (context-aware meanings, natural example sentences);
2. the built-in offline engine — a curated Russian dictionary plus ending-based
   grammar rules, so the feature works with no keys and no network.

The response always says which mode produced it.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from app.core.config import settings
from app.services.ai.ensemble import AiError, AiNotConfigured, Ensemble
from app.services.ai.ratelimit import SlidingWindowLimiter
from app.services.vocab import analyzer, lexicon, morphology, online

router = APIRouter(prefix="/vocab", tags=["vocab"])

ensemble = Ensemble()
limiter = SlidingWindowLimiter(settings.ai_max_requests_per_minute)


class VocabRequest(BaseModel):
    text: str = Field(..., min_length=1)


def _normalise_ai_words(words: list) -> list:
    """Guarantee the fields the UI needs on AI-produced entries."""
    out = []
    for index, item in enumerate(words or []):
        if not isinstance(item, dict) or not item.get("word"):
            continue
        pos = str(item.get("part_of_speech") or "other").lower()
        entry = dict(item)
        entry.setdefault("lemma", "")
        entry["pos_sinhala"] = item.get("pos_sinhala") or morphology.POS_SINHALA.get(
            pos, morphology.POS_SINHALA["other"]
        )
        entry["grammar_sinhala"] = item.get("grammar_sinhala") or (
            morphology.POS_GRAMMAR_SINHALA.get(pos, morphology.POS_GRAMMAR_SINHALA["other"])
        )
        entry["in_dictionary"] = True
        entry["meaning_source"] = "ai"
        entry["occurrences"] = item.get("occurrences") or 1
        out.append(entry)
    return out


@router.get("/status")
def vocab_status():
    """What the vocabulary engine can do right now (no secrets)."""
    configured = len([p for p in ensemble.providers if p.configured])
    return {
        "mode": "ai" if configured and settings.ai_enabled else "offline",
        "ai_configured_providers": configured,
        "dictionary_words": lexicon.size(),
        "online_lookup": online.enabled(),
    }


@router.post("/analyze")
def vocab_analyze(req: VocabRequest, request: Request):
    text = (req.text or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="Text is empty.")
    if len(text) > settings.ai_max_chars:
        raise HTTPException(
            status_code=413,
            detail=(
                f"Text too long ({len(text)} characters; limit "
                f"{settings.ai_max_chars})."
            ),
        )

    configured = [p for p in ensemble.providers if p.configured]
    if settings.ai_enabled and configured:
        client = request.client.host if request.client else "unknown"
        allowed, retry_after = limiter.check(f"vocab:{client}")
        if not allowed:
            raise HTTPException(
                status_code=429,
                detail=f"Too many analyses. Try again in {retry_after:.0f}s.",
            )
        try:
            result = ensemble.vocabulary(text)
            words = _normalise_ai_words(result.get("words") or [])
            if words:
                return {
                    **result,
                    "words": words,
                    "source": text,
                    "mode": "ai",
                    "stats": {
                        "total": len(words),
                        "dictionary": len(words),
                        "rule_based": 0,
                        "online_meaning": 0,
                        "online_enabled": online.enabled(),
                    },
                    "notice": "Analysed by the AI ensemble.",
                }
        except (AiNotConfigured, AiError):
            pass  # fall through to the offline engine

    return analyzer.analyze(text)
