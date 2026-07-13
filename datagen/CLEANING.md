# Data cleaning reference

Every cleaning rule in `fetch_human.py`, what it does, and the problem it solved.
Human web text (Reddit/StackExchange) carries a lot of forum scaffolding; if it
leaks into training, the model learns to *behave like a forum poster* (see the
round-3 chat session: "please edit your post", "I'm Replika", "Edit: typo"). The
rules below strip or drop that while preserving real prose.

## Two mechanisms
- **STRIP** — edit the text in place, keep the example (used when the junk is a
  detachable prefix/suffix and the rest is a good answer).
- **REJECT** — drop the whole example (used when the text *is* the junk, or is
  reference-dependent / off-register).

Cleaning runs on **both the prompt and the response** (a lesson learned the hard
way — cleaning only responses left 13 `edit:` addenda sitting in the questions).

## Core discipline (read before adding a rule)
1. **Look at real matches first.** Count substring vs. real hits before filtering.
   `edit` matched 189× but most were cr**edit**/M**edit**erranean; only ~60 were
   real Reddit edits. `post` (40) was mostly "post-WWII"/"post-quantum" — legit.
2. **Prefer word boundaries + context over substrings.** `\bOP\b` (case-sensitive)
   catches Reddit "OP" but not "op-amp"/"Op."; `/[ur]/\w+` (slash form) catches
   `/r/knives` but not the unit "r/min".
