# The Ultimate Guide to Decontaminating AI Prose

**Purpose:** Detect and remove LLM writing artifacts ("AI slop") from any document -- articles, books, reports, emails, marketing copy.
**Applies to:** Text produced or rewritten by ChatGPT, Claude, Gemini, Llama, or any LLM.

---

## What Is AI Slop?

Simon Willison coined "slop" in 2024 as the AI equivalent of spam: **generated content that nobody asked for, nobody reviewed, and nobody wants.** But even intentionally produced, human-reviewed AI text carries fingerprints. This guide catalogues every known tell and provides a systematic method to remove them.

The core insight: **AI writing is detectable through its uniformity, its inflation, its hedging, and its absence of human texture** -- rough edges, strong opinions, specific memories, and imperfect structure.

---

## Part 1: The Word-Level Tells

### 1.1 The Blacklist Words

These words occur 3-25x more frequently in AI-generated text than in human writing (Kobak et al., 2024; Liang et al., 2024). Their presence in non-literal contexts is a strong AI signal.

| Word | AI frequency spike | Human alternative |
|------|-------------------|-------------------|
| delve | 25x (most notorious GPT-ism) | explore, examine, dig into, look at |
| tapestry | ~10x | mix, web, patchwork, or cut entirely |
| vibrant | ~8x | lively, active, specific descriptor |
| landscape | ~7x (in non-literal use) | field, space, world, or name the thing |
| multifaceted | ~6x | complex, layered, or describe the actual facets |
| crucial | ~5x | important, key, or just state why it matters |
| meticulous | 7.4x in peer reviews | careful, precise, thorough |
| commendable | 9.4x in peer reviews | good, strong, solid |
| intricate | 4.5x | detailed, complex, or describe the complexity |
| nuanced | ~4x | subtle, specific, or show the nuance |
| pivotal | ~4x | important, turning-point, or say why |
| noteworthy | ~3x | worth flagging, or just flag it |
| invaluable | ~3x | valuable, essential, or say what value it adds |
| groundbreaking | ~3x | new, first, original, or describe what it broke |
| robust | ~3x | strong, solid, reliable |
| comprehensive | 3x in peer reviews | thorough, complete, full |
| encompasses | ~3x | includes, covers |
| spearhead | ~3x | lead, drive, start |
| paradigm | ~3x | model, approach, shift |
| underscores | ~3x | shows, reveals, highlights |
| foster | ~3x | build, grow, encourage |
| leverage | ~3x (as verb) | use, apply, take advantage of |
| embark | ~3x | start, begin, set out |
| realm | ~3x | area, field, domain |
| testament | ~3x | proof, evidence, sign |
| beacon | ~3x | example, signal, model |
| resonate | ~3x | connect, ring true, land |

**The rule:** If you can replace the word with something simpler and lose nothing, the original was AI filler.

### 1.2 Filler Intensifiers

Words that pad sentences without adding information. LLMs scatter them everywhere; human writers use them once or twice per thousand words.

| Word | What to do |
|------|-----------|
| remarkably | Replace with a specific number or detail |
| notably | Cut, or say "worth flagging:" |
| crucially | Cut, or say "the critical factor:" |
| importantly | Cut entirely -- if it's important, the reader can tell |
| fundamentally | "at root", "structurally", or cut |
| incredibly | Replace with actual measurement |
| essentially | Almost always deletable |
| ultimately | "in the end", "finally", or cut |
| interestingly | Cut -- if it's interesting, the reader will notice |
| arguably | Take a position or cut |
| certainly | Cut -- just assert the thing |
| absolutely | Cut |
| undeniably | Cut -- if you need to say it's undeniable, it's probably deniable |

### 1.3 Transition Words That Signal AI

These transitions are legitimate in moderation. AI uses them 5-10x more than humans:

- **Moreover** -- prefer "also", "and", or restructure
- **Furthermore** -- prefer "beyond that", "and", or just start the next sentence
- **Additionally** -- prefer "also" or cut
- **Indeed** -- cut unless genuinely emphatic
- **That said** / **That being said** -- prefer "but", "however", or restructure
- **In essence** -- cut and state the essence
- **In terms of** -- rephrase: "for X" or "regarding X"
- **When it comes to** -- cut and just name the thing
- **At the end of the day** -- cut
- **At its core** -- cut and state the core

**Density test:** More than 2 of these per page (250 words) = AI fingerprint.

---

## Part 2: The Phrase-Level Tells

### 2.1 Vapid Openers

Sentences that throat-clear before the actual point.

