"""Accuracy + information-loss eval for base-vs-tuned answers.

For each held-out prompt we have a BASE answer (thorough, but reads AI) and a
TUNED answer (reads human). Fine-tuning for human voice can COST correctness, so
this eval asks a judge, per tuned answer, two things:

  - accuracy (0-5): is the TUNED answer factually correct? + list its errors.
  - info_retention (0-100): what % of the ESSENTIAL correct points does the TUNED
    answer keep, using BASE as a guide to what's essential?
    (information_loss = 100 - info_retention)

BASE is the reference for RETENTION only (same model, fuller answer). ACCURACY is
graded in absolute terms, NOT against BASE -- the base answers have their own
errors (e.g. both arms call the onion irritant "sulfuric acid").

Judge provider follows config.JUDGE_MODEL ("claude-*" -> Anthropic, else OpenAI),
with the same per-run call breaker as scorers/judge.py. Results cache to disk so
re-runs are free.

Usage:
  python accuracy_eval.py                    # scores the round-3 pair in colab_outputs/
  python accuracy_eval.py --base B.json --tuned T.json --out mydir/report
  python accuracy_eval.py --manual           # no API: emit paste-ready judge prompts
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

import config

HERE = config.HERE
OUTDIR = os.path.join(HERE, "colab_outputs")

_PROMPT = """\
You are a careful subject-matter grader for short educational explanations.

You are given a QUESTION, a REFERENCE answer (thorough but possibly imperfect),
and a CANDIDATE answer. Grade ONLY the CANDIDATE.

QUESTION:
{prompt}

REFERENCE (use only to judge what counts as an essential point; it may contain
its own errors, so do NOT treat it as ground truth for correctness):
\"\"\"
{base}
\"\"\"

CANDIDATE (grade this):
\"\"\"
{tuned}
\"\"\"

Grade the CANDIDATE:
1. accuracy (0-5), factual correctness in ABSOLUTE terms:
     5 = fully correct
     4 = correct with only minor imprecision
     3 = core is right but one clear error
     2 = multiple errors OR a wrong core mechanism
     1 = largely wrong
     0 = nonsense or fabricated
2. errors: list each specific factual error in the CANDIDATE (empty list if none).
3. fabrications: the subset of those errors that are CONFIDENTLY-STATED invented
   specifics -- fake names, numbers, or mechanisms asserted as fact (the scariest
   kind for a tutor; e.g. inventing a nonexistent enzyme). Empty list if none.
4. info_retention (0-100): of the ESSENTIAL correct points needed to actually
   answer the question (use the REFERENCE as a guide to what's essential, ignoring
   its padding), what percent does the CANDIDATE include?
5. dropped_points: essential points present in the REFERENCE but missing from the
   CANDIDATE (empty list if none).
6. rationale: one sentence.

