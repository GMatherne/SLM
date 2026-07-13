"""Blind human-preference eval -- the ground truth Pangram and the LLM judge only
approximate. We optimize "reads human to Pangram"; this checks whether a *person*
actually reads the answers as human, on a level playing field with the base model.

Why: a single detector can be gamed/overfit. A blind human rating is the honest
cross-check on the whole premise. Base and tuned answers are anonymized and shuffled
so the rater can't tell which model wrote which.

  python human_eval.py --make            # build a blind rating sheet + secret key
  # ... a human edits human_eval_sheet.md, writing H (human) or A (AI) per answer ...
  python human_eval.py --score           # read the marks + key -> human-rate per arm

Defaults to the round-4 base/tuned outputs. Deterministic shuffle (seeded), so the
key always matches the sheet.
"""

from __future__ import annotations

import argparse
import json
import os
import random

HERE = os.path.dirname(os.path.abspath(__file__))
OUTDIR = os.path.join(HERE, "colab_outputs")
SHEET = os.path.join(OUTDIR, "human_eval_sheet.md")
KEY = os.path.join(OUTDIR, "human_eval_key.json")
SEED = 20260711


def _load(p):
    return json.load(open(p, encoding="utf-8"))


def make(base_path, tuned_path):
    base, tuned = _load(base_path), _load(tuned_path)
    items = []
    for i, (b, t) in enumerate(zip(base, tuned)):
        items.append({"arm": "base", "i": i, "prompt": b["prompt"], "answer": b["output"]})
        items.append({"arm": "tuned", "i": i, "prompt": t["prompt"], "answer": t["output"]})
    random.Random(SEED).shuffle(items)
    key = {}
    L = ["# Blind human eval -- mark each answer H (reads human) or A (reads AI)", "",
         "For each block, write `H` or `A` on the VERDICT line. Don't overthink it -- "
         "gut read of 'did a person write this?'. You do NOT know which model wrote which.", ""]
    for n, it in enumerate(items, 1):
        rid = f"R{n:02d}"
        key[rid] = {"arm": it["arm"], "i": it["i"]}
        L += [f"## {rid}", f"*Prompt:* {it['prompt']}", "", it["answer"], "",
              f"VERDICT {rid}: ", "", "---", ""]
    os.makedirs(OUTDIR, exist_ok=True)
    open(SHEET, "w", encoding="utf-8").write("\n".join(L) + "\n")
    json.dump(key, open(KEY, "w", encoding="utf-8"), indent=2)
    print(f"wrote {SHEET} ({len(items)} answers) + {KEY} (secret).\n"
          f"Edit the sheet: put H or A after each 'VERDICT Rxx:' line, then --score.")


def score():
    if not (os.path.exists(SHEET) and os.path.exists(KEY)):
        raise SystemExit("run --make first, then fill the sheet.")
    key = _load(KEY)
    marks = {}
    for line in open(SHEET, encoding="utf-8"):
        line = line.strip()
        if line.startswith("VERDICT "):
            rid, _, v = line[len("VERDICT "):].partition(":")
            v = v.strip().upper()[:1]
            if v in ("H", "A"):
                marks[rid.strip()] = v
    per = {"base": [0, 0], "tuned": [0, 0]}   # [human, total]
    for rid, v in marks.items():
        arm = key.get(rid, {}).get("arm")
        if arm in per:
            per[arm][1] += 1
            per[arm][0] += 1 if v == "H" else 0
    total_marked = sum(v[1] for v in per.values())
    unmarked = len(key) - total_marked
    L = ["# Blind human-eval result", ""]
    for arm in ("base", "tuned"):
        h, n = per[arm]
        rate = f"{100*h/n:.0f}%" if n else "n/a"
        L.append(f"- **{arm}: {h}/{n} rated human ({rate})**")
    L += ["", f"(marked {total_marked}/{len(key)}; {unmarked} blank)", "",
          "Compare the tuned human-rate to Pangram's; if a *person* reads them human "
          "at a similar rate, the result isn't just Pangram-overfit."]
    out = os.path.join(OUTDIR, "human_eval_result.md")
    open(out, "w", encoding="utf-8").write("\n".join(L) + "\n")
    print("\n".join(L) + f"\n\nwrote {out}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default=os.path.join(OUTDIR, "base_outputs_round5.json"))
    ap.add_argument("--tuned", default=os.path.join(OUTDIR, "tuned_outputs_round5.json"))
    ap.add_argument("--make", action="store_true")
    ap.add_argument("--score", action="store_true")
    args = ap.parse_args()
    if args.make:
        make(args.base, args.tuned)
    elif args.score:
        score()
    else:
        raise SystemExit("use --make (build sheet) or --score (after filling it in).")


if __name__ == "__main__":
    main()