| Opener | Fix |
|--------|-----|
| Here's the thing: | Delete. Start with the thing. |
| Here's where it gets interesting: | Delete. If it's interesting, the reader will notice. |
| Here's what you need to know: | Delete. Just tell them. |
| Let's dive in / Let's dive deeper | Delete. Just dive. |
| Let's unpack this | Delete. Just unpack. |
| Let's be clear / Let's be honest | Delete. Just be clear. Just be honest. |
| It's worth noting that | Delete. If it's worth noting, note it. |
| It's important to note that | Delete. Just note it. |
| It's important to remember that | Delete. Just state the thing. |
| The reality is | Delete. Just state the reality. |
| Picture this: | Delete unless genuinely setting a scene. |
| Imagine a world where... | Delete. Overused and patronizing. |
| Consider for a moment... | Delete. Just present the idea. |

### 2.2 Unearned Profundity

Sentences that reach for gravitas they haven't built.

| Pattern | What's wrong | Fix |
|---------|-------------|-----|
| "This isn't just X -- it's Y" | Implies insight, delivers restatement | State Y directly |
| "X is more than just Y" | Same problem | Say what X actually is |
| "The implications are profound" | Vague grandeur | Name the specific implications |
| "This changes everything" | Almost never true | Say what specifically changes |
| "This raises important questions" | Stalling | Ask the actual questions |
| "The stakes couldn't be higher" | Inflation | State the actual stakes |
| "As we stand on the brink of..." | Melodrama | Name what's happening |
| "Only time will tell" | The laziest possible ending | Make a prediction or state what you don't know |
| "X is a game-changer" | Meaningless hype | Say what changed and how |
| "X sits at the intersection of Y and Z" | AI's favorite spatial metaphor | Say how X combines Y and Z |
| "Navigate the complexities of..." | Vague action | Name the specific challenges |

### 2.3 The Parallelism Tic

The construction **"It's not X, it's Y"** (and its variants). Used once, it's rhetoric. Used ten times in one document, it's a fingerprint.

Variants:
- "It's not X -- it's Y"
- "It's not X; it's Y"
- "This isn't about X, it's about Y"
- "The point isn't X"
- "The question isn't whether X"

**Fix:** Keep 1-2 per document max. For the rest, vary:

| Instead of | Try |
|------------|-----|
| It's not X, it's Y | Less X than Y |
| It's not X -- it's Y | Y, not X (inversion) |
| This isn't about X | X gives way to Y |
| The point isn't X | Where once X, now Y |
| | Just state Y directly without the antithesis |

### 2.4 Sycophantic and Self-Narrating Phrases

Mostly in chat/conversational output, but they leak into documents:

- "Great question!"
- "That's a really interesting point"
- "I'd be happy to help with that"
- "Let me walk you through this"
- "Here's a comprehensive breakdown"
- "I want to be straightforward about..."
- "There's a lot to unpack here"

**Fix:** Delete all of these. Just do the thing.

### 2.5 The Universal Applicability Claim

AI rarely says "this doesn't apply to your situation." Instead:

- "Whether you're a beginner or an expert..."
- "No matter your industry..."
- "For individuals and organizations alike..."

**Fix:** Be specific about who this is for. Excluding audiences builds credibility.

---

## Part 3: The Structural Tells

### 3.1 The Listicle Compulsion

AI defaults to numbered lists and bullet points even when prose would be more natural. A human writer might use 1-2 lists in an article; AI structures the entire piece as nested lists.

**Fix:** Convert at least half of your lists back to prose paragraphs. Lists are for reference material; arguments belong in sentences.

### 3.2 The Five-Paragraph Essay

AI strongly defaults to: intro with thesis, point 1, point 2, point 3, conclusion restating intro. Every section has the same number of sub-points, every bullet is roughly the same length, every paragraph has a similar word count.

**Fix:** Vary section lengths. Some points deserve three paragraphs; others need one sentence. Asymmetry is a sign of human judgment.

### 3.3 The "Heading + Summary + Bullets" Pattern

Almost every AI section follows:
```
## [Heading]
[One paragraph introducing the topic]
- [Point 1]
- [Point 2]
- [Point 3]
[Optional transition sentence]
```

**Fix:** Break the template. Start some sections with a question. Start others with a specific example. Let some sections have no substructure at all.

### 3.4 The Conclusion That Restates the Introduction

AI almost always ends by paraphrasing its opening paragraph. Human writers end with a new insight, a question, a call to action, or an unexpected turn.

**Fix:** Delete conclusions that merely summarize. End with something the reader didn't know at the start.

### 3.5 Excessive Signposting

AI over-narrates its own structure: "First, we'll look at... Then, we'll explore... Finally, we'll consider..." This is the writing equivalent of saying "I'm about to tell a joke" before telling the joke.

