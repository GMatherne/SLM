# Round 1 — findings and problems

First real train → generate → score cycle. This documents what worked, what
broke, and the data fixes for round 2. (Fix problems in the DATA, not the
hyperparameters — per the brief.)

## Setup
- **Model:** `unsloth/Qwen3-4B-Instruct-2507`, QLoRA (r=32) via Unsloth on Colab.
- **Data:** 1,400 human, pre-AI, education examples — ELI5 (250), 17 educational
  StackExchange sites (~850), Khan Academy transcripts (300).
- **Eval:** generate base (pre-train) and tuned (post-train) answers to 12 held-out
  education prompts; score `fraction_ai` on the Pangram website.

## The good news — the thesis held (early signal)

Fine-tuning on human text visibly transformed the output register:

| | Base (untuned) | Tuned |
|---|---|---|
| Format | `### headers`, `**bold**`, numbered lists | plain prose |
| Openers | "Certainly!", "Great question!" | none |
| Punctuation | em dashes | plain |
| Length | 190–240 words | 20–166 words |
| Voice | generic AI assistant | conversational, ELI5/Khan-like |

**Pangram scores (tuned answers ≥50 words):**

| # | prompt | base | tuned |
|---|--------|------|-------|
| 1 | how vaccines work | 100% AI | **100% human** |
| 3 | compound interest | 100% AI | 100% AI |
| 10 | what is a black hole | 100% AI | **100% human** |

**2 of 3 matched pairs flipped from 100% AI to 100% human** by training on human
text alone. That is direct support for "behavior from data": a model that could
NOT be prompted past Pangram was moved off 100% AI by the training data. First round.

Caveat: n is tiny (3 scoreable pairs; the other 9 tuned outputs were <50 words,
Pangram's minimum). Round 2's length floor should make most outputs scoreable so
we get a real hit-rate, not 3 points.

## The problems

### P1 — Spoken-lecture tics (from Khan)
The tuned model overuses "So…", starts sentences with "And," and opens with "So
let's talk a little bit about…". These are learned from the **Khan transcripts**,
which are spoken lectures. Undesirable for a written tutor. The one tuned answer
that scored **AI (#3)** is also the most Khan-spoken of the three — suggestive,
not conclusive.

### P2 — Meta-openers
"I'll try." (#10) — the model answered an *explain* prompt as if accepting a
request. A conversational-transcript artifact, not tutoring prose.

### P3 — Answers too short
Many tuned answers came out 20–40 words: too terse to be a good explanation, and
**below Pangram's 50-word minimum** — so 9 of 12 outputs couldn't even be scored.
Cause: the corpus is full of short answers (ELI5 one-liners, Khan chunks capped
at ~180 words, terse SE replies), so the model learned brevity.

### P4 — Measurement gaps
- Only 3/12 tuned outputs were long enough to score.
- Base arm not yet scored → no complete base-vs-tuned delta.
- Small n overall; Pangram gives near-binary verdicts on short docs.

## Root causes (all data-side)
- **Khan is over-influential** for the spoken register and its tics.
- **Short source answers** taught the model to under-explain.
- **Source mix** wasn't tuned for a clean written-tutor voice.

## Round-2 fixes (data)
1. **De-Khan-ify:** cut or heavily down-weight Khan transcripts; lean on ELI5 +
   StackExchange (written prose).
2. **Tic filter** in `fetch_human.py`: drop answers that start with "So/And/Well"
   or meta-openers ("I'll try"), and cap "so" density.
3. **Length floor:** prefer answers ≥ ~60–80 words so the model learns complete
   explanations (and outputs are Pangram-scoreable).
4. **(Optional) feedback register:** still missing; add a non-code prose source.
5. **Re-run and re-score properly:** score BOTH arms on all ≥50-word outputs for a
   real matched delta; make sure enough tuned outputs clear 50 words.

## One open question
Why did #3 score AI while #1/#10 read human, when all three shifted register? Could
be the Khan-spoken structure, the hypothetical-walkthrough content, or Pangram
noise on a 142-word doc. More scored examples in round 2 should clarify.
