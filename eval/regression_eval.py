"""Regression eval: did fine-tuning for human-sounding education answers BREAK
the model's general ability?

We generate base+tuned answers on off-domain / format-constrained prompts (see
regression_prompts.jsonl; colab_train.py writes base_regression.json and
tuned_regression.json when that file is uploaded). This script grades, per task,
how well EACH arm does it, and flags where the TUNED arm is worse -- the failure
mode of narrow fine-tuning: over-explaining, botching a requested format, or
bleeding the chatty "tutor" voice into a coding / bare-value / formal task.

A regression = tuned_follows < base_follows on the same task.

Judge/caching/caps are shared with accuracy_eval.py. Same manual fallback when no
API is available.

Usage (run from eval/):
  python regression_eval.py                 # base_regression.json vs tuned_regression.json
  python regression_eval.py --manual        # emit paste-ready prompts, no API
"""

from __future__ import annotations

import argparse
import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

import config
from accuracy_eval import _call_llm, _cache_path

OUTDIR = os.path.join(config.HERE, "colab_outputs")

_PROMPT = """\
You are checking whether fine-tuning DEGRADED a model's general ability. For one
TASK you are given the PASS CRITERION, the BASE model's answer, and the TUNED
model's answer. Grade how well EACH answer does the task.

TASK:
{prompt}

PASS CRITERION:
{check}

BASE answer:
\"\"\"
{base}
\"\"\"

TUNED answer:
\"\"\"
{tuned}
\"\"\"

Grade each answer on:
- follows (0-2): 0 = fails the task or ignores the required format/constraint;
  1 = partially does it; 2 = fully does the task AND honors the format/constraint.

Also judge the TUNED answer for register bleed:
- register_bleed (true/false): true if the TUNED answer inappropriately falls into
  a chatty, first-person "explainer/tutor" voice where the task called for something
  else (code, a bare value, a table, a formal email, a one-word answer).

Respond with ONLY a JSON object, no prose:
{{"base_follows": <0-2>, "tuned_follows": <0-2>, "register_bleed": <true|false>, "rationale": "<one sentence>"}}
"""


def _judge(prompt: str, check: str, base: str, tuned: str) -> dict:
    text = _PROMPT.format(prompt=prompt, check=check, base=base, tuned=tuned)
    cp = _cache_path(config.JUDGE_MODEL + "||reg||" + text)
    if os.path.exists(cp):
        return json.load(open(cp, encoding="utf-8"))
    result = _call_llm(text)
    json.dump(result, open(cp, "w", encoding="utf-8"))
    return result


def _load(path: str) -> list:
    return json.load(open(path, encoding="utf-8"))


def _rows(prompts_meta, base, tuned):
    return [(m["prompt"], m.get("check", ""), b["output"], t["output"])
            for m, b, t in zip(prompts_meta, base, tuned)]


def write_manual_template(meta, rows, out):
    L = ["# Regression (general-ability) — MANUAL scoring template", "",
         "No LLM API configured. Paste each block into any capable model (or grade",
         "yourself). follows = 0-2 for each arm; regression = tuned < base.", ""]
    for i, ((p, c, b, t), m) in enumerate(zip(rows, meta)):
        L += [f"## #{i} [{m.get('category','')}] {p}", "```",
              _PROMPT.format(prompt=p, check=c, base=b, tuned=t).strip(), "```", ""]
    L += ["---", "", "## Results", "",
          "| # | category | base /2 | tuned /2 | register bleed? | regression? |",
          "|---|----------|---------|----------|-----------------|-------------|"]
    for i, m in enumerate(meta):
        L.append(f"| {i} | {m.get('category','')} | | | | |")
    open(out + "_TEMPLATE.md", "w", encoding="utf-8").write("\n".join(L) + "\n")
    print(f"wrote {out}_TEMPLATE.md  (manual scoring; no credits spent)")


