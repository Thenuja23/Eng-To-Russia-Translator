#!/usr/bin/env python3
"""Accuracy test suite for the Russian Cursive Learning & Reading Assistant.

Scores five areas against known ground truth:

  1. Translation quality    – keyword-group checks, EN->RU and RU->EN
  2. Sentence completeness  – one keyword group per input sentence (catches the
                              known Opus-MT multi-sentence dropping behaviour)
  3. Token protection       – emails / URLs / dates / times / numbers / course
                              codes must survive translation VERBATIM (critical)
  4. OCR accuracy           – generated print-Cyrillic images vs ground truth
                              (cursive rendered too, reported separately as a
                              known model limitation)
  5. Round-trip sanity      – EN->RU->EN token overlap F1 (informational only)

Usage:
    cd backend && PYTHONPATH=. python3 scripts/accuracy_test.py

Exit code is 1 if token protection is not 100 %, if any HTTP call fails, or if
overall translation accuracy drops below 60 % — otherwise 0.
"""
import difflib
import io
import os
import re
import sys

import requests
from PIL import Image, ImageDraw, ImageFont

BASE = os.environ.get("ETR_BASE", "http://127.0.0.1:8000")
TIMEOUT = 180

# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #

transport_errors = []


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "")).strip().lower()


def translate(text: str, src: str, tgt: str) -> dict:
    try:
        r = requests.post(
            f"{BASE}/translation/",
            json={"text": text, "src_lang": src, "tgt_lang": tgt},
            timeout=TIMEOUT,
        )
        if r.status_code != 200:
            transport_errors.append(f"translate HTTP {r.status_code}: {text[:50]!r}")
            return {}
        return r.json()
    except Exception as exc:  # noqa: BLE001
        transport_errors.append(f"translate error: {exc}")
        return {}


def similarity(pred: str, truth: str) -> float:
    return difflib.SequenceMatcher(None, norm(pred), norm(truth)).ratio()


def f1_tokens(a: str, b: str) -> float:
    ta = set(re.findall(r"[a-zа-яё0-9']+", (a or "").lower()))
    tb = set(re.findall(r"[a-zа-яё0-9']+", (b or "").lower()))
    if not ta or not tb:
        return 0.0
    inter = len(ta & tb)
    p, r = inter / len(tb), inter / len(ta)
    return 2 * p * r / (p + r) if (p + r) else 0.0


# --------------------------------------------------------------------------- #
# 1 + 2. translation quality & sentence completeness
# groups = one keyword-alternatives list per input sentence; ALL must match.
# --------------------------------------------------------------------------- #

TRANSLATION_CASES = [
    # --- EN -> RU ---
    dict(lang="en->ru", text="Hello", groups=[["привет", "здравствуй", "здравствуйте"]]),
    dict(lang="en->ru", text="Good morning", groups=[["доброе утро", "доброго утра"]]),
    dict(lang="en->ru", text="Thank you very much", groups=[["спасибо", "благодарю"]]),
    dict(lang="en->ru", text="I am a student", groups=[["студент"]]),
    dict(lang="en->ru", text="I live in London", groups=[["живу", "лондон"]]),
    dict(lang="en->ru", text="I study Russian", groups=[["русск"]]),
    dict(lang="en->ru", text="The weather is nice today",
         groups=[["погод", "хорош", "прекрасн", "отличн", "ясн"]]),
    dict(lang="en->ru", text="How much does this cost?",
         groups=[["стоит", "цена", "сколько", "стоимост"]]),
    dict(lang="en->ru", text="Please open the door", groups=[["двер"]]),
    # multi-sentence: one group per sentence -> catches dropped sentences
    dict(lang="en->ru",
         text="I am a student. I live in London. I study Russian.",
         groups=[["студент"], ["живу", "лондон"], ["русск"]]),
    dict(lang="en->ru",
         text="Good morning. Thank you very much. See you tomorrow.",
         groups=[["добр", "утр"], ["спасибо", "благодар"], ["завтра", "увидимся", "до встречи"]]),
    # --- RU -> EN ---
    dict(lang="ru->en", text="Привет", groups=[["hello", "hi", "hey"]]),
    dict(lang="ru->en", text="Спасибо большое", groups=[["thank", "thanks"]]),
    dict(lang="ru->en", text="Доброе утро", groups=[["good morning", "morning"]]),
    dict(lang="ru->en", text="Я студент", groups=[["student"]]),
    dict(lang="ru->en", text="Где находится вокзал?",
         groups=[["station", "terminal", "where", "train"]]),
    dict(lang="ru->en",
         text="Привет. Спасибо. До свидания.",
         groups=[["hello", "hi", "hey"], ["thank"], ["goodbye", "bye", "see you", "good day"]]),
]