**Fix:** Cut structural narration. If the structure is clear, you don't need to announce it.

### 3.6 Cross-Reference Over-Explanation

Re-defining terms every time they appear: "the Foundation -- the universal baseline we described earlier -- provides..." A human author trusts the reader to remember; an LLM hedges.

**Fix:** First mention in a section gets a brief reminder. After that, trust the reader.

---

## Part 4: The Formatting Tells

### 4.1 Italic Function Words -- The Most Diagnostic Pattern

No human writer italicizes *and*, *is*, *that*, *with*, *for*, *it*, *was*, *but*, or *or*. LLMs do it constantly because they mimic emphasis patterns without understanding which words carry semantic weight.

**Function words to never italicize** (remove emphasis on sight):
> and, is, that, with, for, it, was, has, but, or, be, do, than, this, are, were, can, all, so, just, very, too, also, even, if, as, how, what, when, the, a, an, of, in, to, on, at, by, up, out, no, not

**This is arguably the single most reliable AI detector.** If a document italicizes function words more than once, it was AI-assisted.

### 4.2 Bold Overuse

AI **bolds key terms** extensively. Human writers use bold sparingly -- for definitions, warnings, or truly critical emphasis.

**Fix:** Remove bold except for:
- Coined terms at first use
- UI elements or technical identifiers
- Genuine warnings or critical notes

If more than 5% of your text is bold, strip most of it.

### 4.3 Em Dash Overuse

LLMs love em dashes -- they use them constantly -- sometimes three or four per paragraph -- creating a breathless, parenthetical style that real editors flag immediately.

**Fix:** Limit to 1-2 per page. Replace with commas, parentheses, periods, or restructured sentences.

### 4.4 Emoji Tells

AI (especially ChatGPT) places emojis in predictable patterns:
- One emoji per section header
- Evenly distributed throughout
- Favorite choices: rocket, lightbulb, checkmark, star, fire, pointing finger

**Fix:** Remove decorative emojis. If you must use them, cluster them naturally rather than distributing them evenly.

### 4.5 Triadic Lists

Groups of three, everywhere: "resilience, creativity, and purpose." Humans write triads too, but LLMs default to them so reliably that density becomes diagnostic.

**Fix:** Vary list length. Use pairs, singles, and groups of four or five. If every list has exactly three items, break the pattern.

---

## Part 5: The Voice-Level Tells

### 5.1 Emotional Flatness

Despite using charged words (vibrant, passionate, transformative), AI writing feels emotionally flat. There's no genuine anger, humor, sarcasm, confusion, or vulnerability. It's uniformly positive-neutral.

**Test:** Read a paragraph aloud. Can you hear a human voice with a mood, an attitude, a personality? Or does it sound like a corporate FAQ?

### 5.2 No Intellectual Courage

AI rarely makes bold claims, takes unpopular positions, or expresses genuine disagreement. Everything is balanced, measured, safe. Real writers have opinions.

**Test:** Does the text ever say something that might make someone disagree? If not, it's playing it safe.

### 5.3 Uniform Register

Human writers shift registers -- formal in one paragraph, colloquial in the next, technical when needed. AI maintains a consistent "educated professional" register throughout.

**Test:** Does the writing ever get casual? Blunt? Funny? Technical? If the register never shifts, it's AI.

### 5.4 Avoided Contractions

LLMs tend toward formal register: "it is" instead of "it's", "do not" instead of "don't." In narrative prose, this creates a stiff, robotic cadence.

**Fix:** Use contractions in narrative and conversational prose. Reserve formal register for technical exposition.

### 5.5 No Negative Space

AI fills every possible angle. Human writers know what to leave out. The absence of content is as important as its presence. AI doesn't know what to omit.

**Test:** Could you cut 30% of the text without losing the argument? If yes, the filler is probably AI padding.

### 5.6 Lack of Specificity

AI uses generic examples and avoids lived details. A human might write "I spilled coffee on my keyboard at 3am debugging this." AI writes "developers often face challenges in their workflow."

**Test:** Are there concrete details that couldn't come from training data? Dates, names, personal anecdotes, specific numbers?

### 5.7 Semantic Satiation Through Synonyms

AI often restates the same idea using different words in consecutive sentences, creating an illusion of depth through synonym rotation rather than adding new information.

**Test:** After each sentence, ask: "Did I learn something new here, or was this a restatement?" If three sentences in a row say the same thing with different words, collapse them into one.

---

## Part 6: Model-Specific Tells

