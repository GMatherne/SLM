# SLM — teaching a small model to write human-sounding educational text

Course project (see `Train_Your_Own_Small_Learning_Model.md`): take a small open
base model and, by controlling its **training data**, make it reliably do one
narrow thing. Our thing:

> **Given an education prompt (a question to tutor, a concept to explain), write
> a helpful answer that reads as human-written rather than AI-generated.**

The objective proxy for "reads human" is **Pangram** (an AI-text detector): a
base model's answers score ~100% AI; the question is whether fine-tuning on
human text moves the tuned model's `fraction_ai` down. The base model **cannot**
do this from prompting alone (we verified: even a heavily-prompted frontier model
reads 100% AI to Pangram), so it's a real "behavior from data" target.

## The one decision that shaped everything

We started by trying to *generate* training data with a frontier "teacher" model
(Opus/GPT) prompted to write human-like. **It failed the premise:** that output
reads 100% AI to Pangram no matter how hard you prompt it — distilling "human"
from an AI is circular. So we **pivoted to training on real, pre-AI, human text.**
(The abandoned generation code lives in `datagen/deprecated/`.)

## Pipeline

```
datagen/   pull + clean + QA real human educational text  ->  human_dataset.jsonl
train/     QLoRA fine-tune Qwen3-4B on it (Unsloth, on Colab)  ->  LoRA adapter
eval/      base-vs-tuned: generate on held-out prompts, score fraction_ai on Pangram
```

### Data (the real deliverable) — `datagen/`
- **`fetch_human.py`** — pulls human, **pre-ChatGPT**, prompt-paired education text
  from the HF datasets-server (no big downloads): **ELI5** (friendly explanations),
  **17 educational StackExchange sites** (ell/english/physics/biology/history/
  philosophy/… — tutoring register), and **Khan Academy transcripts**. Filters out
  code, LaTeX, image-refs, non-English, and out-of-range lengths — but never
  rewrites (rewriting reintroduces the AI signal). Output: **`data/human_dataset.jsonl`**
  (ShareGPT format) — currently **~1,400 examples**.
- **`quality_report.py`** — mechanical QA (length, dedup, code/LaTeX leaks, flags).
- **`make_pangram_checks.py`** — emits a paste-ready file to spot-check a stratified
  sample on the Pangram website (confirming the corpus reads human).
- **`data/essays_cmv.json` / `essays_college.json`** — parked essay data (ChangeMyView
  argument + reflective college essays) for a **round-3** general-writing experiment,
  kept out of the education rounds (see `data/essays_README.md`).
- **`deprecated/`** — the abandoned AI-teacher generation approach.

### Training — `train/`
- **`colab_train.py`** — the active path. Run in Google Colab (free T4 fits 4B
  QLoRA via Unsloth). Trains on the corpus, then generates **base and tuned**
  answers on 12 held-out education prompts, so you leave with the adapter +
  `base_outputs.json` + `tuned_outputs.json`.
- **`train.py`** — the same training as a plain script (for a cloud box that isn't
  Colab). Won't fit 4B on an 8GB local card.

### Eval — `eval/`
- **Active path:** score the base vs tuned answers from Colab on the **Pangram
  website** by hand (no API on the current plan). Does tuned `fraction_ai` drop
  below base's ~100%? Even a partial drop is a real, reportable result.
- **`scorers/`** — `pangram.py` (v3 async API + batched + hard credit caps),
  `surface.py` (descriptive AI-tell stats, informational only), `judge.py`
  (LLM-as-judge; OpenAI/Anthropic by model id — **currently blocked** on OpenAI
  billing). `run_eval.py`/`config.py`/`models.py`/`report.py` are the automated
  harness for when API access exists; today we run eval manually via Colab + Pangram.
- Spend is hard-capped: `PANGRAM_CREDIT_BUDGET`, `PANGRAM_MAX_CALLS_PER_RUN`,
  `LLM_MAX_CALLS_PER_RUN` (see `eval/config.py`).

## Status

- **Data: ready** — ~1,400 clean, human, pre-AI education examples; a sample
  validated as 100% human on Pangram.
- **Round 1: staged** — `colab_train.py` is written and points at the corpus.
- **Gate: a cloud GPU.** Nothing else blocks; 4B QLoRA can't run on the 8GB local card.
- Keys: Pangram (web plan, 600 credits/mo — no API), OpenAI (API key set but
  **billing inactive**, so teacher/judge are offline). Base inference + the demo
  run locally via **Ollama** (`qwen3:4b`).

## Direction

1. **Round 1:** train on ~1,400 → score base vs tuned on Pangram. *Does human
   data move the needle off ~100% AI?* This is the whole experiment.
2. **If it moves:** expand data (more sources, a prose *feedback* register, the
   parked essays as a round-3 general-writing experiment), iterate, maybe DPO (stretch).
3. **Ship:** publish dataset, model on HF Hub, a running Ollama demo, the
   base-vs-tuned results, and the brainlift with evidence.

## Run it

```bash
# 1. Build/refresh the human corpus (no GPU, no keys)
cd datagen && python fetch_human.py && python quality_report.py data/human_dataset_full.jsonl

# 2. Train + generate base/tuned (in Colab: GPU runtime; upload colab_train.py + human_dataset.jsonl)
pip install unsloth && python colab_train.py

# 3. Score base_outputs.json vs tuned_outputs.json on the Pangram website; compare fraction_ai
```

## Honest caveats
- `colab_train.py` is **untested on a live GPU** — Unsloth/TRL APIs move fast, so
  the first run may need a small fix (likely `SFTConfig` args or the
  `train_on_responses_only` markers).
- Whether a 4B fine-tune actually moves Pangram is **genuinely unknown** — that's
  the open research question this project exists to answer.
- Source docs (`brainlift.md`, `ai-cleanup-guide.md`) are research/reference, not
  code inputs.
