# Regression (general-ability) report

Judge: `openai-group/gpt-5`  |  12 tasks

- **mean follows — base 1.42/2  vs  tuned 0.75/2**
- **regressions (tuned worse than base): 7/12**
- **register bleed (chatty voice where inappropriate): 7/12**

| # | category | base /2 | tuned /2 | bleed | regression | note |
|---|----------|---------|----------|-------|------------|------|
| 0 | coding | 0 | 0 | Y | — | Base answer contains multiple syntax/logic errors and no final valid function; tuned answer is chatty and its code is incorrect (missing imports, wrong edge-case handling, and syntax mistakes), so neither meets the criterion of a correct Python primality function without prose. |
| 1 | arithmetic | 0 | 0 | Y | — | Both answers are incorrect (should be 391), and the tuned response also adds chatty explanation instead of just giving a number. |
| 2 | summarize | 2 | 1 | — | Y | The base answer is a single accurate sentence including the 6–3 vote and spring start, while the tuned answer is one sentence but omits the vote and start date and adds an unstated 'heated' detail. |
| 3 | format | 2 | 2 | — | — | Both answers provide a bare valid JSON array of three primary colors with no extra text. |
| 4 | terse | 1 | 1 | Y | — | Both answers provide 'Tokyo' but do not comply with the single-word format; the tuned answer also adds unnecessary explanatory text, indicating register bleed. |
| 5 | register | 2 | 1 | Y | Y | The base response is a concise, professional one-sentence request, whereas the tuned response is multi-sentence and chatty, violating the one-sentence formal email constraint. |
| 6 | creative | 2 | 1 | — | Y | The base has exactly two lines that rhyme (night/light), while the tuned answer has two lines about the sea but the endings (shore/returns) do not rhyme. |
| 7 | reasoning | 0 | 0 | — | — | The base answer is confused and gives no correct end time, and the tuned answer computes wrongly and concludes 1:19 am instead of 9:00 pm. |
| 8 | constraint | 2 | 0 | Y | Y | The base answer provides a correct single-sentence definition, whereas the tuned answer uses multiple sentences with example-based, tutorial tone, violating the exact one-sentence requirement. |
| 9 | constraint | 2 | 1 | Y | Y | The base answer exactly gives '1989' with no extras, while the tuned answer includes the correct year but adds explanatory text in a chatty tone, violating the required bare-answer format. |
| 10 | format | 2 | 1 | — | Y | The base answer correctly provides a markdown table with Mercury 0 and Earth 1, while the tuned answer is a markdown table but leaves Mercury’s moon count blank; neither includes chatty text. |
| 11 | classify | 2 | 1 | Y | Y | Base gives the correct one-word 'negative', while the tuned answer adds explanatory text beyond the required single word, showing a chatty register. |