### ChatGPT (GPT-4/4o)
- Heavy on "delve", "tapestry", "vibrant", "landscape"
- Confident, assertive tone -- rarely hedges
- "Certainly!", "Absolutely!" as openers
- More emoji usage
- Ends with encouraging calls to action
- The "[Topic]. Here's why:" headline pattern
- Tends toward grandiose, inflated prose

### Claude
- More hedging and epistemic humility ("I think", "it seems")
- "I'd be happy to help", "That's a great question"
- Heavy em-dash usage
- "That said," as transition
- "Genuinely", "straightforward", "thoughtful"
- Volunteers ethical caveats unprompted
- More discursive paragraphs, less listicle-heavy
- Meta-commentary: "This is a complex topic, but..."

### Gemini
- More verbose than either GPT or Claude
- Heavy on "It's important to remember that..."
- Produces "Key takeaways" sections unprompted
- More likely to cite sources (sometimes hallucinated)

### Open-Source Models (Llama, Mistral, etc.)
- More repetitive within paragraphs
- Weaker transition management
- More likely to produce circular arguments
- Less polished formatting

---

## Part 7: Detection Methodology

### Quick Scan (5 minutes)

Run these five tests on any document:

1. **The Delve Test:** Ctrl+F for: delve, tapestry, vibrant, landscape, multifaceted, crucial, meticulous, foster, leverage, robust. More than 2 hits in a short document = AI.

2. **The Italic Function Word Test:** Search for single-word italics. If *and*, *is*, *that*, *for*, *it*, or *but* are italicized, it's AI.

3. **The Opener Test:** Search for: "Here's the", "Let's dive", "It's worth noting", "Picture this", "Imagine a world". Any hits = AI.

4. **The Transition Density Test:** Count "Moreover", "Furthermore", "Additionally", "Indeed", "That said." More than 2 per page = AI.

5. **The Structure Test:** Are all sections the same length? Do all lists have 3 items? Does the conclusion restate the intro? If yes to all three = AI.

### Full Audit (30-60 minutes)

For book-length or high-stakes documents, run systematic searches:

**Pass 1 -- Word-level:** Search for every word in sections 1.1, 1.2, and 1.3. Record counts and locations.

**Pass 2 -- Phrase-level:** Search for patterns in sections 2.1 through 2.5. Record counts.

**Pass 3 -- Formatting:** Search for italic single-word patterns, bold patterns, em-dash density.

**Pass 4 -- Structure:** Map section lengths, list item counts, and conclusion types.

**Pass 5 -- Voice:** Read 5 random paragraphs aloud. Apply the tests from Part 5.

### Automated Detection Script

For each pattern, use regex searches across your document:

```bash
# Blacklist words (case-insensitive)
grep -icE '\b(delve|tapestry|vibrant|landscape|multifaceted|crucial|meticulous|intricate|pivotal|commendable|robust|comprehensive|encompasses|spearhead|paradigm|underscores|foster|leverage|embark|realm|testament|beacon|resonate)\b' document.md

# Filler intensifiers
grep -icE '\b(remarkably|notably|crucially|importantly|fundamentally|incredibly|essentially|ultimately|interestingly|arguably|certainly|absolutely|undeniably)\b' document.md

# AI transitions
grep -icE '\b(Moreover|Furthermore|Additionally|Indeed)\b' document.md

# Vapid openers
grep -icE "(Here's the thing|Here's where|Here's what|Let's dive|Let's unpack|Let's be clear|Let's be honest|It's worth noting|It's important to note|Picture this|Imagine a world)" document.md

# Unearned profundity
grep -icE "(This isn't just|more than just|changes everything|implications are profound|stakes couldn't be higher|game.changer|at the intersection of|navigate the complexities)" document.md

# Em dash density
grep -c '—' document.md

# Italic function words (Markdown)
grep -cE '\*\b(and|is|that|with|for|it|was|has|but|or|be|do|than|this|are|were|can|all|so|just|very|too|also|even|if|as|the|a|an|of|in|to)\b\*' document.md
```

---

## Part 8: The Fix Methodology

### Tier 1: Mechanical Fixes (No Judgment Required)

These can be fixed by search-and-replace or automated scripts:

| Pattern | Fix |
|---------|-----|
| Italic function words | Remove italics |
| "It's worth noting that..." | Delete the phrase |
| "Here's the thing:" | Delete |
| "Let's dive in" | Delete |
| Filler intensifiers with no specific content | Delete or replace with specific detail |
| "Certainly", "Absolutely" as openers | Delete |
| Decorative emojis | Delete |

### Tier 2: Judgment Fixes

These require reading context and choosing the best alternative:

