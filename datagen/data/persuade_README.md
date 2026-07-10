# PERSUADE essays — PARKED (not used in round 1)

`persuade_full_text.csv` — 25,996 human argumentative student essays (grades 6–12,
2021–22, pre-ChatGPT), from the PERSUADE 2.0 corpus (Crossley et al.), via the HF
mirror `realbenpope/PERSUADE_manageable`. CC BY-NC-SA. Genuinely human.

## Status: HOLD until after the first training round
Per decision: the first round trains only on the education/tutoring corpus
(`human_dataset.jsonl`, 494 examples). These essays are shelved for a possible
second round, to be reconsidered after we see whether fine-tuning on the 494
moves Pangram.

## Caveats to remember when we do use them
- **No prompts in this mirror** — only `essay_id_comp` + `full_text`. To make
  (prompt → essay) pairs we'd synthesize a generic prompt ("write an argumentative
  essay…") or find the prompt-carrying full CSV (Kaggle / the Google Drive links
  in github.com/scrosseye/persuade_corpus_2.0).
- **Different task** than tutoring — argumentative essays, not explanation/feedback.
- **Volume** — 25,996 vs 494; use only a small sample so it doesn't swamp tutoring.
- Length-filter/chunk (essays run long) and Pangram-spot-check a few before use.
