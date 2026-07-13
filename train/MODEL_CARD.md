---
license: apache-2.0
base_model: unsloth/Qwen3-8B
tags:
  - qwen3
  - qlora
  - unsloth
  - educational
  - human-sounding
language:
  - en
pipeline_tag: text-generation
---

# Qwen3-8B — Human-Sounding Educational Tutor (QLoRA)

A QLoRA fine-tune of **Qwen3-8B** (non-thinking) trained to answer everyday
educational/tutoring questions in **natural, human-sounding prose** — text that an
AI-text detector (Pangram) reads as human-written rather than AI-generated.

**This is a course/research artifact demonstrating "behavior from data," not a
production tutor.** The target behavior is *voice*, and (see Evaluation) that voice
is bought at a real cost in factual accuracy versus the untuned base — so do **not**
use it as a source of factual authority.

## What it does

Given a student's question — explain a concept, help with an essay, correct a
mistake — it responds the way a knowledgeable human would in a forum answer:
conversational, direct, first-person, without the padding, hedging, list-scaffolding,
and even pacing that give default AI writing away. It answers as an AI assistant (it
never claims to be a person) and does not cite sources or add sign-offs.

## Training

- **Base:** `unsloth/Qwen3-8B`, run in **non-thinking** mode (`enable_thinking=False`).
- **Method:** QLoRA (4-bit) via [Unsloth](https://github.com/unslothai/unsloth) —
  LoRA `r=32`, `alpha=32`, dropout 0, all 7 attention+MLP projections; 2 epochs,
  lr `2e-4`, ChatML template, `train_on_responses_only`.
- **Data:** ~1,800 curated, heavily-cleaned **human** answers from StackExchange and
  Reddit (ELI5 / AskScience / AskHistorians / topic SE sites), filtered to remove
  forum scaffolding, fabricated citations, links, markdown, and non-English text.
  The dataset is the real deliverable; training is a downstream button-press.
- Two variants: **SFT** (the fine-tune) and **DPO** (a preference-tuning pass on top).

## Evaluation (honest)

LLM-as-judge (GPT-5) on 16 held-out education prompts, base vs tuned:

| Model | Accuracy /5 | Info retention | Answers w/ ≥1 error | Confident fabrications |
|---|---|---|---|---|
| Qwen3-8B base (untuned) | **4.56** | 65% | 3/16 | 1 |
| This model — SFT | 3.25 | 64% | 11/16 | 12 |
| This model — DPO | 2.88 | 56% | 15/16 | 11 |

**Human-ness (Pangram AI-detector):** SFT reads **human on 13/16 (81%)** held-out
answers; the DPO variant reads **human on 16/16 (100%)**. The base reads as AI. This
is the metric the model is optimized for — the whole point of the fine-tune.

**Read this honestly:** fine-tuning for the human voice **lowers factual accuracy and
raises fabrication rate** relative to the strong base model. It also degrades
instruction-following on terse/format-constrained tasks (write code, "answer in one
word", JSON) — it tends to over-explain. The defensible result is *reliable human
voice in a small local model*, not raw capability.

## Intended use & limitations

- **Use:** research/education on data-driven behavior control; generating
  human-reading educational prose where factual precision is not critical.
- **Do not use** for authoritative facts, math, code, or format-constrained output.
- May still occasionally read as AI on some prompts; may state confident but wrong
  claims (a "forum register" side-effect).

## Usage

**Ollama (GGUF):**
```
ollama create qwen3-human -f Modelfile   # Modelfile FROM ./qwen3-human*.Q8_0.gguf
ollama run qwen3-human
```

**Transformers:** load the merged weights and apply the ChatML chat template with the
system prompt below; sample at `temperature=0.7, top_p=0.8, top_k=20,
repetition_penalty=1.15`.

**System prompt used in training/inference:**
> You are a helpful AI tutor. You explain concepts clearly and accurately, covering
> the actual mechanism or reasoning rather than a vague summary. You help with writing
> and correct mistakes, in natural, plain language. You are an AI assistant — you never
> claim to be a human, a person, or a product. Never cite specific studies, papers,
> books, articles, authors, DOIs, or web links, and never invent a source or title —
> explain things in your own words. Do not end with sign-offs like "hope this helps."

## License

Apache-2.0, inheriting the base model (`unsloth/Qwen3-8B`).
