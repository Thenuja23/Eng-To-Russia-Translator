"""The offline Russian vocabulary engine.

Input: any Russian text (typed, spoken or read from a picture by OCR).
Output: one learner card per distinct word, in the order the words appear, with

    word, pronunciation, English meaning, Sinhala meaning,
    part of speech (+ Sinhala name), grammar explanation (+ Sinhala),
    and two example sentences translated into English and Sinhala.

Nothing is skipped: a word outside the curated dictionary is analysed by rule
(ending-based part of speech and gender), given a pronunciation, and its
meaning is looked up online when that is available. The card says which of
these happened, so a learner always knows how reliable an answer is.
"""
from __future__ import annotations

import re
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Optional

from app.core.config import settings

from . import lexicon, morphology, online

WORD_RE = re.compile(r"[А-Яа-яЁё]+(?:-[А-Яа-яЁё]+)?")

_NOT_FOUND_EN = (
    "No meaning found yet. Check the spelling, or add an AI provider key on the "
    "server for a full analysis."
)
_NOT_FOUND_SI = (
    "මෙම වචනයට තේරුමක් තවම හමු නොවීය. අක්ෂර වින්‍යාසය පරීක්ෂා කරන්න, නැතහොත් සම්පූර්ණ විශ්ලේෂණය සඳහා සේවාදායකයේ AI යතුරක් එක් කරන්න."
)


def _phrase_tokens(text: str) -> List[str]:
    """Word tokens in reading order, merging known multi-word expressions."""
    spans = [(m.group(0), m.start(), m.end()) for m in WORD_RE.finditer(text or "")]
    merged: List[str] = []
    i = 0
    while i < len(spans):
        matched = False
        for size in (3, 2):
            if i + size <= len(spans):
                key = " ".join(span[0] for span in spans[i:i + size]).lower()
                if key in lexicon.LEXICON:
                    start = spans[i][1]
                    end = spans[i + size - 1][2]
                    merged.append(text[start:end])
                    i += size
                    matched = True
                    break
        if not matched:
            merged.append(spans[i][0])
            i += 1
    return merged


def _lemma_entry(key: str) -> Optional[dict]:
    """Find a dictionary entry from an inflected form."""
    entry = lexicon.lookup_form(key)
    if entry:
        return entry
    for candidate in morphology.lemma_candidates(key):
        entry = lexicon.lookup(candidate)
        if entry:
            return entry
    return None


def _pos_sinhala(pos: str) -> str:
    return morphology.POS_SINHALA.get(pos, morphology.POS_SINHALA["other"])


def _from_dictionary(entry: dict, surface: str, count: int) -> dict:
    lemma = entry["word"]
    pos = entry["pos"]
    grammar = entry["grammar"]
    if surface.lower() != lemma.lower():
        grammar = (
            f'{grammar} In the text it appears as "{surface}", a changed form of '
            f'the dictionary word "{lemma}".'
        )
    return {
        "word": surface,
        "lemma": lemma,
        "pronunciation": entry["pron"],
        "english": entry["en"],
        "sinhala": entry["si"],
        "part_of_speech": pos,
        "pos_sinhala": _pos_sinhala(pos),
        "grammar": grammar,
        "grammar_sinhala": morphology.POS_GRAMMAR_SINHALA.get(
            pos, morphology.POS_GRAMMAR_SINHALA["other"]
        ),
        "examples": entry["examples"],
        "in_dictionary": True,
        "meaning_source": "dictionary",
        "occurrences": count,
    }


def _from_rules(surface: str, count: int) -> dict:
    low = surface.lower()
    pos = morphology.guess_pos(low)
    grammar, grammar_si = morphology.grammar_note(low, pos, False)
    return {
        "word": surface,
        "lemma": "",
        "pronunciation": morphology.pronunciation(low),
        "english": "",
        "sinhala": "",
        "part_of_speech": pos,
        "pos_sinhala": _pos_sinhala(pos),
        "grammar": grammar,
        "grammar_sinhala": grammar_si,
        "examples": morphology.word_frames(surface),
        "in_dictionary": False,
        "meaning_source": "pending",
        "occurrences": count,
    }


def _enrich_online(entries: List[dict], limit: int) -> int:
    """Fill meanings for rule-analysed entries from the optional online lookup."""
    pending = [e for e in entries if e["meaning_source"] == "pending"]
    if not pending or limit <= 0:
        return 0
    targets = pending[:limit]
    found = 0

    def fetch(entry: dict) -> None:
        english, sinhala = online.lookup(entry["word"])
        if english:
            entry["english"] = english
            entry["sinhala"] = sinhala or ""
            entry["meaning_source"] = "online"
            if not sinhala:
                entry["sinhala"] = "සිංහල පරිවර්තනය තවම හමු නොවීය."
        else:
            entry["english"] = _NOT_FOUND_EN
            entry["sinhala"] = _NOT_FOUND_SI
            entry["meaning_source"] = "unavailable"

    if online.enabled():
        with ThreadPoolExecutor(max_workers=min(4, len(targets))) as pool:
            list(pool.map(fetch, targets))
    else:
        for entry in targets:
            entry["english"] = _NOT_FOUND_EN
            entry["sinhala"] = _NOT_FOUND_SI
            entry["meaning_source"] = "unavailable"

    for entry in targets:
        if entry["meaning_source"] == "online":
            found += 1
    return found


def analyze(text: str) -> dict:
    """Analyse every Russian word in ``text`` and return learner entries."""
    surfaces = _phrase_tokens(text)
    order: List[str] = []
    counts: Dict[str, int] = {}
    display: Dict[str, str] = {}
    for surface in surfaces:
        key = surface.lower()
        counts[key] = counts.get(key, 0) + 1
        if key not in display:
            display[key] = surface
            order.append(key)

    words: List[dict] = []
    for key in order:
        surface = display[key]
        entry = _lemma_entry(key)
        if entry:
            words.append(_from_dictionary(entry, surface, counts[key]))
        else:
            words.append(_from_rules(surface, counts[key]))

    online_found = _enrich_online(words, settings.vocab_max_online_words)

    from_dictionary = sum(1 for word in words if word["in_dictionary"])
    unknown = len(words) - from_dictionary
    return {
        "words": words,
        "source": (text or "").strip(),
        "mode": "offline",
        "stats": {
            "total": len(words),
            "dictionary": from_dictionary,
            "rule_based": unknown,
            "online_meaning": online_found,
            "online_enabled": online.enabled(),
        },
        "notice": (
            "Analysed with the built-in Russian dictionary and grammar rules."
            if unknown
            else "Every word was found in the built-in Russian dictionary."
        ),
    }
