"""Surface metrics -- descriptive only.

These count the visible, observable stuff (em dash rate, markdown tokens, a few
commonly-cited AI words, transition density). They are NOT a gate and NOT the
verdict: the judge and Pangram decide whether an output is good. Surface numbers
just ride along on each record so you can look at trends, correlate them with
Pangram, and mention them in the writeup.

No thresholds, no pass/fail, no "violation" flags. Just numbers.
"""

from __future__ import annotations

import re

name = "surface"

# A short, illustrative set -- not authoritative, not a scrub list. Just a rough
# gauge of the words people most often point to. Presence != bad (context wins).
AI_WORDS = [
    "delve", "tapestry", "intricate", "multifaceted", "crucial", "meticulous",
    "realm", "leverage", "robust", "underscore", "testament",
]
TRANSITIONS = ["moreover", "furthermore", "additionally", "consequently", "hence"]
MD_PATTERNS = [
    r"\*\*[^*]+\*\*", r"^#{1,6}\s", r"^\s*[-*+]\s+\S", r"^\s*\d+\.\s+\S",
    r"`[^`]+`", r"^\s*>\s+\S",
]


def _count(patterns, text):
    return sum(len(re.findall(p, text, re.MULTILINE | re.IGNORECASE)) for p in patterns)


def score(text: str, scenario: dict) -> dict:
    words = max(1, len(re.findall(r"\b\w+\b", text)))
    em = text.count("—")
    ai_words = sum(len(re.findall(rf"\b{re.escape(w)}\b", text, re.I)) for w in AI_WORDS)
    transitions = sum(len(re.findall(rf"\b{re.escape(w)}\b", text, re.I)) for w in TRANSITIONS)
    return {
        "s_words": words,
        "s_em_dashes": em,
        "s_em_dash_per_1k": round(em / words * 1000, 2),
        "s_markdown_tokens": _count(MD_PATTERNS, text),
        "s_ai_words": ai_words,
        "s_transition_per_250": round(transitions / words * 250, 2),
    }
