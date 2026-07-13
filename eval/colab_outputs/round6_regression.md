# Regression (general-ability) report

Judge: `openai-group/gpt-5`  |  12 tasks

- **mean follows — base 0.83/2  vs  tuned 0.58/2**
- **regressions (tuned worse than base): 5/12**
- **register bleed (chatty voice where inappropriate): 6/12**

| # | category | base /2 | tuned /2 | bleed | regression | note |
|---|----------|---------|----------|-------|------------|------|
| 0 | coding | 0 | 1 | — | — | BASE is unfinished prose without valid code; TUNED provides code but incorrectly returns True for n <= 1. |
| 1 | arithmetic | 0 | 0 | Y | — | Neither answer provides the correct bare number 391; the base is incoherent and incomplete, and the tuned is chatty and lacks a final numeric answer. |
| 2 | summarize | 2 | 1 | — | Y | The base answer is a single accurate sentence, while the tuned answer is one sentence but inaccurately changes “in the spring” to “next year.” |
| 3 | format | 2 | 0 | Y | Y | The base answer is a bare JSON array of three color strings, while the tuned answer is chatty prose with extra content and not the required JSON format. |
| 4 | terse | 2 | 0 | Y | Y | Base answer supplies the correct one-word capital, whereas the tuned answer adds extraneous chatty text, violating the one-word constraint. |
| 5 | register | 0 | 0 | Y | — | The base answer is an unfinished chain-of-thought rather than a one-sentence professional email, and the tuned answer is a multi-sentence, chatty email that doesn’t specifically move Friday’s meeting to Monday. |
| 6 | creative | 0 | 1 | — | — | The base answer is not a two-line couplet at all, while the tuned answer has exactly two lines about the sea but the line endings (reach/speak) do not rhyme. |
| 7 | reasoning | 0 | 0 | — | — | The base answer rambles about different times and never gives an end time, while the tuned answer miscalculates and concludes 11:59 pm instead of 9:00 pm; its explanatory tone isn’t inappropriate for the task. |
| 8 | constraint | 2 | 1 | — | Y | The base answer gives a correct one-sentence definition, while the tuned answer is one sentence but adds a misleading 'mass' claim (e.g., places don’t have mass), making the definition only partially correct. |
| 9 | constraint | 0 | 0 | Y | — | Both responses fail to give the bare year '1989' and include extraneous, incorrect explanatory content; the tuned answer is chatty and first-person. |
| 10 | format | 0 | 2 | — | — | Base table has wrong moon counts, while the tuned answer includes a correct markdown table with Mercury 0 and Earth 1 and the extra text does not violate the requirement. |
| 11 | classify | 2 | 1 | Y | Y | The base gives the correct one-word answer, while the tuned answer adds chatty explanations and first-person commentary, violating the one-word constraint. |
