"""End-to-end QA harness for the Russian Cursive Reading Assistant backend.

Run the backend first, then:
    cd backend
    PYTHONPATH=.:$HOME/Library/Python/3.9/lib/python/site-packages \
        python3 scripts/qa.py [http://127.0.0.1:8000]

Exits non-zero if any check fails.
"""
import json
import re
import sys
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"

RESULTS = []


def record(name, ok, detail=""):
    RESULTS.append((name, ok, detail))
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  -- {detail}" if detail else ""))


def request(method, path, body=None, headers=None, origin=None):
    url = BASE + path
    data = None
    hdrs = dict(headers or {})
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        hdrs.setdefault("Content-Type", "application/json")
    if origin:
        hdrs["Origin"] = origin
    req = urllib.request.Request(url, data=data, method=method, headers=hdrs)
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            raw = r.read().decode("utf-8")
            return r.status, dict(r.headers), raw
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read().decode("utf-8")
    except Exception as e:  # noqa: BLE001
        return 0, {}, f"EXC: {e}"


def jget(raw):
    try:
        return json.loads(raw)
    except Exception:
        return None


def translate(text, src="en", tgt="ru", engine=None, **extra):
    body = {"text": text, "src_lang": src, "tgt_lang": tgt}
    if engine:
        body["engine"] = engine
    body.update(extra)
    return request("POST", "/translation/", body)


# ---------------------------------------------------------------- health
st, hdr, raw = request("GET", "/health")
record("GET /health -> 200 ok", st == 200 and jget(raw) == {"status": "ok"}, f"{st} {raw}")

# ---------------------------------------------------------------- CORS
ORIGIN = "http://127.0.0.1:5173"
st, hdr, raw = request("OPTIONS", "/translation/", body=None, headers={
    "Access-Control-Request-Method": "POST",
    "Access-Control-Request-Headers": "content-type",
}, origin=ORIGIN)
allow_origin = hdr.get("access-control-allow-origin") or hdr.get("Access-Control-Allow-Origin")
record("CORS preflight allows browser origin", allow_origin in ("*", ORIGIN),
       f"status={st} allow-origin={allow_origin}")

st, hdr, raw = request("POST", "/translation/", {"text": "hello", "src_lang": "en", "tgt_lang": "ru"}, origin=ORIGIN)
allow_origin = hdr.get("access-control-allow-origin") or hdr.get("Access-Control-Allow-Origin")
record("CORS header on actual POST", allow_origin in ("*", ORIGIN), f"allow-origin={allow_origin}")

# ---------------------------------------------------------------- engines
st, hdr, raw = request("GET", "/translation/engines")
d = jget(raw)
record("GET /translation/engines lists opustmt", st == 200 and d and "opustmt" in d.get("engines", []), raw)
details = d.get("details", []) if d else []
google_detail = next((item for item in details if item.get("id") == "google"), {})
record("GET /translation/engines exposes details + Google status",
       bool(st == 200 and isinstance(details, list) and "google_configured" in d
            and google_detail and "available" in google_detail),
       raw[:200])

# ---------------------------------------------------------------- basic translation
st, hdr, raw = translate("I need a visa and my passport", "en", "ru")
d = jget(raw)
ok = st == 200 and d and re.search(r"[А-Яа-яЁё]", d.get("translated_text", ""))
record("en->ru produces Cyrillic", bool(ok), raw[:160])
record("en->ru scripted model (opus-mt), no glossary fallback",
       bool(d and d.get("meta", {}).get("engine") == "opustmt"), raw[:160])

st, hdr, raw = translate("Мне нужна виза", "ru", "en")
d = jget(raw)
ok = st == 200 and d and re.search(r"[A-Za-z]", d.get("translated_text", ""))
record("ru->en produces Latin", bool(ok), raw[:160])

# ---------------------------------------------------------------- token protection
src = "Please email teacher@university.ru before 15.10.2026 about CS-101"
st, hdr, raw = translate(src, "en", "ru")
d = jget(raw)
out = d.get("translated_text", "") if d else ""
record("en->ru keeps email", "teacher@university.ru" in out, out)
record("en->ru keeps date", "15.10.2026" in out, out)
record("en->ru keeps course code", "CS-101" in out, out)
record("en->ru all placeholders restored", bool(d and d["meta"].get("all_placeholders_restored")), out)

src = "Иван Петров учится с 2021 года, телефон 89261234567"
st, hdr, raw = translate(src, "ru", "en")
d = jget(raw)
out = d.get("translated_text", "") if d else ""
record("ru->en keeps number", "89261234567" in out, out)
record("ru->en keeps person name", "Иван Петров" in out, out)

# ---------------------------------------------------------------- edge inputs
st, hdr, raw = translate("", "en", "ru")
d = jget(raw)
record("empty text -> 200 with empty output", st == 200 and d is not None and d.get("translated_text", "") == "", f"{st} {raw[:120]}")

st, hdr, raw = translate("   ", "en", "ru")
record("whitespace-only text -> 200", st == 200, f"{st} {raw[:120]}")

st, hdr, raw = request("POST", "/translation/", {"text": "hello"})
d = jget(raw)
record("missing src/tgt uses defaults", st == 200 and d is not None, f"{st} {raw[:120]}")

