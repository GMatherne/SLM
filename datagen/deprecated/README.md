# Deprecated: the AI-teacher generation approach

This folder holds the project's **original, abandoned** data strategy: use a
frontier model (Opus/GPT) as a "teacher" to *generate* human-sounding training
examples, filtered by an LLM judge + Pangram.

**Why it was abandoned.** We tested it against Pangram and it failed at the
premise: even heavily prompted frontier output (via the `write-humanlike-2`
skill, iterated hard) scored **100% AI** on Pangram. You cannot distill "reads
as human" from an AI teacher when "human" is *defined* as "what the AI detector
doesn't flag" — it's circular. So we pivoted to training on **real human text**
(see `../fetch_human.py` and the top-level README).

**What's here (kept for reference / possible DPO reuse):**
- `generate.py` — teacher generation (OpenAI/Anthropic by model id)
- `build_dataset.py` — generate -> judge/Pangram filter -> ShareGPT (cheap-first + batched)
- `gen_prompts.py` — task-prompt diversifier
- `questions.jsonl` — training task-prompts
- `prompts/` — `humanlike.md` (vendored write-humanlike-2 skill), `persona.md`, `task.md`, `exemplars.jsonl`

These could still feed a **DPO** stretch (human "chosen" vs AI-generated
"rejected" pairs), which is the one place AI-generated text is still useful.
Nothing in the active pipeline imports from this folder.
