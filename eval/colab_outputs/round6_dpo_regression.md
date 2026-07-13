# Regression (general-ability) report

Judge: `openai-group/gpt-5`  |  12 tasks

- **mean follows — base 0.83/2  vs  tuned 0.67/2**
- **regressions (tuned worse than base): 4/12**
- **register bleed (chatty voice where inappropriate): 7/12**

| # | category | base /2 | tuned /2 | bleed | regression | note |
|---|----------|---------|----------|-------|------------|------|
| 0 | coding | 0 | 0 | Y | — | Neither answer provides valid Python code for is_prime, and the tuned response is a chatty explanation instead of code. |
| 1 | arithmetic | 0 | 0 | Y | — | Neither answer provides the correct bare number 391; both fail the task, and the tuned response is a chatty first-person monologue. |
| 2 | summarize | 2 | 0 | — | Y | The base answer is a single accurate sentence capturing the vote, debate, and spring construction, while the tuned answer invents a river detail and omits core facts, making it inaccurate. |
| 3 | format | 2 | 2 | — | — | Both answers are bare valid JSON arrays of three color strings with no extra text, and the tuned answer is not chatty. |
| 4 | terse | 2 | 1 | Y | Y | The base gives the correct one-word answer, while the tuned response includes extra explanation violating the one-word requirement and adopts a chatty explainer tone. |
| 5 | register | 0 | 1 | — | — | The base is meta-thought and not a single professional sentence, while the tuned email politely requests moving Friday’s meeting to Monday but uses multiple sentences, violating the one-sentence constraint; there is no register bleed. |
| 6 | creative | 0 | 0 | Y | — | Base provides no final two-line couplet; tuned gives a four-line stanza with chatty commentary instead of exactly two rhyming lines. |
| 7 | reasoning | 0 | 0 | Y | — | BASE is incoherent and never answers the given problem; TUNED misreads the start time and gives incorrect, contradictory answers in a chatty first-person style. |
| 8 | constraint | 2 | 0 | — | Y | The base answer provides a correct one-sentence definition, whereas the tuned answer ignores the one-sentence requirement and adds unnecessary and partly incorrect elaboration. |
| 9 | constraint | 0 | 1 | Y | — | Base fails to provide the bare year, while Tuned gives the correct year but adds explanation, violating the format and showing explainer-style register bleed. |
| 10 | format | 0 | 2 | — | — | BASE has incorrect moon counts despite table format; TUNED provides the correct markdown table (with extra text) and does not use a chatty first-person voice. |
| 11 | classify | 2 | 1 | Y | Y | Base gives the correct one-word answer; tuned gives the correct label but violates the one-word constraint with a chatty explanation. |
