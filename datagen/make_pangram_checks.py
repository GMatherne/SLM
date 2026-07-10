"""Build a paste-ready file for manually checking the human corpus on the Pangram
website, ONE response per submission (clean per-example verdicts, no window
blending). Stratified across sources so you can see if any source reads more AI
than others.

Usage:
    python make_pangram_checks.py                 # 2 per source
    python make_pangram_checks.py --per-source 3
"""

from __future__ import annotations

import argparse
import json
import os
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "data", "human_dataset_full.jsonl")
OUT = os.path.join(HERE, "data", "pangram_checks.md")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-source", type=int, default=2)
    args = ap.parse_args()

    rows = [json.loads(l) for l in open(SRC, encoding="utf-8")]
    by = defaultdict(list)
    for r in rows:
        by[r["source"]].append(r)

    # take an even spread within each source (not just the first few)
    picked = []
    for src, items in by.items():
        step = max(1, len(items) // args.per_source)
        picked.extend(items[::step][:args.per_source])

    lines = ["# Pangram checks -- paste each block on its own (one submission each)",
             "",
             "Paste ONLY the text inside each block into the Pangram site, one at a time,",
             "and record the verdict + AI% in the table at the bottom. Doing them",
             "individually gives a clean per-example score (no window blending).", ""]
    for i, r in enumerate(picked):
        lines.append(f"## #{i}  [{r['source']}]")
        lines.append("```")
        lines.append(r["response"])
        lines.append("```")
        lines.append("")

    lines += ["---", "", "## Results", "", "| # | source | verdict (human/mixed/AI) | AI % |",
              "|---|--------|--------------------------|------|"]
    for i, r in enumerate(picked):
        lines.append(f"| {i} | {r['source']} | | |")

    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"wrote {len(picked)} checks ({args.per_source}/source) -> {OUT}")
    print("sources:", {s: min(args.per_source, len(v)) for s, v in by.items()})


if __name__ == "__main__":
    main()