| Pattern | Approach |
|---------|----------|
| "Not X, it's Y" parallelism | Keep 1-2 per document, vary the rest |
| Blacklist words | Replace with specific alternatives that fit the context |
| Triadic lists | Vary list lengths; break some into prose |
| Em dash overuse | Replace most with commas, periods, or parentheses |
| Bold overuse | Keep only for coined terms and genuine emphasis |
| Avoided contractions | Add contractions in narrative prose |
| Cross-reference over-explanation | Trust the reader after first mention |

### Tier 3: Rewrite Required

These can't be fixed with word-level edits -- they require rewriting passages:

| Pattern | Approach |
|---------|----------|
| Unearned profundity | Replace grandiose claim with specific evidence |
| Emotional flatness | Add genuine voice: an opinion, a joke, an admission |
| Lack of specificity | Add concrete examples, numbers, names, dates |
| Symmetric structure | Vary section lengths and formats |
| Conclusion that restates intro | Write a new ending that advances the argument |
| Semantic satiation | Collapse synonym-rotated sentences into one |
| Universal applicability claims | Name the specific audience |

### Tier 4: Leave Alone

Not every pattern is slop. Keep:

- **Triads that list three actual things** (not filler groupings)
- **Specific, surprising analogies** ("hit the market like a truck" has personality; "like a tapestry" does not)
- **Bold on coined terms** at first use
- **One or two "not X, it's Y" constructions** per long document -- it's legitimate rhetoric in moderation
- **Formal register** in genuinely technical passages

---

## Part 9: Prevention (Writing Prompts That Reduce Slop)

The best cleanup is prevention. When prompting an LLM to write:

### Effective prompt additions:

```
- Write in a direct, conversational tone. Use contractions.
- No filler words: cut "remarkably", "notably", "crucially", "importantly."
- No throat-clearing openers: don't start sentences with "It's worth noting" or "Here's the thing."
- No "not X, it's Y" constructions.
- No em dashes.
- No triadic lists unless listing exactly three things.
- Use specific examples with real numbers, names, and dates.
- Take a clear position. Don't hedge with "on one hand / on the other hand."
- Vary paragraph and section lengths. Not everything needs three sub-points.
- Don't italicize function words (and, is, that, for, it, but, or, with).
- Don't use: delve, tapestry, vibrant, landscape, multifaceted, crucial,
  foster, leverage, robust, comprehensive, embark, realm, beacon, paradigm.
- Don't end by restating the introduction.
```

### The "Write Like a Human" Checklist

Before publishing any AI-assisted text, verify:

- [ ] Would a specific human being actually write this sentence?
- [ ] Does this paragraph add new information, or restate the previous one?
- [ ] Is there at least one opinion, joke, or specific detail per page?
- [ ] Does the register shift at least once (formal to casual or vice versa)?
- [ ] Is the conclusion different from the introduction?
- [ ] Could I cut 20% without losing the argument? (If yes, cut it.)
- [ ] Are there any words I wouldn't use in conversation?
- [ ] Does every list have a reason to be a list instead of prose?

---

## Part 10: Decision Framework

When reviewing a flagged pattern, apply this tree:

```
Is this pattern used fewer than 3 times in the full document?
  YES → Probably fine. Leave it.
  NO  → Continue...

Does removing/changing it alter the author's meaning?
  YES → Leave it. Flag for human review.
  NO  → Continue...

Is this a proper noun, coined term, or intentional style choice?
  YES → Leave it.
  NO  → Continue...

Is this a function word with italic/bold emphasis?
  YES → Remove emphasis. No human writer does this.
  NO  → Continue...

Is this a filler word that can be cut without losing meaning?
  YES → Cut it.
  NO  → Continue...

Is this a structural pattern (triadic list, symmetric sections)?
  YES → Vary it. Break the template.
  NO  → Rewrite the passage with specificity and voice.
```

---

## Appendix A: French-Language AI Slop

French has its own distinct set of AI tells that don't map 1:1 to English. This appendix covers everything specific to detecting and cleaning AI-generated French text.

### A.1 The French Blacklist Words

| French | English equivalent | Human alternative |
|--------|-------------------|-------------------|
| crucial | crucial (THE most notorious French GPT-ism) | important, central, determinant |
| essentiel | essential | important, necessaire, utile |
| fondamental | fundamental | de base, structurel, premier |
| captivant | captivating | interessant, frappant, marquant |
| fascinant | fascinating | interessant, etonnant, surprenant |
| passionnant | thrilling/exciting | interessant, stimulant |
| troublant | troubling | inquietant, preoccupant, deroutant |
| transformateur | transformative | nouveau, different, qui change |
| revolutionnaire | revolutionary | nouveau, inedit, sans precedent |
| indispensable | indispensable | necessaire, utile, important |
| vibrant | vibrant (English carryover) | vivant, anime, dynamique |
| robuste | robust (English calque) | solide, fiable, resistant |
| holistique | holistic (English calque) | global, d'ensemble, complet |
| inlassablement | tirelessly (350x overuse) | sans relache, avec perseverance |
| entrelacer | intertwine (350x overuse) | meler, croiser, combiner |

