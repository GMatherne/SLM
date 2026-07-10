<!-- Vendored from the write-humanlike-2 skill. This is the DEEP guidance for the
teacher model. It changes rarely. Tune persona.md and task.md first; only edit
this when the skill itself improves. -->

# Human Prose

## Why surface fixes aren't enough

Modern AI-text detectors don't score a checklist of tells. Pangram, the reference point here, is a transformer trained with hard-negative mining and synthetic mirrors: for every human document it generates an AI document matched on topic, length, and style, then trains the model to separate the two on whatever's left. That residual is the target.

1. The visible "tells" are not the detector's inputs. Scrubbing em dashes, markdown, and triads does not move the real classifier. What moves it runs deeper: rhythm that barely varies, word choices that stay predictable, grammar that never bends the way real people bend it, and prose so generic it could have come from anyone.
2. Mechanical humanization is itself a learned signal. Do not apply the rules below as an even sprinkle. Apply them as a single, consistent voice.
3. There is no permanent recipe. The levers that keep working are the ones that can't be faked cheaply: specifics that come from actually knowing the subject, and a voice with a real person underneath it.

## Write it, don't launder it

Everything below is a net. The actual plan is simpler: write as a real person from the first word, so there's nothing to catch.

Laundering happens after the fact: write the normal AI draft, then go back through it pulling em dashes and swapping "delve" for something plainer. What actually gives a draft away sits under the words and doesn't budge when you change them: the order the ideas come in, how evenly every claim gets padded with a hedge, the reflex to set up context first and land on a tidy note at the end. That's the layer the detector reads. Vocabulary barely registers. So the humanizer tools scrub the top, and the draft underneath still scores as AI.

Don't compose and then fix. Decide who's writing and what situation they're in, and stay in that person the whole way through. When a draft still reads generic, another cleanup pass won't save it. The generic is coming from the voice, so go back and commit harder to the person.

## Write as a specific person in a specific situation

A real person makes different structural and word-level choices, and those carry the signal. Never fall back on the neutral "helpful assistant" voice. Register is the frame, not the disguise: picking an unusual subject or dialing formality does not move the score; committing to a real person does.

## Vary rhythm and length

AI prose settles into a uniform, mid-length cadence with low variance. Human writing is uneven: mix long, winding sentences with short ones, and don't let any single length dominate. Do not turn this into a predictable long-short-long-short pattern; that is just a different machine pattern. Aim for genuine irregularity in the spread of sentence lengths.

## Don't over-tighten into density

Cutting filler is right, up to a point. AI prose is dense: it packs in content words and drops the small connective ones, so every sentence runs at full load. Human writing breathes. It carries more low-content glue (the, of, it, just, kind of, the "that" you could delete), the throwaway aside, the half-sentence that doesn't earn its place. So the cuts further down have a floor. Strip the padding, sure, but if you compress every sentence into a tight nugget you've swapped one machine tell for another. Leave some slack.

## Say it once, don't rotate synonyms

Common AI move: say something, then say it again in the next sentence with the words swapped around, as if the second pass added information. It just pads. Say it once and move on. This isn't a ban on synonyms, though. Reaching for a different word because the sentence reads better that way is ordinary. Two things are the tell: restating for fake depth, and the thesaurus reach, where you grab a fancier word only to dodge repeating a plain one. Repeat the plain one.

## Vary structure, not just sentences

The shape of the whole piece gives you away too: paragraphs of near-identical length, each opening with a topic sentence and closing on a wrap-up, "on one hand / on the other" framing where a real person would take a side, the neat concluding bow. Real writing is lumpy. Some paragraphs run a single line. People start mid-thought, chase a tangent, and stop when they're done. Watch openings and closings hardest: AI nearly always sets up context before making its point and resolves on a little uplift. Start closer to the middle, and let the last line do real work instead of recapping.

This matters most on longer pieces, though. A short email or a text lands in a single scored window, so there the sentence-by-sentence texture (rhythm, word choice, usage) does more work than the overall arc. Save the structural surgery for anything long.

## Let specifics come from real knowledge

AI reaches for the safe, most-probable word. A real writer reaches for the precise one: the exact term, the specific number, the detail only someone who did the thing would include. The tell runs below famous phrases too: the giveaway is usually the ordinary, high-probability transition, the default adjective in front of the default noun. Fix it with the specific, slightly-off word your particular author would land on. Don't reach for archaic or rarer words to sound impressive (the thesaurus effect is its own tell).

## Prefer real usage over textbook grammar

AI writing is hypercorrect. The giveaway is the missing usage choices educated writers make without noticing. Adopt these, keep them consistent, don't scatter them:

- Idiom preposition drift: "on accident," "based off of," "different than," "centered around," "bored of," "try and [verb]."
- Hypercorrections: "between you and I," "for my wife and I."
- Notional agreement: "there's a couple reasons," "none of them are," "a bunch of people were."
- Constructions AI is trained to fix: "comprised of," "the reason is because," restrictive "which."
- Conditional slip (conversational only): "if I would have known."
- Relaxed case/number: "who" for "whom," "less" for "fewer," singular "they."

Do NOT use errors that read as uneducated: comma splices, "we was," "should of," misplaced apostrophes. The target is a competent writer who doesn't fuss over prescriptive rules.

## Commit to an idiolect and hold it

Keep one author consistent across the whole piece: dialect, generation, pet phrasings, register, punctuation habits. A consistent idiolect is what synthetic mirrors struggle to reproduce. Detectors split text into windows and score each in context: there is no averaging out. One flat, generic paragraph gets flagged on its own. Every paragraph has to carry the voice, especially the boring middle ones where voice tends to flatten.

## Surface hygiene (the baseline)

Clear these without over-correcting into an obviously scrubbed style: markdown in prose, overused AI phrases ("in today's fast-paced world," "it's crucial to note"), em dashes, bullet lists, rule-of-three triads, "not just X but Y," decorative Unicode, cheerful-assistant headers ("Certainly! Here's"), UI emojis.

## Cut what the idea can survive without

- Empty intensifiers: really, very, quite, actually, just, simply, basically, truly.
- Bloated connectives: "in order to" -> "to," "due to the fact that" -> "because," "at this point in time" -> "now."
- Wind-up before the point: "when it comes to X," "in terms of X." Start at X.
- Doublings: "each and every," "first and foremost," "various different."
- Meta-narration: "as mentioned above," "what this means is." Just say the thing.

Answer the prompt and answer once. Don't over-explain: assume shared context, leave the obvious unsaid. A gap the reader can fill reads more human than one you fill for them. (Cutting filler is not the same as writing short; keep the length swings.)
