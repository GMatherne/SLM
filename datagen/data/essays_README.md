# Parked essay data — for round 3 (NOT used in round 2)

Round 2 is education-only (tutoring/explanation) to keep that result clean. These
essay sources are parked for a round-3 general-writing experiment, added as a
SMALL secondary register so they don't swamp the education corpus.

## Sources collected
- `essays_cmv.json` (206) — r/ChangeMyView. Adult **argumentative** essays,
  prompt = the OP's "view", human, pre-2022. Good volume + clear prompts. Matches
  the evaluative/argumentative side of Grant's essays (analysis, paper reviews).
- `essays_college.json` (60) — college admissions essays + attached feedback.
  **Reflective/narrative** register (closest to the "technology and self" essay),
  and doubles as feedback-register data. Small; scraped provenance (some mojibake)
  -> Pangram-validate before use.

## Rejected
- PERSUADE (removed) — no prompts, grade 6–12 quality.
- BAWE / MICUSP (true university academic) — not available on Hugging Face.

## Round-3 TODO when we use these
- Format as (prompt -> essay) ShareGPT; for college essays synthesize a prompt or
  pair with the feedback.
- Length-filter / chunk to a sane range; Pangram-spot-check a sample (esp. college).
- Keep it a minor fraction of the corpus so education stays dominant.
- Measure separately: does adding essays help general writing WITHOUT hurting the
  education base-vs-tuned result?
