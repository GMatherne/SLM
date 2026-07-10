"""LLM-as-judge scorer grading each output against the Behavior Spec on two
dimensions: does it read as human-written, and is it a good answer. Provider is
chosen by config.JUDGE_MODEL id (claude-* -> Anthropic, else -> OpenAI).

Returns 0-2 integer scores per dimension plus a one-line rationale. Results are
cached by (model, spec, text) so re-runs are free.

The judge grades overall texture, not a checklist of surface tells. It is the
subjective "reads human to a person" signal; Pangram is the objective one. They
are complementary: an output should satisfy both.
"""

from __future__ import annotations

import json
import os

import config
from .cache import cached

name = "judge"

_RUBRIC = """\
Score the OUTPUT on two dimensions, each 0, 1, or 2.

reads_human:
  0 = clearly reads as AI-generated (generic, evenly-paced, padded, or hedged)
  1 = plausibly human but with stretches that feel machine-made
  2 = reads convincingly as something a real person wrote
  Judge the overall texture -- rhythm, specificity, voice -- not a checklist of
  individual words or punctuation marks.

task_quality:
  0 = doesn't do the task, off-topic, or useless
  1 = does the task acceptably but flat, or the register doesn't fit the medium
  2 = genuinely good: does the task well and fits the medium/register
"""

_PROMPT = """\
You are grading whether a model output follows a strict writing behavior spec.

BEHAVIOR SPEC:
{spec}

WRITING TASK:
{prompt}

OUTPUT TO GRADE:
\"\"\"
{output}
\"\"\"

{rubric}

Respond with ONLY a JSON object, no prose:
{{"reads_human": <0-2>, "task_quality": <0-2>, "rationale": "<one sentence>"}}
"""


def _parse_json(raw: str) -> dict:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.strip("`").split("\n", 1)[-1]
    start, end = raw.find("{"), raw.rfind("}")
    return json.loads(raw[start : end + 1])


_calls = 0  # per-process call counter (circuit breaker)


def _call_llm(prompt: str) -> dict:
    """Route by model id: 'claude-*' -> Anthropic, else -> OpenAI."""
    global _calls
    if _calls + 1 > config.LLM_MAX_CALLS_PER_RUN:
        raise RuntimeError(
            f"Judge per-run cap reached ({config.LLM_MAX_CALLS_PER_RUN} calls). "
            f"Circuit breaker; raise LLM_MAX_CALLS_PER_RUN if intended."
        )
    _calls += 1
    model = config.JUDGE_MODEL
    if model.startswith("claude"):
        from anthropic import Anthropic

        client = Anthropic()  # reads ANTHROPIC_API_KEY
        msg = client.messages.create(
            model=model,
            max_tokens=config.JUDGE_MAX_TOKENS,
            messages=[{"role": "user", "content": prompt}],
        )
        return _parse_json(msg.content[0].text)

    from openai import OpenAI

    client = OpenAI()  # reads OPENAI_API_KEY
    # JSON mode guarantees valid JSON (the prompt already says "JSON").
    r = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
    )
    return _parse_json(r.choices[0].message.content)


def score(text: str, scenario: dict) -> dict:
    prompt = _PROMPT.format(
        spec=config.BEHAVIOR_SPEC,
        prompt=scenario["prompt"],
        output=text,
        rubric=_RUBRIC,
    )
    # cache key binds judge model + spec + text so changing either invalidates
    payload = config.JUDGE_MODEL + "||" + config.BEHAVIOR_SPEC + "||" + text
    result = cached("judge", payload, lambda: _call_llm(prompt))
    return {
        "j_reads_human": result.get("reads_human"),
        "j_task_quality": result.get("task_quality"),
        "j_rationale": result.get("rationale", ""),
    }
