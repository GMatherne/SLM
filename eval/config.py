"""Central config for the eval harness.

Everything the harness needs to know lives here so the rest of the code stays
generic. Edit the Behavior Spec and thresholds as your target sharpens.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field


# --------------------------------------------------------------------------- #
# Behavior Spec  --  the single source of truth for what "pass" means.
# This string is injected into the LLM-judge prompt, so keep it falsifiable:
# a stranger should be able to mark any output pass/fail using it alone.
# --------------------------------------------------------------------------- #
BEHAVIOR_SPEC = """\
Given an education prompt (a question to answer or tutor, or a concept to
explain), the model writes a helpful, correct answer the way a knowledgeable
person actually would: natural human prose that a reader -- and an AI detector --
would take as human-written, not AI-generated. It explains clearly and directly
and answers what was asked, without the padding, hedging, and generic shape that
give AI writing away.
"""

# --------------------------------------------------------------------------- #
# Models
# --------------------------------------------------------------------------- #
# Base (untuned) model id from the HF hub, and the local path to your trained
# LoRA adapter. The tuned model = base + adapter loaded via peft.
BASE_MODEL = os.getenv("BASE_MODEL", "Qwen/Qwen3-4B-Instruct-2507")
ADAPTER_PATH = os.getenv("ADAPTER_PATH", "outputs/adapter")  # set once you train

# Generation settings used for BOTH base and tuned so the comparison is fair.
GEN = {
    "max_new_tokens": 400,
    "temperature": 0.7,
    "top_p": 0.9,
    "do_sample": True,
    "seed": 0,  # fixed so re-runs are comparable
}

# --------------------------------------------------------------------------- #
# Inference backend per arm: "transformers" (HF weights on a GPU) or "ollama"
# (local GGUF via your Ollama server). You have qwen3:4b locally, so the base
# arm defaults to Ollama -- no cloud GPU needed to generate base outputs.
#
# HONEST-COMPARISON NOTE: for the headline base-vs-tuned number, both arms should
# run through the SAME backend (same precision). Two clean options:
#   (a) after cloud training, merge the adapter + convert to GGUF, `ollama create`
#       a tuned model, set OLLAMA["tuned_model"] and TUNED_BACKEND="ollama"
#       -> both arms local, fully honest;
#   (b) run BOTH arms in the cloud with transformers.
# The default below (base=ollama, tuned=transformers) is fine for iterating, but
# note the precision mismatch when you report the final table.
# --------------------------------------------------------------------------- #
BASE_BACKEND = os.getenv("BASE_BACKEND", "ollama")
TUNED_BACKEND = os.getenv("TUNED_BACKEND", "transformers")

OLLAMA = {
    "host": os.getenv("OLLAMA_HOST", "http://localhost:11434"),
    "base_model": os.getenv("OLLAMA_BASE_MODEL", "qwen3:4b"),
    "tuned_model": os.getenv("OLLAMA_TUNED_MODEL", "qwen3-4b-human"),
    "think": False,  # suppress Qwen3 <think> blocks; we want direct replies
}

# --------------------------------------------------------------------------- #
# Scorers  --  toggle each on/off. Pangram is OFF until you have an API key.
# --------------------------------------------------------------------------- #
@dataclass
class ScorerToggles:
    judge: bool = True          # LLM-as-judge (OpenAI/Anthropic by model id) -- a verdict signal
    pangram: bool = True       # flip to True once PANGRAM_API_KEY is set -- a verdict signal
    surface: bool = True        # free descriptive surface stats -- informational only, not a gate


TOGGLES = ScorerToggles()

# LLM-as-judge. Provider is chosen by the model id: "claude-*" -> Anthropic,
# anything else -> OpenAI. Override JUDGE_MODEL with the exact id you have access
# to (e.g. gpt-5, gpt-4.1, gpt-4o for OpenAI; claude-opus-4-8 for Anthropic).
JUDGE_MODEL = os.getenv("JUDGE_MODEL", "gpt-5")
JUDGE_MAX_TOKENS = 1024

# Pangram v3 async task API (docs.pangram.com/api-reference/ai-detection).
# Wired against the real endpoint; you only need to set PANGRAM_API_KEY and flip
# TOGGLES.pangram above. (The old v1 text.api.pangram.com is deprecated, removed
# 2026-04-01 -- we use text.external-api.pangram.com.)
PANGRAM = {
    "base_url": os.getenv("PANGRAM_BASE_URL", "https://text.external-api.pangram.com"),
    "api_key_env": "PANGRAM_API_KEY",
    "auth_header": "x-api-key",
    "ai_threshold": 0.20,       # fraction_ai below this counts as "reads human"
    "poll_interval_s": 1.5,     # how often to poll the async task
    "poll_timeout_s": 120,      # give up if the task hasn't finished by then
    # batched mode: pack replies up to this many words into one call (1 credit
    # per call <=1000 words). Kept under 1000 for a safety margin vs Pangram's
    # own tokenization. Per-reply scores are recovered from the `windows` array.
    "batch_max_words": 900,
    # ---- HARD SPEND CAPS (enforced before every call; see pangram.py) -------
    # Lifetime budget: total credits this code will EVER spend, tracked in a
    # persistent on-disk ledger. Once reached, calls refuse. Your account has
    # 600; this defaults low so nothing can run away. Raise it deliberately.
    "credit_budget": int(os.getenv("PANGRAM_CREDIT_BUDGET", "50")),
    # Per-process circuit breaker: max calls in a single run, catches loops.
    "max_calls_per_run": int(os.getenv("PANGRAM_MAX_CALLS_PER_RUN", "40")),
    # Freeze switch: set PANGRAM_DRY_RUN=1 and any real Pangram call raises.
    "dry_run": os.getenv("PANGRAM_DRY_RUN", "").lower() in ("1", "true", "yes"),
}

# LLM (OpenAI/Anthropic) per-process circuit breaker for the teacher + judge.
# No credit unit like Pangram, so this is a call-count breaker against runaway
# loops. Raise LLM_MAX_CALLS_PER_RUN if a legit big run needs more.
LLM_MAX_CALLS_PER_RUN = int(os.getenv("LLM_MAX_CALLS_PER_RUN", "500"))

# --------------------------------------------------------------------------- #
# Paths
# --------------------------------------------------------------------------- #
HERE = os.path.dirname(os.path.abspath(__file__))
SCENARIOS = os.path.join(HERE, "scenarios.jsonl")
CACHE_DIR = os.path.join(HERE, ".cache")
RESULTS_DIR = os.path.join(HERE, "results")
