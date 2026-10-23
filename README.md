# Russian Cursive Learning & Reading Assistant

A mobile-friendly PWA that helps foreign students in Russia, beginners, and anyone
who struggles with Russian handwriting to write, read and understand Russian
cursive. The interface is English-first: users read English, not Russian.

## Features

- **English → Russian** translation with a cursive handwriting preview
  (Bad Script / Marck Script / Caveat), plus download-as-image.
- **Russian keyboard → English** and **Latin-phonetic → Russian** input modes.
- **Two-stage pipeline only** (source → Russian/English → target); Opus-MT by
  default, NLLB opt-in. No direct image → English shortcut.
- **Token protection**: e-mails, URLs, dates, times, numbers (including
  `1,234.56`), course codes and Russian names survive verbatim or the response
  is flagged.
- **Image / camera OCR** with Tesseract first and EasyOCR fallback for
  handwriting.
- **Per-block Copy**, **Copy both** and **Copy all**.
- **Listen** buttons (browser speech synthesis) and a Cyrillic → Latin
  **transliteration** reading aid on Russian output.
- **Translation history** stored on the device, restorable, with **Anki CSV**
  export for spaced repetition.
- **Optional multi-provider AI** (ChatGPT + Claude + Perplexity) used as one
  consensus ensemble for translation, review and explanations. Fully optional:
  the app works offline with the local model when no keys are set.
- Light / dark theme.

## Quick Start

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

Backend: <http://127.0.0.1:8000> · Frontend: <http://127.0.0.1:5173>

### OCR engines (image / camera input)

Printed text is read with **Tesseract** when the binary is available, falling
back to **EasyOCR** (which also handles handwriting / cursive better).
Install the better print engine with Russian language data:

```bash
brew install tesseract tesseract-lang   # macOS
```

## Optional AI ensemble (ChatGPT + Claude + Perplexity)

The AI layer is **off by default until a key is added**. Keys live only on the
server; the browser never receives them.

```bash
cd backend
cp .env.example .env
# edit .env and set any of:
#   OPENAI_API_KEY=sk-...
#   ANTHROPIC_API_KEY=sk-ant-...
#   PERPLEXITY_API_KEY=pplx-...
uvicorn app.main:app --reload   # restart after editing .env
```

Every configured provider answers the same prompt in parallel. Answers are
ranked by:

1. protected-token survival (hard requirement — candidates that lose a token
   are rejected),
2. agreement with the other providers (consensus),
3. sentence completeness,
4. correct script,
5. closeness to the existing translation (review mode only).

The best answer is returned, and every candidate is shown in the **AI** tab so
the result is transparent. Endpoints:

| Endpoint | Purpose |
| --- | --- |
| `GET /ai/status` | Providers, models, limits, setup hints |
| `POST /ai/translate` | Ensemble translation |
| `POST /ai/enhance` | Review / improve an existing translation |
| `POST /ai/explain` | Tutor-style explanation (meaning, grammar, reading) |

Without keys these return `503` with setup instructions, and the Write page
simply hides the AI cards. Results are cached (default 15 min) and rate limited
per IP (default 20 requests/min).

Relevant settings (see `backend/.env.example`): `AI_ENABLED`,
`AI_PROVIDER_ORDER`, `AI_MAX_REQUESTS_PER_MINUTE`, `AI_MAX_CHARS`,
`AI_CACHE_TTL_SECONDS`, `AI_TIMEOUT_SECONDS`, and per-provider model names.

## Tests

```bash
cd backend

# Core API/regression checks (31 checks)
PYTHONPATH=. python3 scripts/qa.py

# Accuracy gate: translation, sentence completeness, token protection, OCR
PYTHONPATH=. python3 scripts/accuracy_test.py

# AI ensemble with mock providers (no network or keys needed)
PYTHONPATH=. python3 scripts/ai_test.py
```

The accuracy suite scores translation quality, sentence completeness, verbatim
token protection (e-mails, URLs, dates, times, numbers, course codes) and OCR
against known ground truth. It exits non-zero if token protection drops below
100 %.

## Structure

- `backend/app/api/routes/` — translation, text, feedback, OCR, AI endpoints
- `backend/app/services/translation/` — Opus-MT/NLLB pipeline, token protector
- `backend/app/services/ai/` — provider clients, consensus ensemble, cache,
  rate limiter, prompts
- `frontend/src/components/` — cursive renderer, keyboards, OCR input, AI studio,
  history, study tools
- `frontend/src/pages/WritingPage.jsx` — the three writing modes
- `backend/scripts/` — QA, accuracy and AI mock test suites
