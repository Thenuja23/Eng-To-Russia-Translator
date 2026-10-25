"""Clean-up and repair of raw OCR output.

Recognition engines make predictable mistakes: Latin/Cyrillic look-alikes
inside Russian words, e-mail addresses split around ``@``/dots, course codes
with ``O`` instead of zero, spaces before punctuation and hyphenated line
breaks. Fixing those *without* touching genuine Latin tokens is what turns
"almost right" OCR into usable text.
"""
from __future__ import annotations

import re
import unicodedata

CYR_RE = re.compile(r"[А-Яа-яЁё]")
LAT_RE = re.compile(r"[A-Za-z]")
TOKEN_RE = re.compile(r"\S+")

_LAT_TO_CYR = str.maketrans(
    {
        "A": "А", "a": "а",
        "B": "В", "b": "ь",
        "C": "С", "c": "с",
        "E": "Е", "e": "е",
        "H": "Н", "h": "н",
        "K": "К", "k": "к",
        "M": "М", "m": "м",
        "N": "П", "n": "п",
        "O": "О", "o": "о",
        "P": "Р", "p": "р",
        "T": "Т", "t": "т",
        "U": "И", "u": "и",
        "W": "Ш", "w": "ш",
        "X": "Х", "x": "х",
        "Y": "У", "y": "у",
    }
)

_CYR_TO_LAT = str.maketrans(
    {
        "А": "A", "а": "a",
        "В": "B", "в": "b",
        "С": "C", "с": "c",
        "Е": "E", "е": "e",
        "Н": "H", "н": "h",
        "К": "K", "к": "k",
        "М": "M", "м": "m",
        "О": "O", "о": "o",
        "Р": "P", "р": "p",
        "Т": "T", "т": "t",
        "Х": "X", "х": "x",
        "У": "Y", "у": "y",
    }
)

_CONTACT_RE = re.compile(r"@|https?://|www\.", re.IGNORECASE)
_DOMAIN_RE = re.compile(
    r"([A-Za-z0-9._%+-])\s*\.\s*(?=(?:com|ru|org|net|edu|gov|io|co|uk|de|info|biz)\b)",
    re.IGNORECASE,
)


def _normalise_unicode(text: str) -> str:
    text = unicodedata.normalize("NFC", text or "")
    text = (
        text.replace("\u00a0", " ")
        .replace("\u200b", "")
        .replace("\ufeff", "")
        .replace("\r\n", "\n")
        .replace("\r", "\n")
    )
    # Drop control characters but keep newlines and tabs.
    text = "".join(
        ch for ch in text if ch == "\n" or ch >= " " and ch != "\x7f"
    )
    return text


def _fix_script_confusions(text: str) -> str:
    """Repair words that mix Latin look-alikes into Cyrillic (and vice versa)."""
    lines = []
    for line in text.split("\n"):
        pieces = re.split(r"(\s+)", line)
        fixed = []
        for piece in pieces:
            if not piece or piece.isspace():
                fixed.append(piece)
                continue
            if _CONTACT_RE.search(piece):
                fixed.append(piece)
                continue
            cyr = len(CYR_RE.findall(piece))
            lat = len(LAT_RE.findall(piece))
            if not cyr or not lat:
                fixed.append(piece)
                continue
            # Don't destroy real codes such as CS101 or AIT0001.
            if re.search(r"\d", piece) and lat >= cyr:
                fixed.append(piece)
                continue
            if cyr >= lat:
                fixed.append(piece.translate(_LAT_TO_CYR))
            else:
                fixed.append(piece.translate(_CYR_TO_LAT))
        lines.append("".join(fixed))
    return "\n".join(lines)


def _repair_contacts(text: str) -> str:
    text = re.sub(r"(?<=\S)\s*@\s*(?=\S)", "@", text)
    text = re.sub(r"https?\s*:\s*/\s*/", "https://", text, flags=re.IGNORECASE)
    text = re.sub(r"\bwww\s*\.\s*", "www.", text, flags=re.IGNORECASE)
    text = _DOMAIN_RE.sub(r"\1.", text)
    return text


