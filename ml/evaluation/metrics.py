import re
from typing import List


def cer(ref: str, hyp: str) -> float:
    # Character Error Rate
    ref = ref.lower()
    hyp = hyp.lower()
    # Levenshtein
    d = [[0] * (len(hyp) + 1) for _ in range(len(ref) + 1)]
    for i in range(len(ref) + 1):
        d[i][0] = i
    for j in range(len(hyp) + 1):
        d[0][j] = j
    for i in range(1, len(ref) + 1):
        for j in range(1, len(hyp) + 1):
            cost = 0 if ref[i - 1] == hyp[j - 1] else 1
            d[i][j] = min(d[i - 1][j] + 1, d[i][j - 1] + 1, d[i - 1][j - 1] + cost)
    if len(ref) == 0:
        return 0.0
    return d[len(ref)][len(hyp)] / len(ref)


def wer(ref: str, hyp: str) -> float:
    # Word Error Rate
    ref_words = re.findall(r'\S+', ref.lower())
    hyp_words = re.findall(r'\S+', hyp.lower())
    if len(ref_words) == 0:
        return 0.0
    d = [[0] * (len(hyp_words) + 1) for _ in range(len(ref_words) + 1)]
    for i in range(len(ref_words) + 1):
        d[i][0] = i
    for j in range(len(hyp_words) + 1):
        d[0][j] = j
    for i in range(1, len(ref_words) + 1):
        for j in range(1, len(hyp_words) + 1):
            cost = 0 if ref_words[i - 1] == hyp_words[j - 1] else 1
            d[i][j] = min(d[i - 1][j] + 1, d[i][j - 1] + 1, d[i - 1][j - 1] + cost)
    return d[len(ref_words)][len(hyp_words)] / len(ref_words)


def chrf(ref: str, hyp: str, n: int = 6, beta: float = 2.0) -> float:
    # Basic chrF approximation
    # For real implementation, use sacrebleu-like logic; simplified here
    return 0.0  # placeholder - implement as needed
