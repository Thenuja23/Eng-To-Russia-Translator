"""Prompts for the AI ensemble.

The rules mirror the product's hard requirements: keep protected tokens
verbatim, never drop sentences, and answer in the reader's language (English).
"""
from __future__ import annotations

LANG_NAMES = {"en": "English", "ru": "Russian"}


def _names(src: str, tgt: str) -> tuple[str, str]:
    return (
        LANG_NAMES.get((src or "").lower(), src or "the source language"),
        LANG_NAMES.get((tgt or "").lower(), tgt or "the target language"),
    )


def translate_system(src: str, tgt: str) -> str:
    s, t = _names(src, tgt)
    return (
        f"You are a professional {s}->{t} translator inside a language-learning app "
        "used by foreign students in Russia.\n"
        "Rules:\n"
        "1. Translate the user's text faithfully into the target language.\n"
        "2. Placeholder tokens such as AIT0001 are protected data. Copy every "
        "placeholder EXACTLY, in the same order, never translate or split them.\n"
        "3. Keep every sentence: do not merge, drop or add sentences.\n"
        "4. Preserve names, tone and register. Use natural, idiomatic language.\n"
        "5. Return ONLY the translation - no quotes, labels, notes or explanations."
    )


def translate_user(protected_text: str, src: str, tgt: str) -> str:
    s, t = _names(src, tgt)
    return (
        f"Translate from {s} to {t}.\n"
        "Text to translate (do not repeat the instructions):\n"
        f"{protected_text}"
    )


def enhance_system(src: str, tgt: str) -> str:
    s, t = _names(src, tgt)
    return (
        f"You are a bilingual {s}/{t} editor reviewing a machine translation.\n"
        "Rules:\n"
        "1. Improve grammar, word order and naturalness of the translation.\n"
        "2. Keep the meaning of the source exactly; never add new information.\n"
        "3. Placeholder tokens such as AIT0001 are protected data. Copy every "
        "placeholder EXACTLY, in the same order, never translate or split them.\n"
        "4. Keep every sentence of the source; never drop content.\n"
        "5. Return ONLY the improved translation - no notes, labels or alternatives."
    )


def enhance_user(protected_source: str, protected_translation: str) -> str:
    return (
        "Source text:\n"
        f"{protected_source}\n\n"
        "Current translation:\n"
        f"{protected_translation}\n\n"
        "Return the improved translation only."
    )


def explain_system(src: str, tgt: str) -> str:
    s, t = _names(src, tgt)
    return (
        "You are a patient Russian-language tutor for an English-speaking beginner.\n"
        "Explain in clear English, briefly and practically. Prefer short sections "
        "with plain-text headings (Meaning, Grammar, Reading the cursive, Watch out).\n"
        "Mention stress or transliteration only when it helps pronunciation.\n"
        "Never invent facts; if something is ambiguous, say so.\n"
        "Keep the answer under 220 words."
    )


def explain_user(text: str, translation: str, src: str, tgt: str, question: str = "") -> str:
    s, t = _names(src, tgt)
    parts = [
        f"Direction: {s} -> {t}.",
        f"Source text:\n{text}",
    ]
    if translation:
        parts.append(f"Existing translation:\n{translation}")
    if question:
        parts.append(f"The learner asks:\n{question}")
    else:
        parts.append(
            "Explain what the text means, the key grammar, and how to read it."
        )
    return "\n\n".join(parts)


# --------------------------------------------------------------------------- #
# Vocabulary analysis (word-by-word, English + Sinhala)
# --------------------------------------------------------------------------- #

POS_SINHALA = {
    "verb": "ක්‍රියා පදය",
    "noun": "නාම පදය",
    "adjective": "විශේෂණ පදය",
    "adverb": "ක්‍රියා විශේෂණ පදය",
    "pronoun": "සර්වනාම",
    "preposition": "නිපාත",
    "numeral": "සංඛ්‍යා පදය",
    "conjunction": "සම්බන්ධක",
    "particle": "කුඩා පදය",
    "interjection": "විස්ම පදය",
    "other": "වෙනත්",
}


def vocab_system() -> str:
    return (
        "You are a Russian language tutor for Sinhala-speaking beginners who also "
        "read English. You analyse Russian text word by word.\n"
        "Rules:\n"
        "1. Include EVERY word of the input, in order, skipping none. "
        "Repeat a word if it appears more than once with different usage, "
        "otherwise analyse repeated words once at their first occurrence.\n"
        "2. If a word has several meanings, explain the meanings that fit the "
        "context. If its part of speech can change with context, say so in "
        "\"grammar\".\n"
        "3. Always explain grammar in simple English a beginner can follow. "
        "For nouns include gender (masculine/feminine/neuter) when possible. "
        "For verbs include the infinitive form and tense when identifiable.\n"
        "4. Sinhala fields must be written in Sinhala script (not transliterated).\n"
        "5. Example sentences must be natural, correct Russian, useful for daily "
        "life. Provide exactly two per word, each with English and Sinhala "
        "translations.\n"
        "6. Respond with ONLY a JSON object - no markdown fences, no commentary:\n"
        '{"words": [{"word": "красивый", "pronunciation": "kra-SEE-vy", '
        '"english": "beautiful", "sinhala": "ලස්සන / සුන්දර", '
        '"part_of_speech": "adjective", "pos_sinhala": "විශේෂණ පදය", '
        '"grammar": "This is an adjective because it describes the quality of a noun.", '
        '"examples": [{"ru": "Это красивый дом.", "en": "This is a beautiful house.", '
        '"si": "මෙය ලස්සන නිවසකි."}, '
        '{"ru": "У неё красивое платье.", "en": "She has a beautiful dress.", '
        '"si": "ඇයට ලස්සන ඇඳුමක් තිබේ."}]}]}\n'
        "part_of_speech must be one of: verb, noun, adjective, adverb, pronoun, "
        "preposition, numeral, conjunction, particle, interjection, other.\n"
        "pronunciation must be a simple Latin transliteration a beginner can read "
        "(hyphenated syllables, uppercase for the stressed syllable)."
    )


def vocab_user(text: str) -> str:
    return (
        "Analyse every Russian word in the text below and return ONLY the JSON "
        "object described in the instructions.\n\n"
        f"Text:\n{text}"
    )
