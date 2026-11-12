"""Beginner-friendly Russian morphology for words outside the curated lexicon.

The offline engine must still say something useful about a word it has never
seen: what part of speech it looks like, the likely gender, the infinitive of a
verb form, and how to pronounce it. Everything here is a *rule of thumb* and the
wording shown to the learner says so.
"""
from __future__ import annotations

import re
from typing import List, Optional, Tuple

VOWELS = "аеёиоуыэюя"

POS_LABELS = {
    "noun": "Noun",
    "verb": "Verb",
    "adjective": "Adjective",
    "adverb": "Adverb",
    "pronoun": "Pronoun",
    "preposition": "Preposition",
    "conjunction": "Conjunction",
    "particle": "Particle",
    "numeral": "Numeral",
    "interjection": "Interjection",
    "other": "Other",
}

POS_SINHALA = {
    "noun": "නාම පදය",
    "verb": "ක්‍රියා පදය",
    "adjective": "විශේෂණ පදය",
    "adverb": "ක්‍රියා විශේෂණ පදය",
    "pronoun": "සර්වනාම",
    "preposition": "නිපාත",
    "conjunction": "සම්බන්ධක පදය",
    "particle": "කුඩා පදය",
    "numeral": "සංඛ්‍යා පදය",
    "interjection": "විස්ම පදය",
    "other": "වෙනත්",
}

# Generic Sinhala note per part of speech. Used when an entry has no specific
# Sinhala grammar note, so the learner always gets an explanation in Sinhala.
POS_GRAMMAR_SINHALA = {
    "noun": "නාම පදයක් වන්නේ පුද්ගලයින්, වස්තූන් හෝ අදහස් නම් කරන වචනයි. ලිංගය අනුව අග කොටස හා පසුවිපරම් රූප වෙනස් වේ.",
    "verb": "ක්‍රියා පදයක් වන්නේ ක්‍රියාවක් හෝ තත්ත්වයක් පෙන්වන වචනයි. කාලය හා පුද්ගලය අනුව අග කොටස වෙනස් වේ.",
    "adjective": "විශේෂණ පදයක් වන්නේ නාම පදයක ගුණය, ප්‍රමාණය හෝ වර්ණය විස්තර කරන වචනයි. එය නාම පදයේ ලිංගයට හා වචන ගණනට අනුව අග කොටස වෙනස් කරයි.",
    "adverb": "ක්‍රියා විශේෂණ පදයක් වන්නේ ක්‍රියාවක් කෙසේ, කවදා හෝ කොහේ සිදුවේද යන්න කියන වචනයි. එය වෙනස් නොවේ.",
    "pronoun": "සර්වනාමයක් වන්නේ නාම පදයක් වෙනුවට යොදන වචනයි. උදා: මම, ඔබ, ඔහු, ඇය.",
    "preposition": "නිපාතයක් වන්නේ නාම පදයකට පෙර යොදා ස්ථානය, කාලය හෝ සම්බන්ධය පෙන්වන කුඩා වචනයි. රුසියානුවේ එය නාම පදයේ විභක්තිය වෙනස් කරයි.",
    "conjunction": "සම්බන්ධක පදයක් වන්නේ වචන හෝ වාක්‍ය සම්බන්ධ කරන වචනයි. උදා: සහ, නමුත්, හෝ.",
    "particle": "කුඩා පදයක් වන්නේ වාක්‍යයක අර්ථය වෙනස් කරන කුඩා වචනයි. උදා: නැත, කරුණාකර.",
    "numeral": "සංඛ්‍යා පදයක් වන්නේ ගණනක් හෝ ප්‍රමාණයක් පෙන්වන වචනයි.",
    "interjection": "විස්ම පදයක් වන්නේ හැඟීමක් හෝ ආචාරයක් ප්‍රකාශ කරන වචනයි. උදා: ආයුබෝවන්, ස්තුතියි.",
    "other": "මෙම වචනය ඉහත කිසිදු ප්‍රධාන කාණ්ඩයකට පැහැදිලිව අයත් නොවේ.",
}