def run(meta, rows, out, workers=8):
    def work(i, p, c, b, t):
        r = _judge(p, c, b, t)
        r["i"], r["prompt"], r["category"] = i, p, meta[i].get("category", "")
        r["regression"] = (r.get("tuned_follows", 0) or 0) < (r.get("base_follows", 0) or 0)
        return r

    res = []
    with ThreadPoolExecutor(max_workers=max(1, workers)) as ex:   # parallel judges
        for fut in as_completed([ex.submit(work, i, p, c, b, t) for i, (p, c, b, t) in enumerate(rows)]):
            r = fut.result()
            res.append(r)
            print(f"#{r['i']} [{r['category']}] base={r.get('base_follows')} tuned={r.get('tuned_follows')} "
                  f"bleed={r.get('register_bleed')} regress={r['regression']}", flush=True)
    res.sort(key=lambda r: r["i"])

    n = len(res)
    bf = sum(r.get("base_follows", 0) or 0 for r in res)
    tf = sum(r.get("tuned_follows", 0) or 0 for r in res)
    regr = sum(1 for r in res if r["regression"])
    bleed = sum(1 for r in res if r.get("register_bleed"))
    agg = {"n": n, "mean_base_follows": round(bf / n, 2), "mean_tuned_follows": round(tf / n, 2),
           "regressions": regr, "register_bleed": bleed}

    json.dump({"aggregate": agg, "rows": res}, open(out + ".json", "w", encoding="utf-8"),
              indent=2, ensure_ascii=False)
    L = ["# Regression (general-ability) report", "",
         f"Judge: `{config.JUDGE_MODEL}`  |  {n} tasks", "",
         f"- **mean follows — base {agg['mean_base_follows']}/2  vs  tuned {agg['mean_tuned_follows']}/2**",
         f"- **regressions (tuned worse than base): {regr}/{n}**",
         f"- **register bleed (chatty voice where inappropriate): {bleed}/{n}**", "",
         "| # | category | base /2 | tuned /2 | bleed | regression | note |",
         "|---|----------|---------|----------|-------|------------|------|"]
    for r in res:
        L.append(f"| {r['i']} | {r['category']} | {r.get('base_follows')} | {r.get('tuned_follows')} | "
                 f"{'Y' if r.get('register_bleed') else '—'} | {'Y' if r['regression'] else '—'} | "
                 f"{r.get('rationale','')} |")
    open(out + ".md", "w", encoding="utf-8").write("\n".join(L) + "\n")
    print(f"\n{agg}\nwrote {out}.json / {out}.md")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prompts", default=os.path.join(config.HERE, "regression_prompts.jsonl"))
    ap.add_argument("--base", default=os.path.join(OUTDIR, "base_regression_round5.json"))
    ap.add_argument("--tuned", default=os.path.join(OUTDIR, "tuned_regression_round5.json"))
    ap.add_argument("--out", default=os.path.join(OUTDIR, "round5_regression"))
    ap.add_argument("--manual", action="store_true")
    ap.add_argument("--workers", type=int, default=8, help="parallel judge requests")
    args = ap.parse_args()

    if not (os.path.exists(args.base) and os.path.exists(args.tuned)):
        raise SystemExit("Need base_regression.json + tuned_regression.json. Upload "
                         "regression_prompts.jsonl to Colab and re-run colab_train.py to produce them.")
    meta = [json.loads(l) for l in open(args.prompts, encoding="utf-8")]
    base, tuned = _load(args.base), _load(args.tuned)
    print(f"regression: {os.path.basename(args.tuned)} vs {os.path.basename(args.base)} "
          f"({len(tuned)} tasks) -> {os.path.basename(args.out)}.md | judge {config.JUDGE_MODEL}", flush=True)
    rows = _rows(meta, base, tuned)

    if args.manual:
        write_manual_template(meta, rows, args.out)
        return
    try:
        run(meta, rows, args.out, args.workers)
    except Exception as e:
        print(f"live judge unavailable ({type(e).__name__}: {str(e)[:120]}); writing manual template.")
        write_manual_template(meta, rows, args.out)


if __name__ == "__main__":
    main()
