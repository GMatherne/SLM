"""Judge spot-audit of the TRAINING corpus (not the model's outputs).

Samples a few answers per source and has the judge rate each answer's factual
soundness, then aggregates BY SOURCE. Purpose: validate the training data is
accurate and catch any systematically weak source *before* training -- cheaply
(~2 per source), without the cost or the style-bias of curating the whole corpus.

This is a factual-accuracy GATE, not a quality RANKING: we look for sources that
are systematically wrong, not for the "most complete" answers (ranking that way
would bias toward the AI-reading register). We drop a source only if it's bad;
we do NOT reshape the corpus toward the judge's taste.

Judge provider/gateway comes from config (TrueFoundry etc.). Same disk cache +
per-run call breaker as accuracy_eval.

Usage (run from eval/, with the gateway key set):
  python audit_corpus.py --estimate          # how many calls, spend nothing
  python audit_corpus.py                      # ~2 per source
  python audit_corpus.py --per-source 3
"""

from __future__ import annotations

import argparse
import json
import os
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed

import config
from accuracy_eval import _call_llm, _cache_path

CORPUS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "datagen", "data",
                      "human_dataset_full.jsonl")
OUT = os.path.join(config.HERE, "colab_outputs", "corpus_audit")

# deterministic sampler (no Math.random needed; keeps re-runs cache-stable)
def _pick(items, k, seed):
    if len(items) <= k:
        return items
    idx, out = seed % len(items), []
    for _ in range(k):
        out.append(items[idx])
        idx = (idx + max(1, len(items) // k)) % len(items)
    return out


_PROMPT = """\
You are auditing one answer from a tutor's TRAINING corpus for factual soundness.

QUESTION:
{prompt}

ANSWER:
{resp}

Rate the ANSWER's factual accuracy/soundness 0-5 (5 = fully correct/sound; 3 = mostly
right but one clear error; 0 = nonsense or badly wrong). For essay-feedback or
argumentative answers, judge whether the reasoning/advice is sound. List specific
errors (empty if none).

Respond with ONLY JSON: {{"accuracy": <0-5>, "errors": [<str>...]}}
"""


def _judge(prompt, resp):
    text = _PROMPT.format(prompt=prompt, resp=resp)
    cp = _cache_path(config.JUDGE_MODEL + "||audit||" + text)
    if os.path.exists(cp):
        return json.load(open(cp, encoding="utf-8"))
    r = _call_llm(text)
    json.dump(r, open(cp, "w", encoding="utf-8"))
    return r


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-source", type=int, default=2)
    ap.add_argument("--workers", type=int, default=8, help="parallel judge requests")
    ap.add_argument("--sources", default="", help="comma-separated source filter (e.g. deep re-audit); default all")
    ap.add_argument("--estimate", action="store_true")
    args = ap.parse_args()

    only = {s.strip() for s in args.sources.split(",") if s.strip()}
    out = OUT + "_deep" if only else OUT   # don't clobber the full audit

    rows = [json.loads(l) for l in open(CORPUS, encoding="utf-8")]
    by_src = defaultdict(list)
    for r in rows:
        by_src[r["source"]].append(r)
    sample = []
    for src, items in sorted(by_src.items()):
        if only and src not in only:
            continue
        for r in _pick(items, args.per_source, seed=len(src)):
            sample.append(r)

    print(f"{len(by_src)} sources, corpus {len(rows)} rows -> auditing {len(sample)} samples "
          f"(~{len(sample)} judge calls, {args.workers} in parallel). Judge: {config.JUDGE_MODEL}")
    if args.estimate:
        return

    def work(r):
        v = _judge(r["prompt"], r["response"])
        return {**r, "accuracy": v.get("accuracy"), "errors": v.get("errors", [])}

    graded, done = [], 0
    # I/O-bound gateway calls -> a thread pool runs `workers` judges concurrently.
    # Cached calls return instantly; the per-run breaker (accuracy_eval) is locked.
    try:
        with ThreadPoolExecutor(max_workers=max(1, args.workers)) as ex:
            for fut in as_completed([ex.submit(work, r) for r in sample]):
                g = fut.result()
                graded.append(g)
                done += 1
                print(f"  [{done}/{len(sample)}] {g['source']}: acc={g.get('accuracy')}", flush=True)
    except Exception as e:
        raise SystemExit(f"judge unavailable ({type(e).__name__}: {str(e)[:160]}). "
                         f"Check the gateway env vars, then re-run.")

    agg = defaultdict(lambda: {"n": 0, "sum": 0, "errs": 0})
    for g in graded:
        a = agg[g["source"]]
        a["n"] += 1
        a["sum"] += g.get("accuracy") or 0
        a["errs"] += 1 if g.get("errors") else 0
    overall = sum(g.get("accuracy") or 0 for g in graded) / max(1, len(graded))

    lines = [f"# Corpus factual-audit ({config.JUDGE_MODEL})", "",
             f"- **overall mean accuracy: {overall:.2f}/5** over {len(graded)} samples", "",
             "| source | n | mean acc | with errors | flag |",
             "|--------|---|----------|-------------|------|"]
    weak = []
    for src in sorted(agg, key=lambda s: agg[s]["sum"] / max(1, agg[s]["n"])):
        a = agg[src]
        mean = a["sum"] / max(1, a["n"])
        flag = "⚠ WEAK" if mean < 3 else ""
        if mean < 3:
            weak.append(src)
        lines.append(f"| {src} | {a['n']} | {mean:.1f} | {a['errs']}/{a['n']} | {flag} |")
    lines += ["", f"**sources to review (mean < 3): {weak or 'none'}**"]
    json.dump({"overall": round(overall, 2), "rows": graded}, open(out + ".json", "w", encoding="utf-8"),
              indent=2, ensure_ascii=False)
    open(out + ".md", "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print(f"overall {overall:.2f}/5 | weak sources: {weak or 'none'}\nwrote {out}.md / .json")


if __name__ == "__main__":
    main()
