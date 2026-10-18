# How to Run

## 0) One-time dependency install (macOS, Python 3.9)
The translation models need `torch` + `transformers`. `numpy` must stay `< 2.0`
for torch 2.1.0 (numpy 2.x breaks `torch`'s NumPy bridge).

```bash
pip3 install --user torch transformers sentencepiece sacremoses
pip3 install --user "numpy<2.0"
```

Then download + verify both Opus-MT directions (~300 MB each, cached in
`~/.cache/huggingface`):
```bash
cd "/Users/thenuja_ganganath/Ceylonforce_Projects/Eng To Russia Translator/backend"
PYTHONPATH=.:$HOME/Library/Python/3.9/lib/python/site-packages \
  python3 scripts/download_models.py
```

## 1) Backend (FastAPI)
```bash
cd "/Users/thenuja_ganganath/Ceylonforce_Projects/Eng To Russia Translator/backend"
PYTHONPATH=.:$HOME/Library/Python/3.9/lib/python/site-packages \
  python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

API docs: http://127.0.0.1:8000/docs
Health: http://127.0.0.1:8000/health

## 2) Frontend (React PWA + Vite)
```bash
cd "/Users/thenuja_ganganath/Ceylonforce_Projects/Eng To Russia Translator/frontend"
node node_modules/vite/bin/vite.js --host 127.0.0.1 --port 5173
```

Open: http://127.0.0.1:5173

## Translation engines
Resolution order:

1. **Opus-MT** (default) - `Helsinki-NLP/opus-mt-en-ru` and `opus-mt-ru-en`.
   Downloads ~300 MB per direction from Hugging Face on first use, then cached
   in `~/.cache/huggingface`. The pipeline is cached in-process.
2. **NLLB-200 distilled 600M** - pass `engine: "nllb"`. Non-commercial licence,
   flagged in the response `meta`.
3. **Offline glossary fallback** - used automatically ONLY when (1)/(2) fail.
   Flagged as `"fallback": "offline_glossary"` and shown as an amber banner in the UI.

When Opus-MT is available, response `meta` looks like:
```json
{"model": "opus-mt", "engine": "opustmt", "all_placeholders_restored": true, "placeholder_strategy": "whole"}
```

## Protected tokens (emails / dates / numbers / names)
Emails, URLs, dates, course codes, numbers and Russian proper names are replaced
by placeholders before translation and restored afterwards, so they are never
altered by the model. If a model rewrites/drops a placeholder, the text is
retranslated segment-by-segment and `meta.placeholder_strategy` becomes
`"segmented"` (tokens guaranteed, slightly lower fluency). If a placeholder is
still missing, `meta.flag` is `PLACEHOLDER_LOSS_DETECTED`.
No `fallback` key, and no warning banner.

## Docker (optional)
```bash
cd "/Users/thenuja_ganganath/Ceylonforce_Projects/Eng To Russia Translator/infra"
docker-compose up --build
```
