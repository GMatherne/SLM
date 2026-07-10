"""Pangram scorer -- the objective "reads human" signal, via Pangram's v3 async
task API (docs.pangram.com/api-reference/ai-detection).

Single-text flow: POST /task -> poll GET /task/{id} until STAGE_SUCCESS -> read
fraction_ai.

Batched flow (score_many): Pangram bills per call (<=1000 words = 1 credit), so
we pack several replies into one document, send one call, then recover a
per-reply fraction_ai from the response's `windows` array (each window carries a
label + character offsets). Each reply is cached individually under its own text,
so single-mode and batched-mode share one cache and neither re-spends a credit.

OFF by default (config.TOGGLES.pangram = False) until your account is live. To
enable: `export PANGRAM_API_KEY=...`, then set config.TOGGLES.pangram = True.

Caveat worth knowing: a batched per-reply score is *reconstructed* from windows,
so it can differ slightly from the number a lone single-text call would give
(sliding windows near the joins, cross-text context). Use batched mode for the
high-volume dataset-filtering step; prefer single-text calls for the final
headline eval where fidelity matters more than credits.
"""

from __future__ import annotations

import json
import os
import time

import config
from . import cache

name = "pangram"

_SEP = "\n\n"


# --------------------------------------------------------------------------- #
# Hard spend caps -- enforced BEFORE any network call, so nothing can exceed
# them even if code loops. Three independent guards: a persistent lifetime
# credit budget, a per-process call breaker, and a dry-run freeze switch.
# --------------------------------------------------------------------------- #
class BudgetError(RuntimeError):
    """Raised instead of calling Pangram when a spend cap would be exceeded."""


_run_calls = 0  # per-process counter (resets each run)


def _ledger_path() -> str:
    os.makedirs(config.CACHE_DIR, exist_ok=True)
    return os.path.join(config.CACHE_DIR, "pangram_credits.json")


def credits_spent() -> int:
    """Total credits this code has ever spent (persistent across runs)."""
    p = _ledger_path()
    if os.path.exists(p):
        try:
            return int(json.load(open(p, encoding="utf-8")).get("spent", 0))
        except Exception:
            return 0
    return 0


def credits_remaining() -> int:
    return max(0, config.PANGRAM["credit_budget"] - credits_spent())


def _record_spend(n: int = 1) -> int:
    total = credits_spent() + n
    with open(_ledger_path(), "w", encoding="utf-8") as f:
        json.dump({"spent": total}, f)
    return total


def _guard_before_call():
    """Refuse (raise) rather than spend if any cap would be exceeded."""
    global _run_calls
    if config.PANGRAM["dry_run"]:
        raise BudgetError("PANGRAM_DRY_RUN is set -- refusing to spend a real credit.")
    spent, budget = credits_spent(), config.PANGRAM["credit_budget"]
    if spent + 1 > budget:
        raise BudgetError(
            f"Pangram credit budget reached ({spent}/{budget}). "
            f"Raise PANGRAM_CREDIT_BUDGET to continue."
        )
    per_run = config.PANGRAM["max_calls_per_run"]
    if _run_calls + 1 > per_run:
        raise BudgetError(
            f"Pangram per-run cap reached ({per_run} calls this run). "
            f"Circuit breaker; raise PANGRAM_MAX_CALLS_PER_RUN if intended."
        )


def status() -> str:
    return (f"Pangram credits: spent {credits_spent()}/{config.PANGRAM['credit_budget']}, "
            f"remaining {credits_remaining()} (per-run cap {config.PANGRAM['max_calls_per_run']}, "
            f"dry_run={config.PANGRAM['dry_run']})")


def estimate_credits(texts: list) -> int:
    """How many NEW calls score_many(texts) would make (uncached, packed).
    Costs nothing -- read-only."""
    todo, seen = [], set()
    for t in texts:
        if t not in seen:
            seen.add(t)
            if cache.load("pangram", t) is None:
                todo.append(t)
    return len(_pack(todo, config.PANGRAM["batch_max_words"]))


# --------------------------------------------------------------------------- #
# API
# --------------------------------------------------------------------------- #
def _detect(text: str) -> dict:
    """Run one document through the async task API; return the success payload.
    A spend cap is enforced BEFORE the network call, so this cannot exceed the
    configured budget/per-run limits."""
    import requests

    _guard_before_call()  # raises rather than spend if a cap would be exceeded

    api_key = os.getenv(config.PANGRAM["api_key_env"])
    if not api_key:
        raise RuntimeError(f"{config.PANGRAM['api_key_env']} not set; cannot call Pangram.")
    headers = {config.PANGRAM["auth_header"]: api_key, "Content-Type": "application/json"}
    base = config.PANGRAM["base_url"].rstrip("/")

    resp = requests.post(
        f"{base}/task",
        headers=headers,
        json={"text": text, "public_dashboard_link": False},
        timeout=60,
    )
    resp.raise_for_status()
    task_id = resp.json()["task_id"]

    # A task was created -> a credit is consumed. Record it now (even if polling
    # later fails) so the ledger never undercounts real spend.
    global _run_calls
    _run_calls += 1
    _record_spend(1)

    deadline = time.monotonic() + config.PANGRAM["poll_timeout_s"]
    while time.monotonic() < deadline:
        r = requests.get(f"{base}/task/{task_id}", headers=headers, timeout=60)
        r.raise_for_status()
        data = r.json()
        stage = data.get("stage")
        if stage == "STAGE_SUCCESS":
            return data
        if stage == "STAGE_FAILED":
            raise RuntimeError(f"Pangram task {task_id} failed: {data}")
        time.sleep(config.PANGRAM["poll_interval_s"])
    raise TimeoutError(
        f"Pangram task {task_id} unfinished after {config.PANGRAM['poll_timeout_s']}s"
    )