### A.2 Overused French Verbs and Verb Phrases

The single most overused French AI construction is **"permettre de"** (to allow/enable). AI uses it where a direct verb would be more natural.

| AI writes | Human writes |
|-----------|-------------|
| Cela permet de reduire les couts | Cela reduit les couts |
| Ce systeme permet d'ameliorer | Ce systeme ameliore |
| Cette approche permet de comprendre | Cette approche eclaire / On comprend mieux avec |

Other overused verb constructions:

| Verb phrase | Human alternative |
|-------------|-------------------|
| mettre en oeuvre | faire, realiser, appliquer |
| mettre en place | creer, installer, lancer |
| naviguer dans | traverser, gerer, comprendre |
| ouvrir la voie a | preparer, faciliter |
| tisser des liens | creer des contacts, se rapprocher |
| jeter les bases de | commencer, fonder, preparer |
| franchir un cap | progresser, avancer, depasser |

### A.3 French Vapid Openers and Closers

**Openers to delete on sight:**

| French opener | Equivalent English tell |
|---------------|------------------------|
| Dans un monde en constante evolution... | In today's fast-paced world... |
| Dans le paysage actuel de... | In the current landscape of... |
| A l'ere de... | In the era of... |
| A l'heure ou... | At a time when... |
| Force est de constater... | One must acknowledge... |
| Il est essentiel de noter que... | It is essential to note that... |
| Il est important de noter que... | It is important to note that... |
| Il est crucial de comprendre... | It is crucial to understand... |
| Il convient de souligner... | It should be emphasized... |
| Explorons cette problematique... | Let's explore this issue... |
| Plongeons dans les details... | Let's dive into the details... |

**Fix:** Same as English -- delete the opener and start with the actual point.

**Closers to cut or rewrite:**

| Closer | Fix |
|--------|-----|
| En conclusion | Delete -- if it's the last paragraph, the reader knows |
| En resume | Delete |
| En somme | Delete |
| En definitive | Delete |
| Pour finir | Delete |
| Comme nous l'avons vu | Delete -- don't narrate what the reader just read |

### A.4 French Transition Words AI Overuses

| Transition | Frequency in AI vs human | Alternative |
|------------|-------------------------|-------------|
| En outre | 5-8x overused | aussi, et, par ailleurs (sparingly) |
| Par ailleurs | GPT-4's reported favorite | de plus, d'autre part, et |
| De plus | 5x overused | aussi, et |
| De surcroit | 4x overused | en plus, et |
| En effet | 4x overused | (often deletable -- just state the fact) |
| Neanmoins | 3x overused | mais, pourtant |
| Par consequent | 3x overused | donc, du coup |
| Dans cette optique | 3x overused | pour cela, dans ce but |
| A cet egard | 3x overused | sur ce point, la-dessus |
| Cela etant dit | 3x overused | mais, cependant |
| Dorenavant | unnecessarily formal | desormais, maintenant |
| En d'autres termes | signals restatement, not progress | (delete and state it once) |

**Density test:** More than 3 of these per 250-word page = AI fingerprint. Natural French relies more on sentence flow and implicit logic than on explicit connectors.

### A.5 The "Langue de Bois" Problem

The most distinctive French AI tell is **register**. AI writes French in a pompous, administrative, pseudo-academic style the French call "langue de bois" (wooden language) -- the bureaucratic, evasive, empty style of politicians and corporate communications.

**Symptoms:**

1. **Excessive impersonal "il" constructions:** "Il est important de...", "Il convient de...", "Il est essentiel de..." -- these avoid taking a position. Human writers say "je pense" or "on sait" or just assert directly.

2. **"Nous" where "on" is natural:** In spoken and casual written French, "on" is far more common than "nous" for first-person plural. AI defaults to formal "nous." If every "we" in your text is "nous," it reads like a government report.

3. **No colloquialisms:** AI French has no personality -- no argot, no regional flavor, no generation-specific language. It reads like a textbook written for no one in particular.

4. **Stacked subordinate clauses:** "Il convient de noter que, dans une certaine mesure, cette decision pourrait potentiellement impacter les parties prenantes concernees" -- a sentence that says nothing while sounding important. Human French is more direct.

