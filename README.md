# SLM — teaching a small model to write human-sounding educational text

Course project (see `Train_Your_Own_Small_Learning_Model.md`): take a small open
base model and, by controlling its **training data**, make it reliably do one
narrow thing. Our thing:

> **Given an education prompt (a question to tutor, a concept to explain, an essay
> to help with), write a helpful answer that reads as human-written rather than
> AI-generated.**

The objective proxy for "reads human" is **Pangram** (an AI-text detector): an
instruct base model's answers read as AI; the question is whether fine-tuning on
human text flips the tuned model to read *human*. A prompted model **cannot** do
this (distilling "human" from an AI is circular — see below), so it's a genuine
"behavior from data" target.

## The one decision that shaped everything

We started by trying to *generate* training data with a frontier "teacher" model
prompted to write human-like. **It failed the premise:** that output reads as AI to
Pangram no matter how you prompt it. So we **pivoted to training on real, pre-AI,
human text** (StackExchange / Reddit education answers). The abandoned generation
code lives in `datagen/deprecated/`.

## Results (round 6 — the headline)

Base model **Qwen3-8B** (non-thinking), QLoRA fine-tuned on ~1,800 cleaned human
answers, then a DPO pass. Held-out education prompts, judged by GPT-5 (accuracy)
and Pangram (human-ness):

| Qwen3-8B | Accuracy /5 (GPT-5 judge) | Reads **human** (Pangram) | Confident fabrications |
|---|---|---|---|
| Base (untuned) | **4.56** | reads as AI¹ | 1 |
| SFT (fine-tuned) | 3.25 | 13/16 (81%) | 12 |
| **DPO** (preference-tuned) | 2.88 | **16/16 (100%)** | 11 |

¹ Base reads as AI — the project premise; round-1 spot-check had the base at 100% AI.

**The experiment worked.** Training on human data flips the model from reads-AI to
reads-human — **DPO reaches 100% human** — confirming *behavior from data*. The
cost is real and expected: accuracy falls from 4.56 → ~3 and fabrications rise,
because the casual human-forum register is less precise than the base's careful
(AI-sounding) prose. **These models demonstrate reliable human *voice*, not a more
accurate tutor** — the defensible win the course asks for. DPO is the most human
*and* least accurate; it bought voice with accuracy. (The two held-outs SFT left
reading AI were #14 essay-feedback and #15 "make the case" — the structured/
evaluative registers — and DPO's voice-tuning fixed both.)

Secondary finding — **regression**: the tuned models over-explain on terse/
format-constrained tasks ("answer in one word", write code) — a narrow-fine-tune
side-effect (`eval/regression_eval.py`).

## Pipeline

```
datagen/   pull + clean human educational text  ->  data/human_dataset.jsonl (~1,800)
train/     QLoRA fine-tune Qwen3-8B (Unsloth, Colab A100): SFT -> DPO  ->  adapters + GGUF
eval/      base-vs-tuned on held-out prompts: GPT-5 judge (accuracy + regression)
           + Pangram (human-ness, by hand) + blind human eval
```

### Data (the real deliverable) — `datagen/`
- **`fetch_human.py`** — pulls human, pre-ChatGPT, prompt-paired education text from
  the HF datasets-server (ELI5, AskScience, AskHistorians, ~30 topic StackExchange
  sites). Cleans hard (forum scaffolding, fabricated citations/links, markdown,
  non-English, length) but **never rewrites** (rewriting reintroduces the AI signal).
  Output: **`data/human_dataset.jsonl`** (ShareGPT), ~1,800 answers.
- **`_test_cleaning.py`** — 173 neg-guarded unit tests for the cleaning filters
  (`python datagen/_test_cleaning.py`); **`CLEANING.md`** documents every rule.
- **`data/essays_college.json`** — reflective college essays for the essay-feedback
  behavior. `essays_cmv.json` is parked (dropped source; `--cmv 0`).
- **`deprecated/`** — the abandoned AI-teacher generation approach.

### Training — `train/`
- **`colab_train.py`** — SFT. Runs in Colab; `MODEL`/`BATCH` via env
  (`MODEL=unsloth/Qwen3-8B`). Non-thinking (`enable_thinking=False`). Generates
  base + tuned answers on the held-out eval + regression prompts, saves the adapter,
  and auto-converts a `qwen3-human.Q8_0.gguf` for Ollama.
- **`dpo_build_pairs.py` / `dpo_train.py`** — the DPO stretch: build preference
  pairs, then preference-tune on top of the SFT adapter.
- **`Modelfile`** (Ollama) + **`MODEL_CARD.md`** (HF) + **`convert_to_gguf.md`**.
- Published model: **`GMatherne/qwen3-8b-human-sft`** on the HF Hub.

### Eval — `eval/`
- **`accuracy_eval.py`** / **`regression_eval.py`** — LLM-as-judge (GPT-5 via an
  OpenAI-compatible gateway) scoring accuracy + retention + fabrications, and
  general-ability regression (base vs tuned). Parallel, cached.
- **Pangram** (the headline human-ness metric) — scored by hand on the website
  (`pangram_score_*.md` are paste-ready sheets); `pangram_score.py` + `scorers/`
  wrap the v3 API with hard spend caps for when API credits exist.
- **`human_eval.py`** — a blind human-vs-Pangram cross-check sheet.
- Final results live in `eval/colab_outputs/round6_*` (round-5 kept for comparison).

## Reproduce

```bash
# 1. Build/verify the human corpus (no GPU, no keys)
cd datagen && python fetch_human.py && python _test_cleaning.py

# 2. Train in Colab (A100): upload the train/ + eval/ scripts + human_dataset.jsonl,
#    set MODEL=unsloth/Qwen3-8B, run colab_train.py (SFT) then dpo_build_pairs + dpo_train (DPO).

# 3. Score: accuracy_eval.py / regression_eval.py (gateway judge) + paste the
#    pangram_score_*.md answers into pangram.com. Compare base -> SFT -> DPO.
```

## Status & remaining work
- **Done:** dataset, 8B SFT + DPO, full base-vs-tuned results (accuracy, human-ness,
  regression), model card, model published to HF, brainlift.
- **To finish the submission:** publish the dataset to HF; record the 3–5 min demo
  video; the blind human-eval sheet is optional extra evidence.

## Honest caveats
- **Fine-tuning trades accuracy for voice.** The tuned models are less accurate than
  the 8B base and occasionally state confident-but-wrong claims — do not treat them
  as factual authorities. The win is *human voice*, measured on Pangram.
- **Regression:** the tuned models over-explain on terse/coding/format tasks.
- Source docs (`brainlift.md`, `ai-cleanup-guide.md`) are research/reference, not
  code inputs.