3. **Strip narrowly, reject broadly.** For "Topic: question" titles, strip the
   label ONLY when a self-contained capitalized wh-question follows ("Yugoslav
   wars: Why…"); if it's "Chromatin shearing: what is it", the label IS the
   subject — keep it.
4. **Check both sides and audit a battery**, not one pattern.
5. **Pin every filter with a NEGATIVE test.** `_test_cleaning.py` (run
   `python datagen/_test_cleaning.py`, must exit 0) holds POSITIVE cases (artifact →
   stripped/rejected) and NEGATIVE cases that MUST survive unchanged ("C# and F#",
   "5 * 3", "the picture of health", "co-op", "post-WWII", "a #1 ranking", em-dash +
   apostrophe prose, a full valid answer). Add both when you add a rule; never delete
   a negative to make a new rule pass. Invisible-char inputs are built via `chr()` so
   no literal zero-width/line-separator ever lives in the test source.

## REJECT rules (drop the example)
| rule | side | catches | why |
|------|------|---------|-----|
| length `MIN/MAX_WORDS` (80–350) | resp | too short / too long | terse answers read AI; overlong pad |
| `_URL` | prompt+resp | `http(s)://`, `www.`, `_URL_0_` **and** `_URL_0` (trailing `_` now optional) tokens, `](…)` md links | link-dependent, not self-contained |
| `_IMG_REF` | resp | "see the image/figure/diagram/above" | needs an image we don't have |
| `_REF_DEP` | resp | "here is a link", "notice in the picture", "go to this page", "pretty gif", "youtube" (`(?! of)` spares "picture of health") | answer leans on an absent link/image/video — surfaced by subagent QA of new SE sites |
| `_META_JUNK` | resp | mod-speak: "we don't allow", "this submission", `/r/`, `/u/`, "removed", "our rules", "I'll copy my answer" | not an answer |
| `_FORUM` | prompt+resp | "edit your post", "your post", "cross-post", "up/downvote", "karma", "subreddit", "flair", "the mod(s)", support-sub empathy ("sorry for what…", "hope it gets better", "stay strong"), self-reference ("rarely post here", "lurker", "as others said") | forum register bleed |
| `_REDDIT_TAG` | prompt+resp | `/u/user`, `/r/sub` | forum-context Q/A |
| `_OP` | prompt+resp | `\bOP\b` (case-sensitive) | Reddit "original poster" |
| `_FORUM_TITLE` | prompt | community addresses ("Biologists of Reddit", "of AskScience"), feature threads ("Monday Methods", "Tuesday Trivia", "Floating Feature", "Megathread", "AMA"), x-posts | thread titles, not questions |
| `_TEMPLATE_MARK` | prompt+resp | chat-template / dialogue markers: `### Human/Assistant/User` (`humna` typo), `<\|im_start\|>`/`<\|im_end\|>`, Llama `[INST]`/`[/INST]`, BOS/EOS `<s>`/`</s>` | instruction-dialogue contamination — the CMV data was reformatted as `### Human:/### Assistant:` turns and the round-4 model hallucinated a fake debate (#15). NEG-guarded: "assistant professor", "human beings", "C#/F#", "5 < 3", "<5 items" do NOT trip it (the marker syntax — `##`, `<\|`, `[`, `<…>` — is required) |
| `_TEX` | prompt | LaTeX/TeX in a question: paired inline math `$…mathchar…$`, TeX commands (`\frac`, `\sqrt`, `\alpha`, `\begin`, …), `\cmd{` | the resp `$`/`\` guard was resp-only; TeX prompts aren't self-contained prose. NEG-guarded: the paired form REQUIRES a math char (`\^_={}`) inside, so money ranges "$5 and $10" pass; a lone "$5"/"$1,000" has no closing `$`; "C#" is untouched |
| `_foreign_script` | prompt+resp | ≥2 non-Latin LETTERS from CJK / Cyrillic / Greek / Arabic / Hebrew blocks (category-L only) | off-target language / garbled. NEG-guarded: incidental accented Latin (é ñ ü), the µ/°/× SYMBOLS (category So/Sm, not letters), and a **lone** math glyph (θ) are all spared (threshold is 2) |
| `_shouty` | resp | >30% uppercase | shouting / not prose |
| non-ASCII < 97% | resp | mostly non-English / garbled | off-target language |
| `�` / ``` ``` `` / `{` `}` / `$` / `\` / code ops | resp | mojibake, code, LaTeX | non-prose |
| `_SENT_SO` (>2) | resp | tic-heavy sentence-initial "So/And" | spoken-transcript tic |
| `_repetitive` | resp | repeated openers (>35%) or low unique-trigram ratio (<0.75) | anaphora/restating — an AI tell |
| `_HARD_REF` (round 6) | resp | fabricated-citation signatures that must not survive: a DOI (`10.xxxx/…`), `[PDF]`, or a bare domain (`wikipedia.org`, `reddit.com`) | round-5 answers invented DOIs/books/links (#8 fake link, #10 fake article, #13 fake book "by Dr. Gaffney"). Dry-run: rejects 21/1788. NEG-guarded: TLDs limited to `com/org/edu/gov`, so `Node.js`/`asp.net`/`the .com era`/`9 a.m.` don't trip it (a letter must sit immediately before the dot) |

## STRIP rules (keep the example, remove the junk)
| rule | side | removes |
|------|------|---------|
| `clean` (entities) | both | HTML entities decoded in a **loop** with `html.unescape` until stable — handles double-encoding (`&amp;#x200B;`→`&#x200B;`→zero-width). `_DEAD_ENTITY` then strips malformed/unknown leftovers: `&#x?[0-9A-Fa-f]+;?` and `&[a-zA-Z]+;`. NEG-guarded: the numeric form needs `#`, the named form needs a trailing `;`, so "AT&T", "Salt & pepper", "3 < 4" survive |
| `clean` (invisibles) | both | zero-width / format chars via `_INVISIBLE` + Unicode category **Cf** (`U+200B/C/D`, `U+FEFF` BOM, `U+00AD` soft-hyphen, `U+2060` word-joiner, bidi marks, `U+2028/U+2029` sep). `_UNI_SPACE` normalizes NBSP `U+00A0` + other unicode spaces → normal space; then whitespace collapses (newline handling unchanged). NEG: em-dash + apostrophe prose untouched |
| `clean` (markdown) | both | conservative markdown STRIP: `**bold**`/`__x__`→text (`_MD_BOLD`, double marks only), `` `code` ``→text (`_MD_CODE`, paired single backticks), line-initial `#{1,6}␣`→removed (`_MD_HEAD`), line-initial `>`→removed (`_MD_QUOTE`), line-initial `- * +` bullet→removed (`_MD_BULLET`). NEG-guarded (targeted, NOT blanket): `C#`, `F#`, `A*`, `5 * 3` (single spaced star), `#1` (no space after `#`), hyphens (`co-op`, `post-WWII`), apostrophes, single-star `*italics*` all survive |
| `clean` (@mention) | both | `_AT_MENTION` removes standalone `@Handle` cross-refs ("As @Ilan noted" → "As noted"; gap tidied by whitespace-collapse). NEG-guarded: `(?<!\w)` spares e-mail (`bob@x.com`) and the `[A-Za-z]` start spares prices/counts (`@ $5`, `@1`) |
| `strip_refs` | prompt | `[text](url)` → `text`; `_URL_N_?` tokens |
| `declick` | resp | leading discourse ("So/And/Well/Now"), Khan "let's talk about…", meta-openers ("I'll try", "Great question"), greetings ("Hi everyone"), self-intros ("Hi, this is Kim…") |
| `_EDIT_ADDENDUM` | prompt+resp | Reddit "Edit:/Update:" addenda to end — incl. mid-sentence, markdown-wrapped (`**Edit**:`), after-a-word ("Obligatory edit:") |
| `_ELI5_TAG` | prompt | leading "ELI5:" / "ELIF:" tag |
| `_TITLE_PREFIX` | prompt | redundant topic label before a self-contained capitalized wh-question |
| `_CITEMARK` | resp | dangling `[7]`/`[132]` citation markers (bibliography not present) |
| `_deref` → `_SIGNOFF` (round 6) | resp | trailing forum sign-offs, peeled iteratively: "Hope this helps (:))", "HTH", "Let me know if you have/need…", "feel free to ask/comment", "good/best of luck", "happy to help", "cheers". NEG-guarded: "I hope you feel better", "Let me know if you're stuck …" (non-closing) survive |
| `_deref` → `_REF_CLAUSE` / `_SOURCES_TAIL` (round 6) | resp | fabricated-reference clauses — "check/see/read this/the link/article/page/video…", "(I) recommend reading/the book/article…", "for more details, see…", "here's a link" — plus a line-initial "Sources:/Source:" footer stripped to end. Dry-run: strips 51/1788. NEG-guarded: "check the oil", "the source of the Nile", "we recommend practicing", "see the difference" survive |
| `trunc_prompt` | prompt | truncates question to 90 words |

## NORMALIZE (character-level rewrites, both sides)
Rewriting rather than filtering is justified only when it's character-level and doesn't
touch the structure Pangram reads.

### Smart punctuation → ASCII (`_SMART_PUNCT`, in `clean`)
Highest-volume survivor (~1330) and it reconciles a file-drift bug. `str.translate` maps
curly single/double quotes → `'` / `"`, en/em/figure/bar dash → `-`, prime/double-prime →
`'` / `"`, and the horizontal ellipsis `…` → `...`. **NEG-guarded**: already-ASCII `'` `"`
`-` `...` are untouched, and only the specific unicode *dash* code points are remapped, so
legit hyphens are never merged (`well-known`, `co-op`, `x-y-z` survive).

### British → American spelling (`_americanize`)
This matches the American-English preference.
- **Suffix rules with root whitelists** (handle inflections, avoid disasters):
  `-our`→`-or` (colour→color, favourite→favorite), `-ise`→`-ize` (organise→organize),
  `-yse`→`-yze` (analyse→analyze), `-re`→`-er` (centre→center, kilometres→kilometers).
  Whitelisting roots is what stops surprise→"surprize", exercise→"exercize",
  genre/acre/four/hour, and the nouns analysis/emphasis/hypothesis (the suffix must
  be a verb ending, so these are never touched).
- **Curated dict** for irregulars: defence→defense, practise→practice, travelling→
  traveling, aluminium→aluminum, maths→math, sceptic→skeptic, foetus→fetus,
  haemoglobin→hemoglobin, etc.
- **Lowercase-only** for proper-noun collisions: `grey`→`gray` (skips "Earl Grey"),
  `programme`→`program` (skips "... Programme" org names).
- **Left alone** (accepted American): catalogue, dialogue.

## DEDUP (in `collect`/`add`)
- **Full-text exact**: identical responses dropped.
- **Opener cap**: ≤3 responses may share the same first-5-words (kills a pile-up
  of one templated opener that amplifies a tic).

## Khan-specific (archived — Khan dropped in round 3)
`clean_vtt`, `first_chunk`, `khan_map`, `_KHAN_JUNK` handled spoken transcripts
(fundraising clips, "word of the day", Khanmigo ads, self-intros). Kept in code
but `--khan 0` by default: spoken "Let's say…" walkthroughs read AI on Pangram.

## Deferred (deliberately NOT implemented)
- **Bracketed `[word]` editorial** (round-2 audit, low priority). Left out on purpose:
  a generic "strip standalone `[word]`" cannot be made precise without false positives —
  it collides with `[sic]`, `[i.e.]`, and legit quoted insertions ("he [the author]
  argued"). Per the anti-over-rejection charter, a stray `[word]` is cheaper than
  mangling real prose. Revisit only with a concrete token whitelist from the Audit
  (e.g. `[citation needed]`, `[deleted]`), which would be unambiguous.

## API robustness
`api_rows` retries with backoff and paces calls (0.25s) to survive HF
datasets-server rate limits.