### A.6 French Typography Tells

These are formatting artifacts specific to French that reveal AI authorship:

| Tell | What's wrong | Correct French |
|------|-------------|----------------|
| Em dash (tiret cadratin) overuse | ChatGPT's single most famous French tell, acknowledged by OpenAI. French uses em dashes far less than English. | Prefer commas, parentheses, or restructured sentences |
| "texte" or "texte" | English-style quotation marks | French uses guillemets: << texte >> |
| Missing thin spaces | No space before : ; ! ? | French requires a thin non-breaking space before these |
| Straight apostrophes (') | English-trained model artifact | Use typographic apostrophes (') |
| Title Case Sur Chaque Mot | English capitalization style | French capitalizes only the first word: "Titre de l'article" |
| Comma before "et" | Oxford comma (English convention) | French does NOT use a comma before "et" |

### A.7 Anglicisms AI Introduces

Research shows 16% of ChatGPT's French errors have English origins. Watch for:

| AI writes (anglicism) | Correct French |
|-----------------------|----------------|
| Faire du sens | Avoir du sens |
| Adresser un probleme | Traiter / resoudre un probleme |
| Impacter (overused) | Avoir un impact sur, affecter, toucher |
| Realiser (meaning "understand") | Se rendre compte, comprendre |
| Supporter (meaning "support") | Soutenir, appuyer |
| Definitivement (meaning "definitely") | Assurement, certainement, sans aucun doute |
| Eventuel (used as "eventual") | Eventuel means "possible" in French; for "eventual" use "final" or "a terme" |

### A.8 French Recycled Metaphors

The French equivalents of "like a tapestry":

| Metaphor | Why it's a tell |
|----------|----------------|
| Le paysage de... (the landscape of) | Non-literal "landscape" -- same problem as English |
| Au coeur de... (at the heart of) | AI's go-to locator phrase |
| La pierre angulaire de... (the cornerstone of) | Generic importance marker |
| Un ecosysteme de... (an ecosystem of) | For any group of things |
| Un levier puissant (a powerful lever) | For any tool or method |
| Le fil conducteur (the common thread) | For any recurring theme |
| Un equilibre delicat (a delicate balance) | For any tradeoff |
| La face cachee de... (the hidden face of) | For any downside |
| A double tranchant (double-edged) | For any tradeoff (variant) |
| La pointe de l'iceberg (tip of the iceberg) | For any partial revelation |

### A.9 The "Non seulement X, mais Y" Problem

The French equivalent of "It's not X, it's Y" is **"Non seulement X, mais aussi/egalement Y"** (Not only X, but also Y). ChatGPT uses this construction obsessively in French. Same fix as English: keep 1-2 per document, vary the rest.

### A.10 Quantitative Detection Metrics

These measurements distinguish AI French from human French:

| Metric | AI range | Human range |
|--------|----------|-------------|
| "Notamment" frequency | 1 per 200 words | 1 per 800 words |
| Adverbs ending in "-ment" | 4-6% of words | 1-3% of words |
| Average sentence length | 18-22 words (low variance) | 12-25 words (high variance) |
| Paragraph length variance | +/-20% | +/-50% or more |
| Interrogative sentences | 2-5% | 5-15% |
| Type-Token Ratio (vocabulary diversity) | 0.65-0.75 | 0.50-0.65 |

The **"notamment" test** is the single most reliable quantitative test for French AI text. Count occurrences and divide by word count. If the ratio exceeds 1:400, the text is likely AI-assisted.

### A.11 French Prompt Additions for Prevention

Add these to your prompt when generating French text:

```
- Ecris dans un ton direct et conversationnel. Utilise "on" plutot que "nous."
- Pas de mots-remplissage : supprime "crucial", "essentiel", "fondamental", 
  "fascinant", "passionnant."
- Pas d'ouvertures creuses : ne commence pas par "Dans un monde en constante 
  evolution", "Il est important de noter", "Force est de constater."
- Pas de "non seulement X, mais aussi Y."
- Pas de tirets cadratins (em dashes).
- Utilise les guillemets francais (<< >>) et les espaces fines avant : ; ! ?
- Pas d'anglicismes : "avoir du sens" (pas "faire du sens"), "traiter un 
  probleme" (pas "adresser"), "soutenir" (pas "supporter").
- Varie la longueur des paragraphes et des phrases. Pas de symetrie.
- Utilise "permettre de" au maximum 2 fois. Prefere le verbe direct.
- Pas de conclusion qui repete l'introduction.
- N'utilise pas : paysage (sens figure), pierre angulaire, ecosysteme (sens 
  figure), levier puissant, fil conducteur, equilibre delicat.
- Titre : majuscule uniquement au premier mot.
```

