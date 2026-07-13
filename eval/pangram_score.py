"""One-command Pangram scoring of base-vs-tuned outputs -- so you don't have to
paste into the website by hand.

Reads a base/tuned output pair (default: round 3 in colab_outputs/), scores every
answer through the Pangram scorer (batched to minimise credits, cached so re-runs
are free), and writes a results table. All of Pangram's hard spend caps apply
(persistent credit ledger, per-run breaker, dry-run freeze -- see scorers/pangram.py).

Blocked until the account has API credits: the endpoint returns 402
"Insufficient credits" until you top up the API pool (separate from the web
dashboard's monthly credits). Run `--estimate` first to see the credit cost.

Usage (run from the eval/ dir):
  python pangram_score.py --estimate      # how many credits, spends nothing
  python pangram_score.py                  # score round-3 base+tuned
  python pangram_score.py --tuned-only     # score only the tuned arm (cheaper)
  python pangram_score.py --base X --tuned Y --out report
"""

from __future__ import annotations

import argparse
import json
import os

import config
from scorers import pangram

OUTDIR = os.path.join(config.HERE, "colab_outputs")


def _load(path: str) -> list:
    return json.load(open(path, encoding="utf-8"))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default=os.path.join(OUTDIR, "base_outputs_round3.json"))
    ap.add_argument("--tuned", default=os.path.join(OUTDIR, "tuned_outputs_round3.json"))
    ap.add_argument("--out", default=os.path.join(OUTDIR, "pangram_auto_round3"))
    ap.add_argument("--tuned-only", action="store_true", help="skip the base arm")
    ap.add_argument("--estimate", action="store_true", help="print credit estimate, spend nothing")
    args = ap.parse_args()

    tuned = _load(args.tuned)
    base = None if args.tuned_only else _load(args.base)
    prompts = [t["prompt"] for t in tuned]
    tuned_txt = [t["output"] for t in tuned]
    base_txt = [b["output"] for b in base] if base else []

    all_txt = tuned_txt + base_txt
    print(pangram.status())
    print(f"[estimate] {pangram.estimate_credits(all_txt)} new credit(s) to score "
          f"{len(all_txt)} text(s) (cached ones are free).")
    if args.estimate:
        return

    try:
        tuned_s = pangram.score_many(tuned_txt)
        base_s = pangram.score_many(base_txt) if base else [None] * len(tuned_txt)
    except pangram.BudgetError as e:
        raise SystemExit(f"stopped by spend cap: {e}")
    except Exception as e:
        raise SystemExit(f"Pangram call failed ({type(e).__name__}): {str(e)[:200]}\n"
                         f"If this is 402 'Insufficient credits', top up the API credit pool.")

    def pct(s):
        fa = s and s.get("p_fraction_ai")
        return "—" if fa is None else f"{round(fa * 100)}% AI"

    rows, flipped = [], 0
    L = ["# Pangram auto-scored (base vs tuned)", "",
         "| # | prompt | base | tuned | reads human? |", "|---|--------|------|-------|--------------|"]
    for i, (p, ts) in enumerate(zip(prompts, tuned_s)):
        bs = base_s[i]
        human = bool(ts and ts.get("p_reads_human"))
        flipped += int(human)
        L.append(f"| {i} | {p[:38]} | {pct(bs)} | {pct(ts)} | {'✅' if human else '❌'} |")
        rows.append({"i": i, "prompt": p, "base": bs, "tuned": ts})
        print(f"#{i} base={pct(bs)} tuned={pct(ts)} human={human} — {p[:40]}")

    L += ["", f"**tuned reads human: {flipped}/{len(prompts)}**  |  threshold "
          f"fraction_ai < {config.PANGRAM['ai_threshold']}", ""]
    json.dump(rows, open(args.out + ".json", "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    open(args.out + ".md", "w", encoding="utf-8").write("\n".join(L) + "\n")
    print(f"\ntuned reads human: {flipped}/{len(prompts)}\n{pangram.status()}\nwrote {args.out}.json / .md")


if __name__ == "__main__":
    main()