# --------------------------------------------------------------------------- #
# Normalized cache value: {fraction_ai, fraction_human, prediction_short}
# --------------------------------------------------------------------------- #
def _normalize_document(data: dict) -> dict:
    """Normalize a single-text success payload to the cached shape."""
    return {
        "fraction_ai": data.get("fraction_ai"),
        "fraction_human": data.get("fraction_human"),
        "prediction_short": data.get("prediction_short"),
    }


def _reconstruct(windows: list, start: int, end: int) -> dict:
    """Rebuild a per-reply fraction_ai from the windows overlapping [start, end),
    weighting each window by how many characters it contributes to the reply."""
    ai = assisted = human = 0.0
    for w in windows or []:
        ws, we = w.get("start_index", 0), w.get("end_index", 0)
        overlap = max(0, min(end, we) - max(start, ws))
        if overlap <= 0:
            continue
        label = (w.get("label") or "").lower()
        if "human" in label:
            human += overlap
        elif "assist" in label:
            assisted += overlap
        else:
            ai += overlap
    total = ai + assisted + human
    if total == 0:
        return {"fraction_ai": None, "fraction_human": None, "prediction_short": None}
    fa, fh = ai / total, human / total
    short = "AI" if fa >= 0.5 else "Human" if fh >= 0.5 else "Mixed"
    return {"fraction_ai": round(fa, 4), "fraction_human": round(fh, 4),
            "prediction_short": short}


def _map(norm: dict) -> dict:
    """Cached normalized dict -> the p_* fields the harness records."""
    fa = norm.get("fraction_ai")
    return {
        "p_fraction_ai": fa,
        "p_fraction_human": norm.get("fraction_human"),
        "p_prediction": norm.get("prediction_short"),
        "p_reads_human": fa is not None and fa < config.PANGRAM["ai_threshold"],
    }


# --------------------------------------------------------------------------- #
# Batching
# --------------------------------------------------------------------------- #
def _pack(texts: list, max_words: int) -> list:
    """Greedily group texts so each group stays under max_words."""
    groups, cur, cur_w = [], [], 0
    for t in texts:
        w = len(t.split())
        if cur and cur_w + w > max_words:
            groups.append(cur)
            cur, cur_w = [], 0
        cur.append(t)
        cur_w += w
    if cur:
        groups.append(cur)
    return groups


def _concat(group: list):
    """Join a group with separators, tracking each reply's [start, end) offsets."""
    doc, spans = "", []
    for i, t in enumerate(group):
        if i > 0:
            doc += _SEP
        start = len(doc)
        doc += t
        spans.append((t, start, len(doc)))
    return doc, spans


def score_many(texts: list) -> list:
    """Score many texts with minimal credits: skip cached ones, batch the rest
    into <=max_words calls, reconstruct + cache each reply. Returns p_* dicts in
    the same order as `texts`."""
    max_words = config.PANGRAM["batch_max_words"]
    todo, seen = [], set()
    for t in texts:
        if t not in seen:
            seen.add(t)
            if cache.load("pangram", t) is None:
                todo.append(t)

    planned = len(_pack(todo, max_words))
    print(f"[pangram] plan: {planned} new call(s) ~{planned} credit(s). {status()}")

    for group in _pack(todo, max_words):
        if len(group) == 1:
            # a lone text: score it directly (its document score is exact)
            cache.store("pangram", group[0], _normalize_document(_detect(group[0])))
            continue
        doc, spans = _concat(group)
        data = _detect(doc)
        windows = data.get("windows") or []
        for (t, s, e) in spans:
            cache.store("pangram", t, _reconstruct(windows, s, e))

    return [_map(cache.load("pangram", t)) for t in texts]


def score(text: str, scenario: dict) -> dict:
    """Single-text scoring (used by the eval loop). Cache-first."""
    norm = cache.cached("pangram", text, lambda: _normalize_document(_detect(text)))
    return _map(norm)


if __name__ == "__main__":
    # `python scorers/pangram.py` -> show spend status without spending anything
    print(status())