st, hdr, raw = translate("bonjour le monde", "fr", "de")
d = jget(raw) or {}
meta = d.get("meta", {})
record("unsupported lang pair returns clear signal (not silent passthrough)",
       st != 200 or bool(meta.get("error") or meta.get("unsupported")), f"{st} {raw[:160]}")

st, hdr, raw = translate("hello", "en", "ru", engine="does-not-exist")
record("unknown engine does not 500", st == 200, f"{st} {raw[:120]}")

st, hdr, raw = translate("hi", "en", "ru", engine="nllb")
d = jget(raw) or {}
meta = d.get("meta", {})
record("engine=nllb does not hang/crash (clear result or clear error)",
       st == 200 and bool(d.get("translated_text") or meta.get("error")), f"{st} {raw[:160]}")

# only digits / emails
st, hdr, raw = translate("12345 67890", "en", "ru")
d = jget(raw)
record("numeric-only text round-trips digits", bool(d and "12345" in d.get("translated_text", "") and "8926123" not in ""), f"{raw[:140]}")

# token-only input: nothing to translate, but it must not look like a failure
st, hdr, raw = translate("anna@example.com", "en", "ru")
d = jget(raw) or {}
record("token-only input avoids false failure warning",
       st == 200 and d.get("translated_text") == "anna@example.com"
       and not d.get("meta", {}).get("failed")
       and d.get("meta", {}).get("engine") == "opustmt",
       raw[:200])

# plain course code without a hyphen (CS101) is data, not a failed translation
st, hdr, raw = translate("CS101", "en", "ru")
d = jget(raw) or {}
record("plain course code is preserved without false failure",
       st == 200 and d.get("translated_text") == "CS101"
       and not d.get("meta", {}).get("failed")
       and d.get("meta", {}).get("engine") == "opustmt",
       raw[:200])

# placeholder collision: user text literally contains a placeholder-looking token
st, hdr, raw = translate("The code OPU_0001 must stay OPU_0001", "en", "ru")
d = jget(raw) or {}
out = d.get("translated_text", "")
record("user text containing placeholder-like token is not corrupted",
       "OPU_0001" in out, f"{out}")

# unicode / emoji
st, hdr, raw = translate("Hello 😀 мир", "en", "ru")
record("emoji/mixed input does not 500", st == 200, f"{st} {raw[:120]}")

# long text completeness (model max length is 512 tokens)
st, hdr, raw = translate("I need a visa and my passport " * 40, "en", "ru")
d = jget(raw)
out = d.get("translated_text", "") if d else ""
record("long text not silently truncated",
       st == 200 and len(out) > 200,
       f"out_len={len(out)} (input_len={len('I need a visa and my passport ' * 40)})")

# ---------------------------------------------------------------- malformed input
st, hdr, raw = request("POST", "/translation/", body=None, headers={"Content-Type": "application/json"})
record("empty body -> 422 not 500", st == 422, f"{st}")

req = urllib.request.Request(BASE + "/translation/", data=b"{not json", method="POST",
                             headers={"Content-Type": "application/json"})
try:
    with urllib.request.urlopen(req, timeout=30) as r:
        st = r.status
except urllib.error.HTTPError as e:
    st = e.code
record("malformed JSON -> 422 not 500", st == 422, f"{st}")

st, hdr, raw = request("POST", "/translation/", {"text": 12345, "src_lang": "en", "tgt_lang": "ru"})
record("wrong type for text handled (422 or coerced)", st in (200, 422), f"{st}")

# ---------------------------------------------------------------- text processing
st, hdr, raw = request("POST", "/text/process", {"text": "Привет мир\n\nHello world"})
d = jget(raw)
record("/text/process segments mixed text", st == 200 and d and len(d.get("segments", [])) >= 2, raw[:200])

st, hdr, raw = request("POST", "/text/process", {"text": ""})
d = jget(raw)
record("/text/process empty -> 200 empty list", st == 200 and d and d.get("segments") == [], raw[:120])

st, hdr, raw = request("POST", "/text/process", {"text": "😀😀😀"})
d = jget(raw)
record("/text/process emoji-only -> 200", st == 200 and d is not None, raw[:160])

# ---------------------------------------------------------------- feedback
st, hdr, raw = request("POST", "/feedback/", {"message": "great app", "category": "bug"})
record("/feedback/ endpoint exists", st in (200, 201), f"{st} {raw[:120]}")

# ---------------------------------------------------------------- concurrency
def one(i):
    text = f"Request number 1000{i} from user{i}@example.com"
    st, _, raw = translate(text, "en", "ru")
    d = jget(raw) or {}
    out = d.get("translated_text", "")
    return st == 200 and f"1000{i}" in out and f"user{i}@example.com" in out

with ThreadPoolExecutor(max_workers=6) as ex:
    results = list(ex.map(one, range(6)))
record("6 concurrent requests keep their own tokens", all(results), f"{results}")

# ---------------------------------------------------------------- summary
failed = [r for r in RESULTS if not r[1]]
print("\n" + "=" * 60)
print(f"{len(RESULTS) - len(failed)}/{len(RESULTS)} checks passed")
if failed:
    print("FAILURES:")
    for name, _, detail in failed:
        print(f"  - {name}  ({detail[:120]})")
    sys.exit(1)
print("ALL CHECKS PASSED")
