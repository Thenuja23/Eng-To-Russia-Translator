"""Placeholder-safe translation.

Neural MT models sometimes drop or rewrite out-of-vocabulary placeholder tokens
(e.g. ``OPU_0003`` -> ``OPU_003``). That would silently delete emails, dates,
numbers or names from the user's text, which the locked spec forbids.

Strategy:
1. Translate the whole protected string (best fluency / context).
2. If every placeholder survived (tolerating zero-padding rewrites), keep it.
3. Otherwise retranslate segment-by-segment around the placeholders, which
   guarantees every placeholder is copied through unchanged, preserving the
   surrounding whitespace.

The chosen strategy is reported back so the caller can flag reduced fluency.
"""
import re
from typing import Callable, List, Optional, Tuple


def placeholder_pattern(prefix: str) -> "re.Pattern":
    return re.compile(rf"({re.escape(prefix)}\d{{4}})")


def tolerant_pattern(prefix: str, key: str) -> "re.Pattern":
    suffix = key[len(prefix):]
    if suffix.isdigit():
        return re.compile(re.escape(prefix) + r"0*" + str(int(suffix)) + r"(?!\d)")
    return re.compile(re.escape(key))


def key_present(text: str, prefix: str, key: str) -> bool:
    return tolerant_pattern(prefix, key).search(text) is not None


def translate_preserving_placeholders(
    translate_fn: Callable[[str], str],
    protected: str,
    keys: List[str],
    prefix: str = "TPL_",
    is_present: Optional[Callable[[str, str], bool]] = None,
) -> Tuple[str, str]:
    """Translate ``protected`` while guaranteeing every key in ``keys`` survives.

    Returns ``(text, strategy)`` where strategy is ``"whole"`` or ``"segmented"``.
    """
    pat = placeholder_pattern(prefix)
    present = is_present or (lambda t, k: key_present(t, prefix, k))

    whole = translate_fn(protected)
    if all(present(whole, k) for k in keys):
        return whole, "whole"

    def _run_keep_ws(part: str) -> str:
        lead = part[: len(part) - len(part.lstrip())]
        trail = part[len(part.rstrip()):]
        core = part.strip()
        if core == "":
            return part
        return lead + translate_fn(core) + trail

    # Fall back to segment-by-segment translation around the placeholders.
    parts = re.split(pat, protected)
    out = []
    for part in parts:
        if part == "" or pat.fullmatch(part) or part.strip() == "":
            out.append(part)
        else:
            out.append(_run_keep_ws(part))
    return "".join(out), "segmented"
