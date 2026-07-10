# eval — is the tuned model more human than the base?

The question: on held-out education prompts, does the fine-tuned model's
`fraction_ai` (per Pangram) drop below the base model's ~100%? Even a partial
drop is a real, reportable result.

## Active path (what we actually do now)

Generation runs in Colab (`train/colab_train.py`) and produces `base_outputs.json`
+ `tuned_outputs.json` on 12 held-out prompts. We score those on the **Pangram
website by hand** (the API isn't on the current plan) and compare base vs tuned.
The prompts live in `scenarios.jsonl` (kept in sync with `colab_train.py`), held
OUT of training.

## Automated harness (for when API access exists)

`run_eval.py` orchestrates: generate (or load `--outputs`) → score with the
enabled scorers → print a base-vs-tuned table. Usable today only in part, because
two scorers need API access we don't currently have.

- **`scorers/pangram.py`** — the objective "reads human" signal via Pangram's v3
  async API (POST /task → poll → `fraction_ai`), with **batched** scoring and
  **hard spend caps**. OFF until a Pangram API key exists (`TOGGLES.pangram`).
- **`scorers/judge.py`** — LLM-as-judge (`reads_human` + `task_quality`), provider
  by model id. **Currently blocked** (OpenAI billing inactive; no Anthropic key).
- **`scorers/surface.py`** — free descriptive AI-tell stats (em-dash rate, markdown,
  etc.). **Informational only — never a gate.**
- `config.py` holds the Behavior Spec, model/backend settings (transformers or
  local Ollama), and the spend caps. `models.py` loads base / base+adapter or
  hits Ollama. `report.py` prints the verdict table + surface section.

## Spend caps (eval/config.py)
`PANGRAM_CREDIT_BUDGET` (persistent lifetime ledger), `PANGRAM_MAX_CALLS_PER_RUN`,
`PANGRAM_DRY_RUN`, and `LLM_MAX_CALLS_PER_RUN` — enforced before any paid call so
a bug can't drain credits.

## Files
- `scenarios.jsonl` — held-out education prompts (keep OUT of training).
- `scorers/` — pangram, judge, surface, cache.
- `run_eval.py` / `config.py` / `models.py` / `report.py` — the automated harness.
