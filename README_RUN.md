# How to Run

## 1) Backend (FastAPI)
```bash
cd "/Users/thenuja_ganganath/Ceylonforce_Projects/Eng To Russia Translator/backend"
PYTHONPATH=/Users/thenuja_ganganath/Library/Python/3.9/lib/python/site-packages:/Users/thenuja_ganganath/Ceylonforce_Projects/Eng\ To\ Russia\ Translator/backend python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

API docs: http://127.0.0.1:8000/docs
Health: http://127.0.0.1:8000/health

## 2) Frontend (React PWA + Vite)
```bash
cd "/Users/thenuja_ganganath/Ceylonforce_Projects/Eng To Russia Translator/frontend"
node node_modules/vite/bin/vite.js --host 127.0.0.1 --port 5173
```

Open: http://127.0.0.1:5173

## Translation engines (important)
The translation service tries engines in this order:

1. **Opus-MT** (default, locked decision) - requires `torch` + `transformers` + `sentencepiece`.
2. **NLLB-200 distilled 600M** (`engine: "nllb"`) - non-commercial licence, flagged in meta.
3. **Offline glossary fallback** - used automatically only when (1)/(2) are unavailable.
   - Flagged in the response as `"fallback": "offline_glossary"` with a `notice`.
   - Limited vocabulary; grammar is rough. It exists so the app still works without models.

### Enable real Opus-MT translation
```bash
pip3 install --user torch transformers sentencepiece sacremoses
```
Then restart the backend. Models download from Hugging Face on first use
(~300 MB per direction). No code change needed - the fallback switches off
automatically and the notice disappears from the UI.

## Docker (optional)
```bash
cd "/Users/thenuja_ganganath/Ceylonforce_Projects/Eng To Russia Translator/infra"
docker-compose up --build
```
