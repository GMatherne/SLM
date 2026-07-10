"""Build the SFT dataset: for each training task, generate the reply, score
it with the SAME scorers the model eval uses, keep only the ones that pass the
bar, and write them in ShareGPT format. Rejected outputs and a failure-mode
histogram are written too -- that histogram is how you know what to fix in the
prompt next.

The dataset (this is your real deliverable) is filtered by the exact criteria the
tuned model will later be graded on, so a high-scoring dataset and a high-scoring
model measure the same thing.

Usage:
    export OPENAI_API_KEY=...        # or ANTHROPIC_API_KEY if TEACHER/JUDGE are claude-*
    python build_dataset.py --n 100        # generate+filter 100 questions
    python build_dataset.py --dry 5        # generate 5, print them, no write
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter

import generate

# reuse the eval harness scorers so dataset filter == model eval criteria
EVAL_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "eval")
sys.path.insert(0, EVAL_DIR)
import config as eval_config  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
QUESTIONS = os.path.join(HERE, "questions.jsonl")
OUT_DIR = os.path.join(HERE, "data")


def load_questions() -> list[dict]:
    rows = []
    with open(QUESTIONS, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            line = line.strip()
            if line:
                r = json.loads(line)
                r.setdefault("scenario_id", i)
                rows.append(r)
    return rows


def free_gate(text: str, scenario: dict, use_judge: bool):
    """Free scorers only: the judge (verdict) + surface stats (informational).
    Returns (reasons, metrics). Runs before any Pangram credit is spent."""
    reasons, metrics = [], {}
    if use_judge:
        from scorers import judge as J
        j = J.score(text, scenario)
        metrics.update(j)
        if (j.get("j_reads_human") or 0) < 2:
            reasons.append(f"reads_human={j.get('j_reads_human')}")
        if (j.get("j_task_quality") or 0) < 2:
            reasons.append(f"task_quality={j.get('j_task_quality')}")
    if eval_config.TOGGLES.surface:
        from scorers import surface as S
        metrics.update(S.score(text, scenario))
    return reasons, metrics


def pangram_gate(text: str, scenario: dict):
    """Pangram check. If score_many warmed the cache this is a free cache hit.
    Returns (reasons, metrics)."""
    from scorers import pangram as P
    p = P.score(text, scenario)
    reasons = [] if p.get("p_reads_human") else [f"fraction_ai={p.get('p_fraction_ai')}"]
    return reasons, p


def to_sharegpt(question: str, response: str) -> dict:
    return {"conversations": [
        {"from": "human", "value": question},
        {"from": "gpt", "value": response},
    ]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=0, help="max questions to process (0 = all)")
    ap.add_argument("--dry", type=int, default=0, help="generate N, print, don't write/score")
    ap.add_argument("--no-judge", action="store_true", help="skip the LLM judge (keep everything unless Pangram is on)")
    args = ap.parse_args()

    version = generate.prompt_version()
    questions = load_questions()
    if args.n:
        questions = questions[: args.n]

    if args.dry:
        for q in questions[: args.dry]:
            print(f"\n=== {q['prompt']}\n{generate.generate(q['prompt'])}")
        return

    use_judge = not args.no_judge
    use_pangram = eval_config.TOGGLES.pangram

    os.makedirs(OUT_DIR, exist_ok=True)
    fail_hist = Counter()

    # Phase 1: generate + free scoring (judge + surface). No Pangram credits yet.
    items = []
    for q in questions:
        text = generate.generate(q["prompt"])
        reasons, metrics = free_gate(text, q, use_judge)
        items.append({"q": q, "text": text, "reasons": reasons,
                      "metrics": metrics, "judge_passed": not reasons})
        print(f"[judge {'ok ' if not reasons else 'rej'}] {q['prompt'][:46]:<46} {reasons}")

    # Phase 2: batch-warm Pangram for judge-survivors ONLY (cheap-first), packing
    # them into <=1000-word calls (batched). One credit per call, cached per reply.
    if use_pangram:
        survivors = [it["text"] for it in items if it["judge_passed"]]
        if survivors:
            from scorers import pangram
            print(f"\nPangram: batch-scoring {len(set(survivors))} unique survivor "
                  f"replies (cheap-first + batched)...")
            pangram.score_many(survivors)

    # Phase 3: finalize -- Pangram calls here are cache hits from phase 2.
    accepted, rejected = [], []
    for it in items:
        reasons, metrics = list(it["reasons"]), it["metrics"]
        if use_pangram and it["judge_passed"]:
            p_reasons, p_metrics = pangram_gate(it["text"], it["q"])
            metrics.update(p_metrics)
            reasons += p_reasons
        ok = not reasons
        row = {"prompt_version": version, "scenario_id": it["q"]["scenario_id"],
               "question": it["q"]["prompt"], "response": it["text"],
               "reasons": reasons, **{k: metrics[k] for k in metrics if k.startswith(("j_", "p_", "s_"))}}
        (accepted if ok else rejected).append(row)
        if not ok:
            for r in reasons:
                fail_hist[r.split("=")[0].split(":")[0]] += 1

    # write ShareGPT dataset + provenance sidecar
    ds_path = os.path.join(OUT_DIR, "dataset.jsonl")
    with open(ds_path, "w", encoding="utf-8") as f:
        for r in accepted:
            f.write(json.dumps(to_sharegpt(r["question"], r["response"]), ensure_ascii=False) + "\n")
    with open(os.path.join(OUT_DIR, "accepted_full.jsonl"), "w", encoding="utf-8") as f:
        for r in accepted:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    with open(os.path.join(OUT_DIR, "rejected.jsonl"), "w", encoding="utf-8") as f:
        for r in rejected:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    n = len(questions)
    print("\n" + "=" * 60)
    print(f"prompt {version}: accepted {len(accepted)}/{n} "
          f"({len(accepted)/n*100:.0f}%)  -> {ds_path}")
    print("Failure modes (fix the top one in persona.md/task.md, regenerate):")
    for reason, count in fail_hist.most_common():
        print(f"  {count:>3}  {reason}")


if __name__ == "__main__":
    main()
