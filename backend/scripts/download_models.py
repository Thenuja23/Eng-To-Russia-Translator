"""Download and verify the Opus-MT translation models.

Run:
    cd backend
    PYTHONPATH=.:$HOME/Library/Python/3.9/lib/python/site-packages \
        python3 scripts/download_models.py

Downloads (~300 MB per direction) into the Hugging Face cache and runs a
smoke test in both directions. Safe to re-run; cached files are reused.
"""
import os
import sys
import warnings

warnings.filterwarnings("ignore")

# allow running from backend/ without installing the package
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

MODELS = {
    "en-ru": "Helsinki-NLP/opus-mt-en-ru",
    "ru-en": "Helsinki-NLP/opus-mt-ru-en",
}


def download_all():
    from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

    for label, name in MODELS.items():
        print(f"[download] {label}: {name}")
        AutoTokenizer.from_pretrained(name)
        AutoModelForSeq2SeqLM.from_pretrained(name)
        print(f"[ok] {label} cached")


def verify():
    from transformers import pipeline

    print("[verify] en->ru")
    p = pipeline("translation", model=MODELS["en-ru"])
    out = p("I need a visa and my passport", max_length=512)
    print("   ", out[0]["translation_text"])

    print("[verify] ru->en")
    p2 = pipeline("translation", model=MODELS["ru-en"])
    out2 = p2("Привет, как дела?", max_length=512)
    print("   ", out2[0]["translation_text"])


if __name__ == "__main__":
    download_all()
    verify()
    print("[done] models ready")