# --------------------------------------------------------------------------- #
# 3. token protection (critical – must be 100 %)
# --------------------------------------------------------------------------- #

TOKEN_CASES = [
    dict(text="Email me at anna.smith@example.com tomorrow",
         src="en", tgt="ru", must=["anna.smith@example.com"]),
    dict(text="Open https://example.com/page?q=1 for the docs",
         src="en", tgt="ru", must=["https://example.com/page?q=1"]),
    dict(text="The meeting is on 2026-10-20 at 15:30",
         src="en", tgt="ru", must=["2026-10-20", "15:30"]),
    dict(text="My course code CS101-2026 starts tomorrow",
         src="en", tgt="ru", must=["CS101-2026"]),
    dict(text="The total is 1,234.56 dollars",
         src="en", tgt="ru", must=["1,234.56"]),
    dict(text="Встреча 20.10.2026 в 15:30",
         src="ru", tgt="en", must=["20.10.2026", "15:30"]),
    dict(text="Напиши на ivan.petrov@example.ru до 31.12.2026",
         src="ru", tgt="en", must=["ivan.petrov@example.ru", "31.12.2026"]),
]

# --------------------------------------------------------------------------- #
# 4. OCR ground-truth images
# --------------------------------------------------------------------------- #

OCR_PRINT_CASES = [
    dict(truth="Привет мир", mode="exact"),                 # word pair
    dict(truth="Москва - столица России", mode="ratio"),    # full sentence
    dict(truth="Код CS101 на почте anna@example.com", mode="tokens",
         must=["cs101", "anna@example.com"]),
]

FONT_CANDIDATES = [
    "/System/Library/Fonts/Supplemental/Times New Roman.ttf",
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/Library/Fonts/Arial.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf",
]
CURSIVE_FONT = "/tmp/badscript.ttf"


def load_font(size: int):
    for path in FONT_CANDIDATES + ([CURSIVE_FONT] if os.path.exists(CURSIVE_FONT) else []):
        try:
            return ImageFont.truetype(path, size)
        except Exception:  # noqa: BLE001
            continue
    return ImageFont.load_default()


def render_image(text: str, size: int = 64, font_path: str = None) -> bytes:
    font = ImageFont.truetype(font_path, size) if font_path else load_font(size)
    width = max(700, int(size * max(len(text), 8) * 0.75))
    img = Image.new("RGB", (width, size + 80), "white")
    draw = ImageDraw.Draw(img)
    draw.text((30, 40), text, fill="black", font=font)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def ocr(png: bytes) -> dict:
    try:
        r = requests.post(f"{BASE}/ocr", files={"file": ("t.png", png, "image/png")},
                          timeout=TIMEOUT)
        if r.status_code != 200:
            transport_errors.append(f"ocr HTTP {r.status_code}")
            return {}
        return r.json()
    except Exception as exc:  # noqa: BLE001
        transport_errors.append(f"ocr error: {exc}")
        return {}


# --------------------------------------------------------------------------- #
# runner
# --------------------------------------------------------------------------- #

