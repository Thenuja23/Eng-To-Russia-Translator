import re
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional


EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
URL_RE = re.compile(r"https?://\S+|www\.[^\s]+")
DATE_RE = re.compile(r"\b(\d{4}-\d{1,2}-\d{1,2}|\d{1,2}/\d{1,2}/\d{4}|\d{1,2}\.\d{1,2}\.\d{4}|\d{1,2}\.\d{1,2}\.\d{2})\b")
NUMBER_RE = re.compile(r"\b\d+[.,]?\d*(?:\s*[%‰])?\b")
COURSE_CODE_RE = re.compile(r"\b[A-ZА-ЯЁ]{2,6}[-_]\d{2,4}\b", re.IGNORECASE)
NAME_RE = re.compile(r"\b[А-ЯЁ][а-яё]{2,}\b")


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

    def _make_key(self) -> str:
        self.counter += 1
        return f"{self.prefix}{self.counter:04d}"

    def protect(self, text: str) -> Tuple[str, Dict[str, str]]:
        protected = text
        tokens: List[ProtectedToken] = []
        for m in URL_RE.finditer(protected):
            tokens.append(ProtectedToken(self._make_key(), m.group(0), m.start(), m.end()))
        for m in EMAIL_RE.finditer(protected):
            tokens.append(ProtectedToken(self._make_key(), m.group(0), m.start(), m.end()))
        for m in DATE_RE.finditer(protected):
            tokens.append(ProtectedToken(self._make_key(), m.group(0), m.start(), m.end()))
        for m in COURSE_CODE_RE.finditer(protected):
            tokens.append(ProtectedToken(self._make_key(), m.group(0), m.start(), m.end()))
        for m in NUMBER_RE.finditer(protected):
            tokens.append(ProtectedToken(self._make_key(), m.group(0), m.start(), m.end()))
        for m in NAME_RE.finditer(protected):
            tokens.append(ProtectedToken(self._make_key(), m.group(0), m.start(), m.end()))
        tokens.sort(key=lambda t: (t.start, t.end))
        dedup = []
        for t in tokens:
            if dedup and t.start < dedup[-1].end:
                continue
            dedup.append(t)
        dedup.sort(key=lambda t: t.start, reverse=True)
        mapping: Dict[str, str] = {}
        for t in dedup:
            mapping[t.key] = t.value
            protected = protected[:t.start] + t.key + protected[t.end :]
        self.mapping = mapping
        return protected, mapping

    def restore(self, text: str, mapping: Optional[Dict[str, str]] = None) -> Tuple[str, bool]:
        use_map = mapping if mapping is not None else self.mapping
        restored = text
        all_restored = True
        # Replace in order of keys length desc to avoid partial matches? keys are fixed
        for key in sorted(use_map.keys(), key=len, reverse=True):
            if key in restored:
                restored = restored.replace(key, use_map[key])
            else:
                all_restored = False
        return restored, all_restored

    def clear(self):
        self.mapping.clear()
        self.counter = 0
