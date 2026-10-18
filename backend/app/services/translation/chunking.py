"""Chunking for translation.

Two problems motivate splitting text before translation:

1. MarianMT/Opus-MT has a fixed window (512 tokens) and silently truncates
   longer input, deleting the rest of the user's text.
2. More importantly, Opus-MT is *unreliable on multi-sentence input*: for some
   inputs it emits a translation of only one of the sentences, quietly dropping
   the others (e.g. "Is the library open? Thank you." -> "Библиотека открыта?").
   This is a property of the model, not of the pipeline.

We therefore split input into sentence-bounded units that comfortably fit,
translate each unit, and reassemble. Concatenating every produced value in
order reproduces the input exactly, so no whitespace or content is lost.
"""
import re
from typing import List, Tuple

# Kept well below the model's 512-token window (English ~4 chars/token).
DEFAULT_MAX_CHARS = 800

# Split right after sentence-final punctuation, keeping the following run of
# whitespace as the separator. re.split with a capture group returns
# [even..., sep, even..., sep, ...]: parts at odd indices are separators.
_SENTENCE_SPLIT = re.compile(r"(?<=[.!?…])(\s+)")

Unit = Tuple[str, str]  # ("text" | "sep", value)


def _split_long(text: str, max_chars: int) -> List[Unit]:
    """Wrap a single over-long sentence, preserving every character.

    A whitespace run is appended to the chunk it follows, so concatenating the
    returned values reproduces ``text`` exactly.
    """
    units: List[Unit] = []
    cur = ""
    for token in re.split(r"(\s+)", text):
        if token == "":
            continue
        if not token.isspace() and len(cur) + len(token) > max_chars and cur.strip():
            units.append(("text", cur))
            cur = ""
        cur += token
    if cur:
        units.append(("text", cur))
    return units


def chunk_text(text: str, max_chars: int = DEFAULT_MAX_CHARS) -> List[Unit]:
    """Split ``text`` into ordered ``(kind, value)`` units.

    ``kind`` is ``"text"`` for translatable content and ``"sep"`` for literal
    whitespace. Concatenating every value in order reproduces the input exactly.
    """
    units: List[Unit] = []
    lines = text.split("\n")
    for i, line in enumerate(lines):
        if i > 0:
            units.append(("sep", "\n"))
        if line == "":
            continue
        parts = _SENTENCE_SPLIT.split(line)
        for j, part in enumerate(parts):
            if part == "":
                continue
            if j % 2 == 1:  # whitespace between two sentences
                units.append(("sep", part))
            elif len(part) <= max_chars:
                units.append(("text", part))
            else:
                units.extend(_split_long(part, max_chars))
    return units


def reassemble(units: List[Unit]) -> str:
    """Inverse of :func:`chunk_text` for ``(kind, value)`` pairs."""
    return "".join(value for _, value in units)