def main() -> int:
    print("=" * 74)
    print("ACCURACY TEST SUITE — Russian Cursive Learning & Reading Assistant")
    print("=" * 74)

    # ---------- health ----------
    try:
        requests.get(f"{BASE}/", timeout=10)
    except Exception as exc:  # noqa: BLE001
        print(f"FATAL: backend not reachable at {BASE}: {exc}")
        return 1

    # ---------- 1 + 2. translation ----------
    print("\n[1] TRANSLATION QUALITY & SENTENCE COMPLETENESS")
    print("-" * 74)
    tr_pass = tr_total = 0
    confidences = []
    for case in TRANSLATION_CASES:
        src, tgt = ("en", "ru") if case["lang"] == "en->ru" else ("ru", "en")
        res = translate(case["text"], src, tgt)
        out = res.get("translated_text", "")
        if res.get("confidence") is not None:
            confidences.append(res["confidence"])
        missed = [g[0] for g in case["groups"] if not any(a in norm(out) for a in g)]
        ok = bool(out) and not missed
        tr_total += 1
        tr_pass += ok
        mark = "PASS" if ok else "FAIL"
        print(f"  {mark} [{case['lang']}] {case['text'][:46]!r}")
        print(f"         -> {out[:78]!r}")
        if missed:
            print(f"         missing sentence keyword(s): {missed}")
    tr_pct = 100.0 * tr_pass / tr_total if tr_total else 0.0
    mean_conf = sum(confidences) / len(confidences) if confidences else 0.0
    print(f"  => {tr_pass}/{tr_total} ({tr_pct:.0f}%)  mean confidence {mean_conf:.2f}")

    # ---------- 3. token protection ----------
    print("\n[2] TOKEN PROTECTION (critical — must survive verbatim)")
    print("-" * 74)
    tok_pass = tok_total = 0
    for case in TOKEN_CASES:
        res = translate(case["text"], case["src"], case["tgt"])
        out = res.get("translated_text", "")
        missing = [t for t in case["must"] if t not in out]
        tok_total += 1
        ok = not missing and bool(out)
        tok_pass += ok
        mark = "PASS" if ok else "FAIL"
        print(f"  {mark} {case['text'][:44]!r}")
        print(f"         -> {out[:78]!r}")
        if missing:
            print(f"         LOST token(s): {missing}")
    tok_pct = 100.0 * tok_pass / tok_total if tok_total else 0.0
    print(f"  => {tok_pass}/{tok_total} ({tok_pct:.0f}%)")

    # ---------- 4. OCR ----------
    print("\n[3] OCR ACCURACY (generated print-Cyrillic images)")
    print("-" * 74)
    ocr_pass = ocr_total = 0
    ratios = []
    for case in OCR_PRINT_CASES:
        res = ocr(render_image(case["truth"]))
        pred = res.get("text", "")
        sim = similarity(pred, case["truth"])
        ratios.append(sim)
        if case["mode"] == "exact":
            ok = sim >= 0.9
        elif case["mode"] == "tokens":
            ok = all(t in norm(pred) for t in case["must"])
        else:  # ratio
            ok = sim >= 0.75
        ocr_total += 1
        ocr_pass += ok
        mark = "PASS" if ok else "FAIL"
        print(f"  {mark} truth={case['truth']!r}")
        print(f"         pred={pred.strip()!r}  similarity={sim:.2f}  engine={res.get('engine', '?')}")
    ocr_pct = 100.0 * ocr_pass / ocr_total if ocr_total else 0.0
    mean_sim = sum(ratios) / len(ratios) if ratios else 0.0
    print(f"  => {ocr_pass}/{ocr_total} ({ocr_pct:.0f}%)  mean char similarity {mean_sim:.2f}")

    # cursive (informational – known model limitation)
    if os.path.exists(CURSIVE_FONT):
        truth = "привет мир"
        res = ocr(render_image(truth, font_path=CURSIVE_FONT))
        pred = res.get("text", "")
        sim = similarity(pred, truth)
        print(f"  [known limitation] cursive truth={truth!r} pred={pred.strip()!r} "
              f"similarity={sim:.2f}  (not scored)")
    else:
        print(f"  [skip] cursive font {CURSIVE_FONT} not found (not scored)")

    # ---------- 5. round-trip (informational) ----------
    print("\n[4] ROUND-TRIP SANITY EN->RU->EN (informational)")
    print("-" * 74)
    rt_scores = []
    for sentence in ["Hello world", "I am a student", "Thank you very much"]:
        ru = translate(sentence, "en", "ru").get("translated_text", "")
        back = translate(ru, "ru", "en").get("translated_text", "") if ru else ""
        score = f1_tokens(sentence, back)
        rt_scores.append(score)
        print(f"  {sentence!r} -> {ru!r} -> {back!r}  F1={score:.2f}")
    rt_mean = sum(rt_scores) / len(rt_scores) if rt_scores else 0.0
    print(f"  => mean token F1 {rt_mean:.2f}")

    # ---------- summary ----------
    print("\n" + "=" * 74)
    print("SUMMARY")
    print("=" * 74)
    print(f"  Translation + sentence completeness : {tr_pass}/{tr_total} ({tr_pct:.0f}%)")
    print(f"  Token protection (critical)         : {tok_pass}/{tok_total} ({tok_pct:.0f}%)")
    print(f"  OCR (print Cyrillic)                : {ocr_pass}/{ocr_total} ({ocr_pct:.0f}%)")
    print(f"  Round-trip F1 (informational)       : {rt_mean:.2f}")
    if transport_errors:
        print(f"\n  TRANSPORT ERRORS ({len(transport_errors)}):")
        for e in transport_errors:
            print(f"    - {e}")

    failed = False
    if tok_pct < 100.0:
        print("\nRESULT: FAIL — token protection must be 100%")
        failed = True
    if transport_errors:
        print("\nRESULT: FAIL — transport errors occurred")
        failed = True
    if tr_pct < 60.0:
        print(f"\nRESULT: FAIL — translation accuracy {tr_pct:.0f}% < 60%")
        failed = True
    if not failed:
        print("\nRESULT: PASS")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
