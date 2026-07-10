"""Data-quality report for a human dataset (the _full sidecar with source/prompt/
response, or a ShareGPT jsonl). Measures the stuff we CAN check automatically:
length distribution, cleanliness/format problems, dedup, and appropriateness
flags. It does NOT judge "reads human" (that's Pangram) or "good content" (that's
a judge/eyeball) -- it catches the mechanical junk before those steps.

Usage:
    python quality_report.py data/human_dataset_full.jsonl
    python quality_report.py data/human_dataset.jsonl        # ShareGPT too
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter

IMG_REF = re.compile(r"\b(see|as shown|refer to)\s+(the\s+)?(image|images|figure|fig|diagram|picture|photo|attachment|above|below|following)\b", re.I)
URL = re.compile(r"https?://|www\.")
SLURS = ["fuck", "shit", "nigg", "faggot", "retard", "cunt", "bitch"]  # crude appropriateness flag


def load(path):
    rows = []
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        d = json.loads(line)
        if "conversations" in d:  # ShareGPT
            turns = {t["from"]: t["value"] for t in d["conversations"]}
            rows.append({"source": d.get("source", "?"),
                         "prompt": turns.get("human", ""),
                         "response": turns.get("gpt") or turns.get("assistant", "")})
        else:  # sidecar
            rows.append({"source": d.get("source", "?"),
                         "prompt": d.get("prompt", ""), "response": d.get("response", "")})
    return rows


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "data/human_dataset_full.jsonl"
    rows = load(path)
    n = len(rows)
    print(f"{path}: {n} examples\n")

    print("by source:", dict(Counter(r["source"] for r in rows)))

    lens = [len(r["response"].split()) for r in rows]
    lens.sort()
    def pct(p): return lens[min(len(lens) - 1, int(p * len(lens)))]
    print(f"\nresponse words: min {lens[0]}, p10 {pct(.1)}, median {pct(.5)}, "
          f"p90 {pct(.9)}, max {lens[-1]}")

    # flags
    flags = Counter()
    flagged_examples = {}
    seen = set()
    for r in rows:
        resp = r["response"]
        w = len(resp.split())
        issues = []
        if w < 25: issues.append("too_short")
        if w > 320: issues.append("too_long")
        if URL.search(resp): issues.append("has_url")
        if IMG_REF.search(resp): issues.append("image_ref")           # references missing visual
        if sum(c.isascii() for c in resp) / max(1, len(resp)) < 0.97: issues.append("non_ascii")
        if sum(c.isupper() for c in resp) / max(1, sum(c.isalpha() for c in resp)) > 0.3: issues.append("shouty")
        if any(s in resp.lower() for s in SLURS): issues.append("possible_toxic")
        key = resp[:60].lower()
        if key in seen: issues.append("dup")
        seen.add(key)
        for i in issues:
            flags[i] += 1
            flagged_examples.setdefault(i, r)

    print("\nflags (count / 400):")
    if not flags:
        print("  none")
    for f, c in flags.most_common():
        print(f"  {c:4}  {f}")

    # show one example per flag type
    if flagged_examples:
        print("\n--- one example per flag ---")
        for f, r in flagged_examples.items():
            print(f"[{f}] ({r['source']}) {r['response'][:140]}")

    # random-ish sample for eyeballing (every Nth)
    print("\n--- sample for manual review ---")
    step = max(1, n // 4)
    for r in rows[::step][:4]:
        print(f"[{r['source']}] Q: {r['prompt'][:70]}")
        print(f"           A: {r['response'][:160]}\n")


if __name__ == "__main__":
    main()