### A.12 French Detection Script

```bash
# Blacklist words
grep -icE '\b(crucial|essentiel|fondamental|captivant|fascinant|passionnant|troublant|transformateur|revolutionnaire|indispensable|vibrant|robuste|holistique|inlassablement)\b' document.md

# Vapid openers
grep -icE "(Dans un monde en constante|Dans le paysage|A l'ere de|Force est de constater|Il est essentiel de|Il est important de noter|Il est crucial|Il convient de|Explorons cette|Plongeons dans)" document.md

# Overused transitions
grep -icE '\b(En outre|Par ailleurs|De plus|De surcroit|Neanmoins|Par consequent|Dorenavant|Cela etant dit|Dans cette optique|A cet egard)\b' document.md

# "Permettre de" density
grep -ic 'permet\(tre\)\? de' document.md

# "Notamment" frequency test
echo "Notably count vs word count:"
grep -ic 'notamment' document.md
wc -w document.md

# Anglicisms
grep -icE "(faire du sens|adresser (un |le |ce )?probl|impacter|definitivement)" document.md

# Em dash density
grep -c '—' document.md

# English-style quotes in French text
grep -cE '["""]' document.md
```

### A.13 Summary: English vs French AI Tells

| Category | English tell | French equivalent |
|----------|-------------|-------------------|
| Most notorious word | "delve" | "crucial" |
| Most overused verb | "leverage" | "permettre de" |
| Vapid opener | "In today's fast-paced world" | "Dans un monde en constante evolution" |
| Favorite transition | "Moreover" / "Furthermore" | "Par ailleurs" / "En outre" |
| Hedging phrase | "It's worth noting that" | "Il est important de noter que" |
| Register problem | Corporate-speak | Langue de bois |
| Typography tell | Em dash overuse | Em dashes + English quotes + missing thin spaces |
| Parallelism tic | "It's not X, it's Y" | "Non seulement X, mais aussi Y" |
| Pronoun tell | N/A | "Nous" where "on" is natural |
| Quantitative test | N/A | "Notamment" frequency (1/200 vs 1/800) |
| Anglicism tell | N/A | "Faire du sens", "adresser un probleme" |

---

## References

- **Kobak et al. (2024)** -- "Delve into ChatGPT usage in scientific writing: monitoring excess word usage in academic papers." Documented 25x spike in "delve" and other LLM-signature words in academic publications post-ChatGPT.
- **Liang et al. (2024)** -- "Monitoring AI-Modified Content at Scale: A Case Study on the Impact of ChatGPT on AI Conference Peer Reviews." Found 10-17% of ICLR/NeurIPS reviews showed substantial LLM modification. Identified "commendable" (9.4x), "meticulous" (7.4x), "intricate" (4.5x) as top markers.
- **Gao et al. (2024)** -- Frequency analysis of scientific abstracts showing statistically significant increases in "realm", "intricate", "pivotal" post-2023.
- **Simon Willison (2024)** -- "Slop is the new spam." Coined/popularized the term for unwanted AI-generated content.
- **Dan Shipper** -- "The Field Guide to AI Slop" ([ignorance.ai](https://www.ignorance.ai/p/the-field-guide-to-ai-slop)). The original catalogue of LLM prose fingerprints: filler intensifiers, vapid openers, unearned profundity, parallelism tics, triadic lists, em dash overuse, generic analogies, bold/italic abuse, avoided contractions.

### French-specific sources
- **Daria Decrypte l'IA** -- "Les tics de langage de ChatGPT." Detailed analysis of ChatGPT's French verbal tics.
- **Generation IA / Flint Media** -- "Comment dejouer les tics de langage de ChatGPT." Practical guide to avoiding French AI patterns.
- **Projet Voltaire** -- "Comment detecter un texte produit par ChatGPT." Linguistic analysis from France's leading language-quality platform.
- **Cours NDRC (2026)** -- "Comment Detecter l'Ecriture IA: 15 Signes a Reconnaitre." Quantitative metrics for French AI detection (TTR, adverb density, sentence variance).
- **Siecle Digital / Fnac L'Eclaireur / CCFI** -- Multiple articles on the tiret cadratin (em dash) as ChatGPT's most recognizable French tell.
- **Journal du Net** -- "Si votre collegue emploie cette expression." Top 5 most overused ChatGPT French phrases.
- **Shaib et al. (arXiv, 2509.19163)** -- "Measuring AI Slop in Text." Cross-language frequency analysis of AI-overused terms.