# Small closed-class word lists so function words are recognised even when a
# form is inflected or hyphenated.
PRONOUNS = {
    "я", "ты", "вы", "он", "она", "оно", "мы", "они", "это", "этот", "эта",
    "эти", "тот", "та", "те", "мой", "моя", "моё", "мои", "твой", "твоя",
    "наш", "наша", "наше", "ваш", "ваша", "свой", "своя", "кто", "что",
    "который", "которая", "которое", "которые", "себя", "никто", "ничего",
    "всё", "все", "каждый", "другой",
}
PREPOSITIONS = {
    "в", "во", "на", "с", "со", "из", "от", "к", "ко", "по", "у", "о", "об",
    "за", "под", "над", "для", "без", "через", "при", "про", "между", "до",
    "после", "около", "вокруг",
}
CONJUNCTIONS = {
    "и", "а", "но", "или", "потому", "если", "что", "чтобы", "когда", "пока",
    "хотя", "тоже", "также", "поэтому", "либо", "ни",
}
PARTICLES = {"не", "ни", "же", "ли", "бы", "ведь", "вот", "даже", "только", "пожалуйста"}
INTERJECTIONS = {
    "привет", "здравствуйте", "спасибо", "пока", "извините", "ура", "ох", "ах",
}
NUMERALS = {
    "один", "одна", "одно", "два", "две", "три", "четыре", "пять", "шесть",
    "семь", "восемь", "девять", "десять", "сто", "тысяча",
}

# Endings used to guess the part of speech of an unknown word.
_ADJ_ENDINGS = (
    "ый", "ий", "ой", "ая", "яя", "ое", "ее", "ые", "ие", "ого", "его",
    "ому", "ему", "ым", "им", "ых", "их", "ую", "юю", "ей", "ыми", "ими",
)
_VERB_ENDINGS = (
    "ться", "тся", "ешь", "ишь", "ете", "ите", "ет", "ит", "ут", "ют",
    "ат", "ят", "ал", "ил", "ыл", "ла", "ли", "ло", "ть",
)
_ADV_ENDINGS = ("ски", "ому", "ему", "о", "е")

# Suffix rewrites tried when reducing an inflected form to a dictionary form.
_LEMMA_RULES: List[Tuple[str, Tuple[str, ...]]] = [
    ("ого", ("ый", "ий", "ой")),
    ("его", ("ий", "ый")),
    ("ому", ("ый", "ий", "ой")),
    ("ему", ("ий", "ый")),
    ("ыми", ("ый", "ий")),
    ("ими", ("ий", "ый")),
    ("ых", ("ый", "ий", "ой")),
    ("их", ("ий", "ый")),
    ("ым", ("ый", "ий", "ой")),
    ("им", ("ий", "ый")),
    ("ую", ("ый", "ий", "ая")),
    ("юю", ("ий", "яя")),
    ("ая", ("ый", "ий", "ой")),
    ("яя", ("ий", "ый")),
    ("ое", ("ый", "ий", "ой")),
    ("ее", ("ий", "ый")),
    ("ые", ("ый", "ий")),
    ("ие", ("ий", "ый")),
    ("ой", ("ый", "ий", "а")),
    ("ей", ("ий", "ый", "я", "а")),
    ("ами", ("а", "я")),
    ("ями", ("я", "а")),
    ("ах", ("а", "я")),
    ("ях", ("я", "а")),
    ("ов", ("", "а")),
    ("ев", ("", "а", "я")),
    ("ам", ("а", "я", "")),
    ("ям", ("я", "а")),
    ("ом", ("", "а")),
    ("ем", ("", "ь", "а", "я")),
    ("ет", ("ть", "ать", "ить", "еть")),
    ("ит", ("ть", "ать", "ить", "еть")),
    ("ешь", ("ть", "ать", "ить")),
    ("ишь", ("ть", "ать", "ить")),
    ("ут", ("ть", "ать", "ить")),
    ("ют", ("ть", "ать", "ить")),
    ("ат", ("ть", "ать", "ить")),
    ("ят", ("ть", "ать", "ить")),
    ("ал", ("ть", "ать", "ить")),
    ("ил", ("ть", "ать", "ить")),
    ("ла", ("ть", "ать", "ить")),
    ("ли", ("ть", "ать", "ить")),
    ("у", ("", "а")),
    ("ю", ("", "а", "я")),
    ("но", ("ый", "ный")),
    ("а", ("", "о", "е")),
    ("я", ("", "ь", "е")),
    ("ы", ("", "а", "о")),
    ("и", ("", "а", "я", "ь")),
    ("е", ("", "а", "о", "ь")),
    ("о", ("", "а", "е", "ый")),
]

