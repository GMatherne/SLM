"""Orchestrator: generate (or load) outputs for base and tuned, score every
output with the enabled scorers, write per-output records, and print the
base-vs-tuned report.

Usage
-----
Full run (needs a GPU + a trained adapter):
    python run_eval.py

Score pre-computed outputs (no GPU needed -- e.g. base/tuned answers from Colab):
    python run_eval.py --outputs outputs.jsonl

Only one arm (e.g. baseline numbers before you've trained):
    python run_eval.py --arms base

`outputs.jsonl` rows: {"scenario_id": ..., "arm": "base|tuned", "prompt": ..., "output": ...}
"""

from __future__ import annotations

import argparse
import json
import os

import config
import report as report_mod


def load_scenarios() -> list[dict]:
    rows = []
    with open(config.SCENARIOS, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            row.setdefault("scenario_id", i)
            rows.append(row)
    return rows


def build_scorers():
    scorers = []
    if config.TOGGLES.judge:
        from scorers import judge
        scorers.append(judge)
    if config.TOGGLES.pangram:
        from scorers import pangram
        scorers.append(pangram)
    if config.TOGGLES.surface:
        from scorers import surface
        scorers.append(surface)
    return scorers


def generate_outputs(scenarios: list[dict], arms: list[str]) -> list[dict]:
    """Lazily import models (heavy) only when we actually need to generate."""
    import models

    outputs = []
    makers = {"base": models.base_generator, "tuned": models.tuned_generator}
    for arm in arms:
        gen = makers[arm]().load()
        for sc in scenarios:
            outputs.append({
                "scenario_id": sc["scenario_id"],
                "arm": arm,
                "prompt": sc["prompt"],
                "output": gen.generate(sc),
            })
    return outputs


def load_outputs(path: str) -> list[dict]:
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--outputs", help="score a precomputed outputs.jsonl instead of generating")
    ap.add_argument("--arms", default="base,tuned", help="comma list: base,tuned")
    args = ap.parse_args()

    arms = [a.strip() for a in args.arms.split(",") if a.strip()]
    scenarios = load_scenarios()
    by_id = {s["scenario_id"]: s for s in scenarios}

    if args.outputs:
        outputs = load_outputs(args.outputs)
    else:
        outputs = generate_outputs(scenarios, arms)

    scorers = build_scorers()
    print(f"Scorers enabled: {[s.name for s in scorers]}")
    if config.TOGGLES.pangram:
        # Warm the Pangram cache in one batched pass: pack all outputs into
        # <=1000-word calls so we spend ~1 credit per batch instead of per
        # output. The per-output scorer loop below then hits the cache for free.
        from scorers import pangram
        texts = [o["output"] for o in outputs]
        print(f"Pangram ON -- batching {len(set(texts))} unique outputs to minimize credits...")
        pangram.score_many(texts)

    records = []
    for o in outputs:
        sc = by_id.get(o["scenario_id"], {"prompt": o.get("prompt", "")})
        rec = {"scenario_id": o["scenario_id"], "arm": o["arm"],
               "prompt": o.get("prompt", sc.get("prompt", "")), "output": o["output"]}
        for scorer in scorers:
            rec.update(scorer.score(o["output"], sc))
        records.append(rec)

    os.makedirs(config.RESULTS_DIR, exist_ok=True)
    rec_path = os.path.join(config.RESULTS_DIR, "records.jsonl")
    with open(rec_path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"Wrote {len(records)} records -> {rec_path}")

    report_mod.report(records)


if __name__ == "__main__":
    main()
