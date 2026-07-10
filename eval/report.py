"""Turn per-output records into the base-vs-tuned table the brief asks for:
mean score per metric for each arm, plus the delta. Also dumps the worst tuned
outputs for the error-analysis paragraph.

No pandas dependency required -- pure stdlib so it runs anywhere. If you want the
prettier grid, pandas is used opportunistically when installed.
"""

from __future__ import annotations

import json
import os
from collections import defaultdict

import config

# metrics where HIGHER is better (judge scores); everything else lower is better
HIGHER_BETTER = {"j_reads_human", "j_task_quality", "p_reads_human"}
# the verdict: what actually decides if the tune worked
KEY_METRICS = [
    "j_reads_human", "j_task_quality",
    "p_fraction_ai", "p_reads_human",
]
# descriptive only -- shown separately, never the verdict
SURFACE_METRICS = [
    "s_em_dash_per_1k", "s_markdown_tokens", "s_ai_words", "s_transition_per_250",
]


def _num(v):
    if isinstance(v, bool):
        return 1.0 if v else 0.0
    return float(v) if isinstance(v, (int, float)) else None


def _means(records: list[dict]) -> dict:
    by_arm_metric = defaultdict(list)
    for r in records:
        for k, v in r.items():
            n = _num(v)
            if n is not None and k not in ("scenario_id",):
                by_arm_metric[(r["arm"], k)].append(n)
    means = {}
    for (arm, metric), vals in by_arm_metric.items():
        means[(arm, metric)] = sum(vals) / len(vals)
    return means


def _print_table(title, metric_list, means, arms, arrows=True):
    metrics = [m for m in metric_list if any((a, m) in means for a in arms)]
    if not metrics:
        return
    print("\n" + "=" * 64)
    print(title)
    print("=" * 64)
    header = f"{'metric':<26}" + "".join(f"{a:>12}" for a in arms)
    if arrows and "base" in arms and "tuned" in arms:
        header += f"{'delta':>12}"
    print(header)
    print("-" * len(header))
    for m in metrics:
        row = f"{m:<26}"
        vals = {}
        for a in arms:
            v = means.get((a, m))
            vals[a] = v
            row += f"{v:>12.3f}" if v is not None else f"{'-':>12}"
        if arrows and "base" in arms and "tuned" in arms and vals.get("base") is not None and vals.get("tuned") is not None:
            delta = vals["tuned"] - vals["base"]
            if m in HIGHER_BETTER:
                arrow = " +" if delta > 0 else " -" if delta < 0 else "  "
            else:
                arrow = " +" if delta < 0 else " -" if delta > 0 else "  "  # lower better
            row += f"{delta:>10.3f}{arrow}"
        print(row)


def report(records: list[dict]):
    means = _means(records)
    arms = sorted({r["arm"] for r in records})

    _print_table("VERDICT  --  base vs tuned (mean)", KEY_METRICS, means, arms)

    # win condition callout: tuned should read more human than base
    if "base" in arms and "tuned" in arms:
        print("-" * 62)
        b = means.get(("base", "j_reads_human"))
        t = means.get(("tuned", "j_reads_human"))
        if b is not None and t is not None:
            print(f"Reads-human (judge): base {b:.2f} -> tuned {t:.2f}  "
                  f"[{'WIN' if t > b else 'not yet'}]")
        pb = means.get(("base", "p_fraction_ai"))
        pt = means.get(("tuned", "p_fraction_ai"))
        if pb is not None and pt is not None:
            print(f"Pangram fraction_ai: base {pb:.2f} -> tuned {pt:.2f}  "
                  f"[{'WIN' if pt < pb else 'not yet'}]")

    # surface stats: descriptive context, explicitly NOT the verdict
    _print_table("surface stats (informational, not the verdict)",
                 SURFACE_METRICS, means, arms)

    _error_analysis(records)


def _error_analysis(records: list[dict], n: int = 5):
    """Dump the worst tuned outputs to seed the error-analysis paragraph."""
    tuned = [r for r in records if r["arm"] == "tuned"]
    if not tuned:
        return

    def badness(r):
        # worst = reads least human, then lowest task quality
        return (
            -(_num(r.get("j_reads_human")) or 0),
            -(_num(r.get("j_task_quality")) or 0),
        )

    worst = sorted(tuned, key=badness)[:n]
    print("\n" + "=" * 64)
    print(f"ERROR ANALYSIS -- {len(worst)} weakest tuned outputs")
    print("=" * 64)
    for r in worst:
        print(f"\n[scenario {r['scenario_id']}] reads_human={r.get('j_reads_human')} "
              f"quality={r.get('j_task_quality')} fraction_ai={r.get('p_fraction_ai','-')}")
        print(f"  prompt : {r.get('prompt','')[:100]}")
        print(f"  output : {r.get('output','')[:200]}")
        if r.get("j_rationale"):
            print(f"  judge  : {r['j_rationale']}")
