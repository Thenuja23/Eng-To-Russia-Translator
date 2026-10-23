import re
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional


EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
URL_RE = re.compile(r"https?://\S+|www\.[^\s]+")
DATE_RE = re.compile(r"\b(\d{4}-\d{1,2}-\d{1,2}|\d{1,2}/\d{1,2}/\d{4}|\d{1,2}\.\d{1,2}\.\d{4}|\d{1,2}\.\d{1,2}\.\d{2})\b")
TIME_RE = re.compile(r"\b\d{1,2}:\d{2}(?::\d{2})?\b")
# Thousands-separated numbers must be ONE token ("1,234.56", "1.234,56"),
# otherwise the model injects junk between the two placeholders and the
# value never reappears verbatim. Plain decimals ("1234.56") fall to the
# second alternative. The trailing % / ‰ suffix is optional.
_NUMBER_TAIL = r"(?:[.,]\d+)?(?:\s*[%‰])?"
NUMBER_RE = re.compile(
    rf"\b\d{{1,3}}(?:[,.]\d{{3}})+{_NUMBER_TAIL}|\b\d+{_NUMBER_TAIL}"
)
COURSE_CODE_RE = re.compile(r"\b[A-ZА-ЯЁ]{2,6}[-_]\d{2,4}\b", re.IGNORECASE)

# Capitalised Russian words are treated as candidate proper names, but only when
# they behave like names: either part of a multi-word run ("Иван Петров") or a
# mid-sentence capitalised word. Sentence-initial capitalised words ("Позвони",
# "Привет") are ordinary sentence case and must be translated normally.
NAME_WORD_RE = re.compile(r"[А-ЯЁ][а-яё]+")
NAME_RUN_RE = re.compile(r"\b[А-ЯЁ][а-яё]+(?:\s+[А-ЯЁ][а-яё]+)+\b")
NAME_STOPWORDS = {
    "привет", "здравствуйте", "пока", "спасибо", "пожалуйста", "извините",
    "это", "этот", "эта", "эти", "тот", "мой", "моя", "моё", "мои",
    "наш", "наша", "ваш", "ваша", "его", "её", "их", "как", "что", "где",
    "когда", "почему", "кто", "сегодня", "завтра", "вчера", "здесь", "там",
    "он", "она", "они", "мы", "вы", "ты", "я", "да", "нет", "все", "весь",
    "очень", "можно", "нужно", "надо", "если", "или", "но", "и", "а",
    "хорошо", "плохо",
}


def _is_sentence_initial(text: str, start: int) -> bool:
    prefix = text[:start]
    if prefix.strip() == "":
        return True
    return re.search(r"[.!?…\n]\s*$", prefix) is not None


def _name_tokens(text: str) -> List["ProtectedToken"]:
    out: List[ProtectedToken] = []
    covered: List[Tuple[int, int]] = []
    # 1) multi-word runs ("Иван Петров")
    for run in NAME_RUN_RE.finditer(text):
        for w in NAME_WORD_RE.finditer(run.group(0)):
            s = run.start() + w.start()
            e = run.start() + w.end()
            if w.group(0).lower() in NAME_STOPWORDS:
                continue
            covered.append((s, e))
            out.append(ProtectedToken("", w.group(0), s, e))
    # 2) lone mid-sentence capitalised words ("... сказал Иван")
    for m in NAME_WORD_RE.finditer(text):
        s, e = m.start(), m.end()
        if any(cs <= s < ce for cs, ce in covered):
            continue
        if m.group(0).lower() in NAME_STOPWORDS:
            continue
        if _is_sentence_initial(text, s):
            continue
        out.append(ProtectedToken("", m.group(0), s, e))
    return out


@dataclass
class ProtectedToken:
    key: str
    value: str
    start: int
    end: int


class TokenProtector:
    def __init__(self, prefix: str = "TPL_"):
        self.prefix = prefix
        self.counter = 0
        self.mapping: Dict[str, str] = {}

    def _make_key(self, avoid: str = "") -> str:
        # Never generate a placeholder that already appears literally in the
        # input, otherwise restore() would overwrite the user's own text.
        while True:
            self.counter += 1
            key = f"{self.prefix}{self.counter:04d}"
            if key not in avoid:
                return key

    def protect(self, text: str) -> Tuple[str, Dict[str, str]]:
        tokens: List[ProtectedToken] = []
        for m in URL_RE.finditer(text):
            tokens.append(ProtectedToken(self._make_key(text), m.group(0), m.start(), m.end()))
        for m in EMAIL_RE.finditer(text):
            tokens.append(ProtectedToken(self._make_key(text), m.group(0), m.start(), m.end()))
        for m in DATE_RE.finditer(text):
            tokens.append(ProtectedToken(self._make_key(text), m.group(0), m.start(), m.end()))
        for m in TIME_RE.finditer(text):
            tokens.append(ProtectedToken(self._make_key(text), m.group(0), m.start(), m.end()))
        for m in COURSE_CODE_RE.finditer(text):
            tokens.append(ProtectedToken(self._make_key(text), m.group(0), m.start(), m.end()))
        for m in NUMBER_RE.finditer(text):
            tokens.append(ProtectedToken(self._make_key(text), m.group(0), m.start(), m.end()))
        for t in _name_tokens(text):
            tokens.append(ProtectedToken(self._make_key(text), t.value, t.start, t.end))

        # Longest match wins at the same start position, so "15.10.2026" is kept
        # as one date token instead of being split into "15.10" + "2026".
        tokens.sort(key=lambda t: (t.start, -t.end))
        dedup: List[ProtectedToken] = []
        for t in tokens:
            if dedup and t.start < dedup[-1].end:
                continue
            dedup.append(t)

        protected = text
        mapping: Dict[str, str] = {}
        for t in sorted(dedup, key=lambda t: t.start, reverse=True):
            mapping[t.key] = t.value
            protected = protected[:t.start] + t.key + protected[t.end:]
        self.mapping = mapping
        return protected, mapping

    def _tolerant_pattern(self, key: str) -> "re.Pattern":
        suffix = key[len(self.prefix):]
        if suffix.isdigit():
            # models sometimes rewrite EXP_0003 as EXP_003 or EXP_3
            return re.compile(re.escape(self.prefix) + r"0*" + str(int(suffix)) + r"(?!\d)")
        return re.compile(re.escape(key))

    def key_present(self, text: str, key: str) -> bool:
        return self._tolerant_pattern(key).search(text) is not None

    def restore(self, text: str, mapping: Optional[Dict[str, str]] = None) -> Tuple[str, bool]:
        use_map = mapping if mapping is not None else self.mapping
        restored = text
        all_restored = True
        for key, value in use_map.items():
            m = self._tolerant_pattern(key).search(restored)
            if m:
                restored = restored[:m.start()] + value + restored[m.end():]
            else:
                all_restored = False
        return restored, all_restored

    def clear(self):
        self.mapping.clear()
        self.counter = 0