TRANSLIT = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "yo",
    "ж": "zh", "з": "z", "и": "i", "й": "y", "к": "k", "л": "l", "м": "m",
    "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u",
    "ф": "f", "х": "kh", "ц": "ts", "ч": "ch", "ш": "sh", "щ": "shch",
    "ъ": "", "ы": "y", "ь": "", "э": "e", "ю": "yu", "я": "ya",
}


def translit(word: str) -> str:
    """Cyrillic → a Latin reading aid a beginner can pronounce."""
    out: List[str] = []
    lowered = (word or "").lower()
    for i, ch in enumerate(lowered):
        if ch == "е" and i == 0:
            out.append("ye")
        else:
            out.append(TRANSLIT.get(ch, ch))
    return "".join(out)


def pronunciation(word: str, stress_index: Optional[int] = None) -> str:
    """Readable Latin pronunciation, hyphenated by syllable.

    ``stress_index`` is the index of the stressed vowel (0-based). Without it
    the stress is unknown, and the caller says so in the grammar note.
    """
    clean = (word or "").strip().lower()
    if not clean:
        return ""
    vowels = [index for index, ch in enumerate(clean) if ch in VOWELS]
    if not vowels:
        return translit(clean)

    bounds = [0]
    start = 0
    for position, index in enumerate(vowels):
        if position == 0:
            continue
        cursor = index - 1
        while cursor >= start and clean[cursor] not in VOWELS:
            cursor -= 1
        cluster_start = cursor + 1
        cluster_length = index - cluster_start
        if cluster_length == 0:
            boundary = index
        elif cluster_length == 1:
            boundary = index - 1
        else:
            boundary = cluster_start + 1
        bounds.append(boundary)
        start = boundary
    bounds.append(len(clean))

    syllables: List[str] = []
    for position in range(len(bounds) - 1):
        chunk = clean[bounds[position]:bounds[position + 1]]
        if not chunk:
            continue
        part = translit(chunk).replace("yy", "y")
        syllables.append(
            part.upper() if position == stress_index else part
        )
    return "-".join(syllables) if syllables else translit(clean)


def count_vowels(word: str) -> int:
    return sum(1 for ch in (word or "").lower() if ch in VOWELS)


def guess_pos(word: str) -> str:
    """Best-guess part of speech for a word outside the curated lexicon."""
    low = (word or "").strip().lower()
    if not low:
        return "other"
    if low in PRONOUNS:
        return "pronoun"
    if low in PREPOSITIONS:
        return "preposition"
    if low in CONJUNCTIONS:
        return "conjunction"
    if low in PARTICLES:
        return "particle"
    if low in INTERJECTIONS:
        return "interjection"
    if low in NUMERALS:
        return "numeral"
    if low.endswith("ться") or low.endswith("тся"):
        return "verb"
    if low.endswith(_VERB_ENDINGS):
        return "verb"
    if low.endswith(_ADJ_ENDINGS):
        return "adjective"
    if len(low) > 4 and low.endswith(_ADV_ENDINGS) and not low.endswith(("нно", "ско")):
        return "adverb"
    return "noun"


def guess_gender(word: str) -> str:
    """Masculine / feminine / neuter guess from the ending of a noun."""
    low = (word or "").strip().lower()
    if low.endswith(("ость", "есть", "а", "я", "ь")):
        return "feminine"
    if low.endswith(("о", "е", "мя")):
        return "neuter"
    return "masculine"


def guess_verb_tense(word: str) -> Tuple[str, str]:
    """Return (tense description, likely infinitive) for a verb form."""
    low = (word or "").strip().lower()
    if low.endswith(("ться", "тся")):
        return "reflexive verb form", low[:-2] + "ть" if low.endswith("тся") else low
    if low.endswith("ть"):
        return "infinitive (dictionary form)", low
    stem = low
    for ending, tense in (
            ("ешь", "2nd person singular, present"),
            ("ишь", "2nd person singular, present"),
            ("ете", "2nd person plural, present"),
            ("ите", "2nd person plural, present"),
            ("ет", "3rd person singular, present"),
            ("ит", "3rd person singular, present"),
            ("ут", "3rd person plural, present"),
            ("ют", "3rd person plural, present"),
            ("ат", "3rd person plural, present"),
            ("ят", "3rd person plural, present"),
            ("ал", "past tense, masculine"),
            ("ил", "past tense, masculine"),
            ("ыл", "past tense, masculine"),
            ("ла", "past tense, feminine"),
            ("ло", "past tense, neuter"),
            ("ли", "past tense, plural"),
    ):
        if low.endswith(ending):
            stem = low[: -len(ending)]
            infinitive = _infinitive_from_stem(stem)
            return f"{tense} form", infinitive
    return "verb form", ""


