# Russian Cursive Learning & Reading Assistant

A mobile-friendly PWA that helps foreign students in Russia, beginners, and anyone who struggles with Russian handwriting to write, read and understand Russian cursive. Users read English, not Russian.

## Step 1 - Status
Completed basic project scaffolding with:
- Backend (FastAPI) skeleton with `/health` endpoint
- Frontend base structure (React PWA + Tailwind - to be initialized)
- Cursive renderer, font test, keyboard components (planned under frontend/src/components)
- Copy buttons utilities (planned under frontend/src/lib)
- Phonetic keyboard and on-screen Russian keyboard (planned)

## Quick Start (TBD)
Backend: `cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload`
Frontend: `cd frontend && npm install && npm run dev`

### OCR engines (image / camera input)
Printed text is read with **Tesseract** when the binary is available, falling
back to **EasyOCR** (which also handles handwriting / cursive better).
Install the better print engine with Russian language data:

```bash
brew install tesseract tesseract-lang   # macOS
```

### Accuracy suite
```bash
cd backend && PYTHONPATH=. python3 scripts/accuracy_test.py
```
Scores translation quality, sentence completeness, verbatim token protection
(e-mails, URLs, dates, times, numbers, course codes) and OCR against known
ground truth. Exits non-zero if token protection drops below 100 %.

## Structure
See folder structure as specified in project requirements.
