"""Teacher-model generation: turn a writing task into the finished piece, using the
vendored write-humanlike-2 guidance + the fixed persona + the task rules, plus a
few curated gold examples (few-shot).

The assembled prompt is hashed into a PROMPT_VERSION so every dataset row records
exactly which prompt produced it. Change any prompt file or the exemplars and the
version changes automatically -- that's your A/B provenance.
"""

from __future__ import annotations

import hashlib
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
PROMPTS = os.path.join(HERE, "prompts")
EXEMPLARS = os.path.join(PROMPTS, "exemplars.jsonl")

# Provider chosen by model id: "claude-*" -> Anthropic, else -> OpenAI.
# Override with the exact id you have (e.g. gpt-5, gpt-4.1, gpt-4o).
TEACHER_MODEL = os.getenv("TEACHER_MODEL", "gpt-5")
MAX_FEWSHOT = int(os.getenv("MAX_FEWSHOT", "3"))

# Per-process call-count circuit breaker against runaway generation loops.
LLM_MAX_CALLS_PER_RUN = int(os.getenv("LLM_MAX_CALLS_PER_RUN", "500"))
_calls = 0


def _read(name: str) -> str:
    with open(os.path.join(PROMPTS, name), "r", encoding="utf-8") as f:
        # drop HTML comments so internal notes don't reach the model
        lines = [ln for ln in f.read().splitlines()]
    text = "\n".join(lines)
    while "<!--" in text and "-->" in text:
        a, b = text.index("<!--"), text.index("-->") + 3
        text = text[:a] + text[b:]
    return text.strip()


def build_system_prompt() -> str:
    return "\n\n".join([_read("humanlike.md"), _read("persona.md"), _read("task.md")])


def load_exemplars() -> list[dict]:
    """Gold (question, response) pairs promoted from earlier good generations.
    These are the strongest lever: as you find outputs that score well, add them
    here and every later generation imitates them."""
    if not os.path.exists(EXEMPLARS):
        return []
    rows = []
    with open(EXEMPLARS, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows[:MAX_FEWSHOT]


def prompt_version() -> str:
    payload = build_system_prompt() + json.dumps(load_exemplars(), sort_keys=True)
    return "v" + hashlib.sha256(payload.encode("utf-8")).hexdigest()[:8]


def _messages(question: str) -> list[dict]:
    msgs = []
    for ex in load_exemplars():
        msgs.append({"role": "user", "content": ex["question"]})
        msgs.append({"role": "assistant", "content": ex["response"]})
    msgs.append({"role": "user", "content": question})
    return msgs


def generate(question: str) -> str:
    global _calls
    if _calls + 1 > LLM_MAX_CALLS_PER_RUN:
        raise RuntimeError(
            f"Teacher per-run cap reached ({LLM_MAX_CALLS_PER_RUN} calls). "
            f"Circuit breaker; raise LLM_MAX_CALLS_PER_RUN if intended."
        )
    _calls += 1
    system = build_system_prompt()
    if TEACHER_MODEL.startswith("claude"):
        from anthropic import Anthropic

        client = Anthropic()  # reads ANTHROPIC_API_KEY
        msg = client.messages.create(
            model=TEACHER_MODEL,
            max_tokens=800,
            system=system,
            messages=_messages(question),
        )
        return msg.content[0].text.strip()

    from openai import OpenAI

    client = OpenAI()  # reads OPENAI_API_KEY
    # OpenAI takes the system prompt as the first message.
    messages = [{"role": "system", "content": system}] + _messages(question)
    r = client.chat.completions.create(model=TEACHER_MODEL, messages=messages)
    return r.choices[0].message.content.strip()


if __name__ == "__main__":
    # quick manual check of the current prompt on one question
    import sys

    q = sys.argv[1] if len(sys.argv) > 1 else "Write a short email to your landlord asking them to fix a leaking faucet."
    print(f"[{prompt_version()}]\n")
    print(generate(q))
