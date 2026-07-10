# datagen — build the human educational corpus

The dataset is the deliverable. This directory pulls **real, pre-ChatGPT, human**
educational text, cleans it, and QAs it. It does **not** generate text with an AI
(that approach failed against Pangram — see `deprecated/`).

## Tools

- **`fetch_human.py`** — pull + filter + write the corpus.
  ```bash
  python fetch_human.py                 # default volumes (~1,400)
  python fetch_human.py --dry           # print samples, don't write
  python fetch_human.py --eli5 300 --se-per-site 60 --khan 400   # scale up
  ```
  Sources (all human, pre-AI, prompt-paired, via the HF datasets-server REST API):
  - **ELI5** (`sentence-transformers/eli5`) — friendly explanations
  - **17 educational StackExchange sites** (`flax-sentence-embeddings/...`):
    ell, english, physics, biology, chemistry, astronomy, earthscience, history,
    philosophy, economics, linguistics, cogsci, health, music, hsm, matheducators,
    academia
  - **Khan Academy transcripts** (`iblai/ibl-khanacademy-transcripts`) — cleaned
    from WebVTT, prompt = "Can you explain {title}?"

  Filters (in `ok()`): length 25–300 words, English/ASCII, **no code, no LaTeX,
  no markdown image-refs, no all-caps, no mojibake**. It never rewrites the text.
  Output: `data/human_dataset.jsonl` (ShareGPT) + `data/human_dataset_full.jsonl`
  (with `source` tags for QA).

- **`quality_report.py`** — mechanical QA on a corpus file.
  ```bash
  python quality_report.py data/human_dataset_full.jsonl
  ```
  Length distribution, dedup, and flags (image_ref / toxic / shouty / code-LaTeX).
  It does NOT judge "reads human" (Pangram) or content quality (a judge/eyeball).

- **`make_pangram_checks.py`** — emit a paste-ready file to validate a stratified
  sample on the Pangram website, one submission per example (clean per-example
  scores, no window-blending).
  ```bash
  python make_pangram_checks.py --per-source 2   # -> data/pangram_checks.md
  ```

## Quality gates (what "good data" means here)
1. **Reads human** — the whole point. Confirm a sample on Pangram (`make_pangram_checks.py`).
2. **Clean prose** — `quality_report.py` + the fetch filters.
3. **On-domain** — education (tutoring/explanation). Sources are chosen for this.

## Notes
- **Feedback register is thin.** We dropped Code Review (code-laden) and Writing
  SE yields little, so the corpus is currently tutoring/explanation. A non-code
  prose-feedback source is a TODO if we want the model to *critique*, not just explain.
- `data/persuade_full_text.csv` — parked essays for round 2 (`data/persuade_README.md`).
- `deprecated/` — the abandoned AI-teacher generation pipeline.