Respond with ONLY a JSON object, no prose:
{{"accuracy": <0-5>, "errors": [<str>...], "fabrications": [<str>...], "info_retention": <0-100>, "dropped_points": [<str>...], "rationale": "<one sentence>"}}
"""


def _parse_json(raw: str) -> dict:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.strip("`").split("\n", 1)[-1]
    start, end = raw.find("{"), raw.rfind("}")
    return json.loads(raw[start : end + 1])


def _cache_path(key: str) -> str:
    os.makedirs(config.CACHE_DIR, exist_ok=True)
    h = hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]
    return os.path.join(config.CACHE_DIR, f"accuracy_{h}.json")


_calls = 0
_calls_lock = threading.Lock()   # breaker is shared across judge threads


def _call_llm(prompt: str) -> dict:
    global _calls
    with _calls_lock:   # thread-safe so parallel judges can't blow past the cap
        if _calls + 1 > config.LLM_MAX_CALLS_PER_RUN:
            raise RuntimeError(f"per-run cap reached ({config.LLM_MAX_CALLS_PER_RUN}); raise LLM_MAX_CALLS_PER_RUN if intended.")
        _calls += 1
    model = config.JUDGE_MODEL
    if model.startswith("claude") and not config.JUDGE_BASE_URL:   # direct Anthropic
        from anthropic import Anthropic

        client = Anthropic(timeout=120)
        msg = client.messages.create(model=model, max_tokens=config.JUDGE_MAX_TOKENS,
                                     messages=[{"role": "user", "content": prompt}])
        return _parse_json(msg.content[0].text)
    from openai import OpenAI

    # timeout so a stalled gateway call fails in 2 min instead of the ~10 min SDK default
    client = OpenAI(base_url=config.JUDGE_BASE_URL, timeout=120)   # gateway (TrueFoundry) or default OpenAI
    r = client.chat.completions.create(model=model, response_format={"type": "json_object"},
                                       messages=[{"role": "user", "content": prompt}])
    return _parse_json(r.choices[0].message.content)


def _judge(prompt: str, base: str, tuned: str) -> dict:
    text = _PROMPT.format(prompt=prompt, base=base, tuned=tuned)
    key = config.JUDGE_MODEL + "||acc||" + text
    cp = _cache_path(key)
    if os.path.exists(cp):
        return json.load(open(cp, encoding="utf-8"))
    result = _call_llm(text)
    json.dump(result, open(cp, "w", encoding="utf-8"))
    return result


def _load(path: str) -> list:
    return json.load(open(path, encoding="utf-8"))


def write_manual_template(pairs: list, out: str) -> None:
    """No-API fallback: emit each judge prompt in a fenced block + a blank table
    so the answers can be graded by hand (or pasted into any chat model)."""
    L = ["# Accuracy + information-loss — MANUAL scoring template", "",
         "No LLM API configured. Paste each block into any capable model (or grade",
         "yourself), then fill the table. accuracy 0-5; info_retention 0-100 "
         "(info_loss = 100 - retention).", ""]
    for i, (p, b, t) in enumerate(pairs):
        L += [f"## #{i} — {p}", "```", _PROMPT.format(prompt=p, base=b, tuned=t).strip(), "```", ""]
    L += ["---", "", "## Results", "",
          "| # | prompt | accuracy /5 | fabrications | info_retention % | errors |",
          "|---|--------|-------------|--------------|------------------|--------|"]
    for i, (p, _, _) in enumerate(pairs):
        L.append(f"| {i} | {p[:40]} | | | | |")
    open(out + "_TEMPLATE.md", "w", encoding="utf-8").write("\n".join(L) + "\n")
    print(f"wrote {out}_TEMPLATE.md  (manual scoring; no credits spent)")


def run(pairs: list, out: str, workers: int = 8) -> None:
    def work(i, p, b, t):
        r = _judge(p, b, t)
        r["i"], r["prompt"] = i, p
        return r

    rows = []
    with ThreadPoolExecutor(max_workers=max(1, workers)) as ex:   # parallel judges
        for fut in as_completed([ex.submit(work, i, p, b, t) for i, (p, b, t) in enumerate(pairs)]):
            r = fut.result()
            rows.append(r)
            print(f"#{r['i']} acc={r.get('accuracy')}/5 retention={r.get('info_retention')}% "
                  f"errors={len(r.get('errors', []))} — {r['prompt'][:40]}", flush=True)
    rows.sort(key=lambda r: r["i"])

    n = len(rows)
    acc = [r.get("accuracy", 0) or 0 for r in rows]
    ret = [r.get("info_retention", 0) or 0 for r in rows]
    with_err = sum(1 for r in rows if r.get("errors"))
    fabs = sum(len(r.get("fabrications", [])) for r in rows)
    with_fab = sum(1 for r in rows if r.get("fabrications"))
    agg = {"n": n, "mean_accuracy": round(sum(acc) / n, 2),
           "mean_info_retention": round(sum(ret) / n, 1),
           "mean_info_loss": round(100 - sum(ret) / n, 1),
           "answers_with_errors": with_err,
           "fabrications_total": fabs, "answers_with_fabrication": with_fab}

    json.dump({"aggregate": agg, "rows": rows}, open(out + ".json", "w", encoding="utf-8"),
              indent=2, ensure_ascii=False)

    L = ["# Accuracy + information-loss report", "",
         f"Judge: `{config.JUDGE_MODEL}`  |  {n} answers", "",
         f"- **mean accuracy: {agg['mean_accuracy']}/5**",
         f"- **mean info retention: {agg['mean_info_retention']}%**  "
         f"(info loss {agg['mean_info_loss']}%)",
         f"- **answers with >=1 factual error: {with_err}/{n}**",
         f"- **confident fabrications: {fabs} across {with_fab}/{n} answers**", "",
         "| # | prompt | acc /5 | retain % | fab | errors |",
         "|---|--------|--------|----------|-----|--------|"]
    for r in rows:
        L.append(f"| {r['i']} | {r['prompt'][:38]} | {r.get('accuracy')} | "
                 f"{r.get('info_retention')} | {len(r.get('fabrications', []))} | "
                 f"{'; '.join(r.get('errors', [])) or '—'} |")
    open(out + ".md", "w", encoding="utf-8").write("\n".join(L) + "\n")
    print(f"\n{agg}\nwrote {out}.json / {out}.md")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default=os.path.join(OUTDIR, "base_outputs_round5.json"))
    ap.add_argument("--tuned", default=os.path.join(OUTDIR, "tuned_outputs_round5.json"))
    ap.add_argument("--out", default=os.path.join(OUTDIR, "round5_accuracy"))
    ap.add_argument("--manual", action="store_true", help="emit paste-ready prompts, no API")
    ap.add_argument("--workers", type=int, default=8, help="parallel judge requests")
    args = ap.parse_args()

    base, tuned = _load(args.base), _load(args.tuned)
    print(f"scoring: {os.path.basename(args.tuned)} vs {os.path.basename(args.base)} "
          f"({len(tuned)} answers) -> {os.path.basename(args.out)}.md  | judge {config.JUDGE_MODEL}", flush=True)
    if len(base) != len(tuned):
        raise SystemExit(f"length mismatch: base={len(base)} tuned={len(tuned)}")
    pairs = [(b["prompt"], b["output"], t["output"]) for b, t in zip(base, tuned)]

    if args.manual:
        write_manual_template(pairs, args.out)
        return
    try:                                    # fall back to manual if the API is down/blocked
        run(pairs, args.out, args.workers)
    except Exception as e:
        print(f"live judge unavailable ({type(e).__name__}: {str(e)[:120]});\n"
              f"writing manual template instead.")
        write_manual_template(pairs, args.out)


if __name__ == "__main__":
    main()
