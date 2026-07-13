# Accuracy + information-loss report

Judge: `openai-group/gpt-5`  |  16 answers

- **mean accuracy: 4.56/5**
- **mean info retention: 65.3%**  (info loss 34.7%)
- **answers with >=1 factual error: 3/16**
- **confident fabrications: 1 across 1/16 answers**

| # | prompt | acc /5 | retain % | fab | errors |
|---|--------|--------|----------|-----|--------|
| 0 | Why does the ocean look blue? | 5 | 100 | 0 | — |
| 1 | Can you explain how vaccines work? | 5 | 55 | 0 | — |
| 2 | What causes the seasons to change? | 5 | 50 | 0 | — |
| 3 | Explain what compound interest is and  | 4 | 10 | 0 | — |
| 4 | Why do we get hiccups? | 2 | 50 | 0 | States the burst of air through the trachea creates the hic sound; the sound is primarily due to sudden closure of the vocal cords (glottis).; Implies the vagus nerve controls the diaphragm; the phrenic nerve innervates the diaphragm, whereas the vagus does not control it. |
| 5 | How does the internet send a message f | 5 | 10 | 0 | — |
| 6 | Why does bread rise when you bake it? | 5 | 20 | 0 | — |
| 7 | What is the difference between weather | 5 | 90 | 0 | — |
| 8 | How do noise-cancelling headphones wor | 4 | 85 | 0 | — |
| 9 | Why does metal feel colder than wood a | 5 | 100 | 0 | — |
| 10 | Can you explain what a black hole is w | 5 | 100 | 0 | — |
| 11 | Why do onions make you cry when you cu | 4 | 100 | 1 | Misspells the irritant as "syn-Propanethiole S-oxide"; the correct name is syn-propanethial-S-oxide.; Calls the compound odorless; syn-propanethial-S-oxide is not strictly odorless and has an onion-like odor.; Refers to "tiny droplets of this gas"; gases/vapors diffuse as molecules rather than droplets. |
| 12 | My textbook says humans only use 10% o | 5 | 100 | 0 | — |
| 13 | A friend told me lightning never strik | 4 | 90 | 0 | Overgeneralizes that regions near large bodies of water are more likely to have repeated strikes; lightning frequency is generally higher over land than over open water and depends on local convective patterns. |
| 14 | Here's the opening of my college essay | 5 | 80 | 0 | — |
| 15 | Make the case that public libraries ar | 5 | 5 | 0 | — |
