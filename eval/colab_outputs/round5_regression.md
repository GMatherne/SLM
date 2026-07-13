# Regression (general-ability) report

Judge: `openai-group/gpt-5`  |  12 tasks

- **mean follows — base 1.42/2  vs  tuned 0.75/2**
- **regressions (tuned worse than base): 6/12**
- **register bleed (chatty voice where inappropriate): 6/12**

| # | category | base /2 | tuned /2 | bleed | regression | note |
|---|----------|---------|----------|-------|------------|------|
| 0 | coding | 0 | 0 | Y | — | The base response never delivers a valid final function and has syntax/logic errors, while the tuned response is chatty and its function incorrectly treats n<2 (e.g., 0 or 1) as prime. |
| 1 | arithmetic | 0 | 0 | Y | — | Both answers give the wrong number (401 instead of 391), and the tuned answer is chatty with extra explanation instead of a bare number. |
| 2 | summarize | 2 | 1 | — | Y | The base response is a single accurate sentence, while the tuned response is accurate but adds a separate 'Source: AP' sentence, breaking the one-sentence constraint. |
| 3 | format | 2 | 2 | — | — | Both answers are bare valid JSON arrays of three color strings with no extra prose. |
| 4 | terse | 1 | 1 | Y | — | Both provide the correct city but fail the one-word format; the tuned answer also adds unnecessary explanatory text in a chatty voice. |
| 5 | register | 2 | 0 | — | Y | The base answer is a single professional sentence requesting Friday-to-Monday rescheduling, while the tuned answer is multiple sentences and does not specify Monday. |
| 6 | creative | 2 | 1 | — | Y | The base response is exactly two lines that rhyme; the tuned response has two lines about the sea but they do not rhyme. |
| 7 | reasoning | 0 | 0 | Y | — | Neither answer gives the correct 9:00 pm end time; the tuned answer is incoherent and chatty with self-corrections, indicating register bleed. |
| 8 | constraint | 2 | 1 | — | Y | The base response is a standard, correct one-sentence definition, whereas the tuned response is one sentence but inaccurately defines nouns as things that can exist independently of other words. |
| 9 | constraint | 2 | 0 | Y | Y | Base answer gives only '1989' as required; tuned answer adds explanations and narrative, violating the no-explanation constraint and adopting an explainer voice. |
| 10 | format | 2 | 1 | Y | Y | The base answer correctly provides the table (even if fenced) with correct values, while the tuned answer includes the correct table but adds unnecessary explanatory text in a chatty first-person voice. |
| 11 | classify | 2 | 2 | — | — | Both answers provide the correct one-word sentiment 'negative' with no extra text. |
