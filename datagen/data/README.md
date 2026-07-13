# data/ — file guide

## The corpus (what the trainer and QA read)
- **`human_dataset.jsonl`** — the **active** training corpus, ShareGPT format
  (`{"conversations":[{"from":"human",...},{"from":"assistant",...}]}`). This is
  the file you upload to Colab / `train.py` reads.
- **`human_dataset_full.jsonl`** — the same rows plus a `source` tag per row
  (`{"source","prompt","response"}`). The **QA sidecar**: `quality_report.py` and
  `make_pangram_checks.py` read this so they can group/report by source.

So each corpus is a *pair*: the ShareGPT file (for training) and the `_full`
sidecar (for QA). They hold the same examples.

## Per-round snapshots (versioning)
- **`human_dataset_round3.jsonl`** / **`_round3_full.jsonl`** — frozen round-3
  corpus (~1,520): repetition filter added, mix biased to ELI5 + AskHistorians,
  Khan dropped, `_URL_`/markdown/moderator junk stripped. This is the current
  active corpus.
- **`human_dataset_round2.jsonl`** / **`_round2_full.jsonl`** — frozen round 2
  (~1,560). We keep every round so we never lose one again (round 1's file was
  overwritten before we started versioning; its results survive in `eval/colab_outputs/`).

`human_dataset.jsonl` (active) equals the latest round's snapshot until we build
the next round, at which point the active file is overwritten and the previous
round stays frozen under its `_roundN` name. Before any overwrite, snapshot first.

## Parked (not in the current round)
- **`essays_cmv.json`** (ChangeMyView argument) / **`essays_college.json`**
  (reflective college essays + feedback) — for a **round-3** general-writing
  experiment. See `essays_README.md`. Kept out of the education rounds.

## Generated artifacts (regenerable, safe to delete)
- **`pangram_checks.md`** — a stratified paste file for manual Pangram spot-checks,
  produced by `make_pangram_checks.py`. Regenerate anytime.