def _infinitive_from_stem(stem: str) -> str:
    """Very rough infinitive guess: чита- → читать, говори- → говорить."""
    if not stem:
        return ""
    if stem.endswith(("а", "я", "е", "и", "о", "у")):
        return stem + "ть"
    if stem.endswith("в"):
        return stem + "ать"
    return stem + "ть"


def lemma_candidates(word: str) -> List[str]:
    """Dictionary forms an inflected token might come from, best first."""
    low = (word or "").strip().lower()
    candidates: List[str] = [low]
    for ending, replacements in _LEMMA_RULES:
        if low.endswith(ending) and len(low) > len(ending):
            stem = low[: -len(ending)]
            for replacement in replacements:
                candidate = stem + replacement
                if candidate not in candidates:
                    candidates.append(candidate)
    return candidates


def gender_note(word: str) -> str:
    gender = guess_gender(word)
    reason = {
        "feminine": "it ends in -а/-я/-ь, the typical feminine endings",
        "neuter": "it ends in -о/-е, the typical neuter endings",
        "masculine": "it ends in a hard consonant, the typical masculine ending",
    }[gender]
    return f"Gender is probably {gender} because {reason}."


def grammar_note(word: str, pos: str, in_dictionary: bool) -> Tuple[str, str]:
    """(English explanation, Sinhala reminder) for an analysed word."""
    low = (word or "").lower()
    sinhala = POS_GRAMMAR_SINHALA.get(pos, POS_GRAMMAR_SINHALA["other"])
    unknown = "" if in_dictionary else (
        " This word is not in the built-in dictionary, so this is a rule-based "
        "analysis of its ending."
    )
    if pos == "noun":
        english = (
            "It looks like a noun: it names a person, thing or idea. "
            f"{gender_note(low)}{unknown}"
        )
    elif pos == "verb":
        tense, infinitive = guess_verb_tense(low)
        form = f" The infinitive is probably {infinitive}." if infinitive and infinitive != low else ""
        english = (
            "It looks like a verb: it names an action or a state, and its ending "
            f"shows the person and tense. This is a {tense}.{form}{unknown}"
        )
    elif pos == "adjective":
        english = (
            "It looks like an adjective: it describes a noun and copies the "
            "noun's gender, number and case through its ending (-ый/-ая/-ое)."
            f"{unknown}"
        )
    elif pos == "adverb":
        english = (
            "It looks like an adverb: it tells us how, when or where an action "
            f"happens, and adverbs never change their form.{unknown}"
        )
    elif pos == "pronoun":
        english = "It is a pronoun: it stands in place of a noun." + unknown
    elif pos == "preposition":
        english = (
            "It is a preposition: a short word before a noun that shows place, "
            "time or relation. In Russian it also decides the noun's case."
            + unknown
        )
    elif pos == "conjunction":
        english = "It is a conjunction: it joins words or sentences." + unknown
    elif pos == "particle":
        english = "It is a particle: a short word that changes the meaning or tone of the sentence." + unknown
    elif pos == "numeral":
        english = "It is a numeral: it shows a number or a quantity." + unknown
    elif pos == "interjection":
        english = "It is an interjection: a fixed word for a feeling or a greeting." + unknown
    else:
        english = "The part of speech could not be identified with confidence." + unknown
    return english, sinhala


def word_frames(word: str) -> List[dict]:
    """Two safe example sentences for a word we cannot decline.

    The word is quoted, so the sentences stay grammatically correct whatever
    its case, gender or tense. They are genuinely useful learner sentences.
    """
    return [
        {
            "ru": f"Что значит слово «{word}»?",
            "en": f'What does the word "{word}" mean?',
            "si": f"«{word}» යන වචනයේ තේරුම කුමක්ද?",
        },
        {
            "ru": f"Я записал новое слово «{word}» в тетрадь.",
            "en": f'I wrote the new word "{word}" in my notebook.',
            "si": f"මම «{word}» යන නව වචනය සටහන් පොතේ ලිව්වෙමි.",
        },
    ]


def is_russian_word(token: str) -> bool:
    return bool(re.search(r"[А-Яа-яЁё]", token or ""))