def _repair_codes(text: str) -> str:
    # "CS 101" -> "CS101" (course codes are common in this app's content).
    text = re.sub(r"\b([A-Z]{2,6})\s+(\d{2,4})\b", r"\1\2", text)

    def _digits(match: re.Match) -> str:
        token = match.group(0)
        if not re.search(r"\d", token):
            return token
        return token.translate(str.maketrans({"O": "0", "o": "0", "I": "1", "l": "1", "|": "1"}))

    text = re.sub(r"\b[A-Z]{2,6}[0-9OIl|]{2,4}\b", _digits, text)

    # Fix common OCR confusions inside course-like tokens: С$101, C$101, CS I 01
    def _fix_code_mismatch(match: re.Match) -> str:
        token = match.group(0)
        # normalize
        token = token.replace("$", "S").replace("£", "S")
        token = token.translate(str.maketrans({"С": "C", "с": "c", "О": "O", "о": "o", "Ι": "I", "і": "i"}))
        token = token.translate(str.maketrans({"O": "0", "o": "0", "I": "1", "l": "1"}))
        # prefer letter+digits for course codes like CS101
        m = re.match(r"([A-Za-z]{2,6})[^\w]?([0-9]{2,6})", token)
        if m:
            return (m.group(1) + m.group(2)).upper()
        return token

    text = re.sub(r"\b[\w$£СсОоΙі]{3,10}\d[\w$OIl|]{0,6}\b", _fix_code_mismatch, text)
    text = re.sub(r"\b[A-Za-z]\s*\$\s*\d+\b", _fix_code_mismatch, text)
    return text


def _fix_hyphenation(text: str) -> str:
    # A word split at a line end: "слово-\nпродолжение" -> "словопродолжение".
    return re.sub(r"(?<=[А-Яа-яЁёA-Za-z])-\s*\n\s*(?=[а-яёa-z])", "", text)


def _normalise_spacing(text: str) -> str:
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+([,.;:!?%])", r"\1", text)
    text = re.sub(r"([,;:])(?=[А-Яа-яЁёA-Za-z])", r"\1 ", text)
    text = re.sub(r"\s+([)»”])", r"\1", text)
    text = re.sub(r"([(«“])\s+", r"\1", text)
    text = re.sub(r"\s*[—–]\s*", " — ", text)
    return text


def clean_text(raw: str) -> str:
    text = _normalise_unicode(raw)
    text = _fix_hyphenation(text)
    text = _repair_contacts(text)
    text = _repair_codes(text)
    text = _fix_script_confusions(text)
    text = _normalise_spacing(text)
    return "\n".join(line.strip() for line in text.split("\n")).strip()


def clean_line(raw: str) -> str:
    return clean_text(raw).replace("\n", " ").strip()


def valid_character_ratio(text: str) -> float:
    """Fraction of non-space characters that look like real text/punctuation."""
    characters = [ch for ch in text if not ch.isspace()]
    if not characters:
        return 0.0
    allowed = set(".,;:!?«»\"'()[]{}—-–/@:%+№*#&$")
    good = sum(1 for ch in characters if ch.isalnum() or ch in allowed)
    return good / len(characters)


def has_mixed_scripts(text: str) -> bool:
    for token in TOKEN_RE.findall(text):
        if _CONTACT_RE.search(token):
            continue
        if CYR_RE.search(token) and LAT_RE.search(token):
            cyr = len(CYR_RE.findall(token))
            lat = len(LAT_RE.findall(token))
            # A single Latin character inside a Russian word is the problem.
            if cyr >= 2 and lat >= 1:
                return True
    return False


def looks_like_noise(text: str) -> bool:
    cleaned = (text or "").strip()
    if not cleaned:
        return True
    if len(cleaned) < 2:
        return True
    # e.g. "||||", "~~~~", "...." with no letters/digits
    if not any(ch.isalnum() for ch in cleaned):
        return True
    if valid_character_ratio(cleaned) < 0.55:
        return True
    if re.search(r"([^\w\s])\1{3,}", cleaned):
        return True
    return False
