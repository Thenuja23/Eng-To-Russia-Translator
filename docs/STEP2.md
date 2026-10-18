# Step 2 - Translation service (Opus-MT + NLLB) with protected tokens

## Goal
Implement translation service with Opus-MT (ru-en, en-ru) as default and NLLB-200 distilled 600M, with token protection/restore for names, numbers, dates, URLs, emails, course codes.

## Components

### Services
- `services/translation/base.py` - Translator interface, TranslationResult
- `services/translation/token_protector.py` - Protects/restores sensitive tokens; verifies placeholders survive
- `services/translation/opusmt.py` - Opus-MT implementation (lazy load; CPU default)
- `services/translation/nllb.py` - NLLB implementation (non-commercial flag)
- `services/translation/translator_service.py` - Unified service
- `services/translation/__init__.py`

### API
- `api/routes/translation.py` - POST /translation/, GET /translation/engines

### Core/Schemas
- `core/config.py` - settings (device, defaults, model names, flags)
- `schemas/translation.py` - request/response models
- `main.py` - includes router

## Decisions
- Protect before translation, restore after. Verify all placeholders restored; flag if lost.
- NLLB marked non-commercial in meta.
- Lazy loading to avoid heavy deps at import if not needed; graceful error handling.

## Tests
- Token roundtrip: emails/URLs/dates/numbers/course codes/names
- Empty text handled
- Engines endpoint returns both
- License flag present for NLLB
- Placeholder loss detection

## Done when
✓ All files created and API routes registered ✓ Token protector preserves and restores all specified types ✓ Meta includes license flag for NLLB ✓ Structure matches spec
