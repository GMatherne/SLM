"""Unit tests for the corpus-cleaning filters in fetch_human.py.

    python datagen/_test_cleaning.py        # exits 0 iff every assertion passes

Discipline (see CLEANING.md): this repo has been burned by OVER-rejection, so every
filter is pinned by BOTH kinds of case:
  * POSITIVE  -- a string WITH the artifact -> asserted stripped / rejected.
  * NEGATIVE  -- legit text that MUST survive / pass unchanged.
Do not delete the negatives to make a new filter pass; they are the guard rails.

All non-ASCII / invisible artifacts are built from explicit code points with chr() so
that NO literal zero-width / line-separator char ever lives in this source file (a
stray U+2028 would silently split lines in editors, git, and tooling).
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fetch_human as fh  # noqa: E402

_N = 0


def eq(got, want, label):
    global _N
    assert got == want, f"FAIL [{label}]: got {got!r}, want {want!r}"
    _N += 1


def yes(cond, label):
    global _N
    assert cond, f"FAIL [{label}]: expected truthy"
    _N += 1


def no(cond, label):
    global _N
    assert not cond, f"FAIL [{label}]: expected falsy"
    _N += 1


EMDASH = chr(0x2014)

# A clean, self-contained ~95-word answer that must pass ok() untouched. Reused as the
# body for REJECT tests: prove ok() accepts it, then re-run with one artifact injected.
VALID = (
    "Photosynthesis is how green plants turn sunlight into chemical energy. "
    "Inside the leaves, chlorophyll captures light and uses that energy to split "
    "water molecules into hydrogen and oxygen. The oxygen escapes through tiny pores "
    "while the hydrogen combines with carbon dioxide pulled from the air. That "
    "reaction builds simple sugars, which the plant stores or burns for growth. "
    "Without this quiet process the atmosphere would hold far less oxygen, and most "
    "of the life we see on land could never have appeared in the first place."
)
VALID_Q = "Can you explain how photosynthesis actually works?"


# ---------------------------------------------------------------------------- #
# 1. HTML entities + zero-width / invisible unicode  (clean, both sides)
# ---------------------------------------------------------------------------- #
def test_entities():
    # POSITIVE -- entities decoded, incl. a double-encoded loop and malformed leftovers.
    eq(fh.clean("Tom &amp; Jerry &lt;3"), "Tom & Jerry <3", "entity-basic")
    eq(fh.clean("salt &amp;amp; pepper"), "salt & pepper", "entity-double-amp")
    eq(fh.clean("gap &amp;#x200B; here"), "gap here", "entity-double-encoded-zwsp")
    eq(fh.clean("x &fakeentity; y"), "x y", "entity-malformed-named")
    eq(fh.clean("num &#8203; done"), "num done", "entity-numeric-zwsp")  # &#8203; == U+200B
    # NEGATIVE -- bare ampersands / comparators in prose must survive.
    eq(fh.clean("Salt & pepper, 3 < 4 and 5 > 2"), "Salt & pepper, 3 < 4 and 5 > 2",
       "entity-neg-bare-amp")
    eq(fh.clean("AT&T raised prices"), "AT&T raised prices", "entity-neg-att")


def test_invisible():
    # Build inputs from explicit code points -- no literal invisibles in this file.
    ZWSP, ZWNJ, ZWJ = chr(0x200B), chr(0x200C), chr(0x200D)
    BOM, SHY, WJ = chr(0xFEFF), chr(0x00AD), chr(0x2060)
    LRE, LSEP = chr(0x202A), chr(0x2028)        # Cf bidi mark, and Zl line separator
    NBSP, IDSP = chr(0x00A0), chr(0x3000)       # non-breaking + ideographic space
    # POSITIVE -- zero-width / format chars removed; unicode spaces normalized.
    eq(fh.clean("a" + ZWSP + "b"), "ab", "inv-zwsp")
    eq(fh.clean("wo" + ZWNJ + "rd" + ZWJ + "join"), "wordjoin", "inv-zwnj-zwj")
    eq(fh.clean(BOM + "hello" + WJ + "there"), "hellothere", "inv-bom-wordjoiner")
    eq(fh.clean("co" + SHY + "op"), "coop", "inv-soft-hyphen")
    eq(fh.clean("left" + LRE + "right"), "leftright", "inv-cf-bidi")
    eq(fh.clean("line" + LSEP + "break"), "linebreak", "inv-line-sep")  # U+2028 removed, not spaced
    eq(fh.clean("a" + NBSP + "b"), "a b", "inv-nbsp")
    eq(fh.clean("a b c" + IDSP + "d"), "a b c d", "inv-ideographic-space")
    # NEGATIVE -- plain prose is untouched (em-dash is NORMALIZED below, not here).
    eq(fh.clean("The cat sat on the mat."), "The cat sat on the mat.", "inv-neg-plain")


# ---------------------------------------------------------------------------- #
# 2. Chat-template / dialogue markers  (_TEMPLATE_MARK -> REJECT, both sides)
# ---------------------------------------------------------------------------- #
def test_template_marks():
    for s in ["### Human:", "### Assistant:", "## User", "###Human", "### humna",
              "<|im_start|>", "<|im_end|>", "[INST]", "[/INST]", "<s>", "</s>", "<S>"]:
        yes(fh._TEMPLATE_MARK.search(s), f"tmpl-pos {s!r}")
    # NEGATIVE -- these words / symbols without the marker syntax must NOT trip it.
    for s in ["I use C# and F# every day", "the mists rolled in", "assistant professor",
              "human beings are curious", "5 < 3 is false", "less than <5 items",
              "the answer is s > 0", "a list of items"]:
        no(fh._TEMPLATE_MARK.search(s), f"tmpl-neg {s!r}")
    # REJECT wiring: a template marker on either side drops the whole example.
    no(fh.ok("### Human: hi there", VALID), "tmpl-reject-prompt")
    no(fh.ok(VALID_Q, VALID + " [INST] do this"), "tmpl-reject-resp")


# ---------------------------------------------------------------------------- #
# 3. Markdown cruft  (STRIP conservatively in clean, both sides)
# ---------------------------------------------------------------------------- #
def test_markdown_positive():
    eq(fh.clean("This is **bold** text"), "This is bold text", "md-bold")
    eq(fh.clean("use __emphasis__ here"), "use emphasis here", "md-underscore-bold")
    eq(fh.clean("run the `code` now"), "run the code now", "md-inline-code")
    eq(fh.clean("# Heading"), "Heading", "md-h1")
    eq(fh.clean("###### Deep heading"), "Deep heading", "md-h6")
    eq(fh.clean("> a quoted line"), "a quoted line", "md-blockquote")
    eq(fh.clean("- bullet one"), "bullet one", "md-bullet-dash")
    eq(fh.clean("* bullet two"), "bullet two", "md-bullet-star")
    eq(fh.clean("+ bullet three"), "bullet three", "md-bullet-plus")
    eq(fh.clean("# Title\n> quote\n- item\n+ next"), "Title\nquote\nitem\nnext",
       "md-multiline-combo")


def test_markdown_negative():
    # The famous over-rejection traps -- ALL must survive byte-for-byte.
    for s in ["C# and F#", "compute 5 * 3 = 15", "the picture of health", "surprise",
              "exercise", "co-op", "post-WWII", "credit", "a #1 ranking",
              "A* is a search algorithm", "email me at a@b.com", "2 + 2 - 1 = 3",
              "she said 'hi' and left", "the multiplier is 3*4 here",
              "*italics* stay put with single stars"]:
        eq(fh.clean(s), s, f"md-neg {s!r}")


# ---------------------------------------------------------------------------- #
# R2-1. Smart punctuation -> NORMALIZE to ASCII (clean, both sides)
# ---------------------------------------------------------------------------- #
def test_smart_punct():
    LSQ, RSQ, LDQ, RDQ = chr(0x2018), chr(0x2019), chr(0x201C), chr(0x201D)
    ENDASH, ELLIPSIS, PRIME = chr(0x2013), chr(0x2026), chr(0x2032)
    # POSITIVE -- curly quotes/dashes/ellipsis flattened to ASCII.
    eq(fh.clean(LDQ + "hi" + RDQ), '"hi"', "sp-double-quotes")
    eq(fh.clean("it" + RSQ + "s " + LSQ + "x" + RSQ), "it's 'x'", "sp-single-quotes")
    eq(fh.clean("a" + ENDASH + "b"), "a-b", "sp-en-dash")
    eq(fh.clean("well" + EMDASH + "then"), "well-then", "sp-em-dash")
    eq(fh.clean("wait" + ELLIPSIS + "ok"), "wait...ok", "sp-ellipsis")
    eq(fh.clean("5" + PRIME + " tall"), "5' tall", "sp-prime")
    # NEGATIVE -- already-ASCII punctuation is left exactly as-is (no hyphen merging).
    for s in ["it's a 'quote' and a \"double\"", "well-known co-op post-WWII",
              "wait... ok then", 'she said "hi" - really', "a - b and x-y-z"]:
        eq(fh.clean(s), s, f"sp-neg {s!r}")


# ---------------------------------------------------------------------------- #
# R2-2. LaTeX/TeX in a PROMPT -> REJECT (resp already rejects $ and backslash)
# ---------------------------------------------------------------------------- #
def test_tex_prompt():
    B = chr(92)
    pos = ["Solve $x^2 + 1 = 0$", "reduce $a_i$ now", "Use " + B + "frac{1}{2}",
           "the " + B + "alpha decay rate", "let " + B + "theta vary", B + "begin{aligned}",
           "apply " + B + "cdot here"]
    for p in pos:
        yes(fh._TEX.search(p), f"tex-pos {p!r}")
        no(fh.ok(p, VALID), f"tex-reject {p!r}")
    # NEGATIVE -- money / lone $ / ranges / C# must NOT be seen as TeX.
    for p in ["it cost $5", "price is $1,000", "between $5 and $10", "pay $10 or $20",
              "I use C# and F#", "the answer is 5 dollars"]:
        no(fh._TEX.search(p), f"tex-neg {p!r}")
    yes(fh.ok("How much more is the $10 item than the $5 one?", VALID), "tex-money-ok")


# ---------------------------------------------------------------------------- #
# R2-4. @username cross-refs -> STRIP (clean, both sides)
# ---------------------------------------------------------------------------- #
def test_at_mention():
    # POSITIVE -- standalone handle removed, gap tidied by whitespace-collapse.
    eq(fh.clean("As @Ilan noted, this works"), "As noted, this works", "at-midsentence")
    eq(fh.clean("@user thanks for that"), "thanks for that", "at-leading")
    # NEGATIVE -- e-mail addresses, prices, and counts with @ are untouched.
    eq(fh.clean("reach me at bob@example.com please"),
       "reach me at bob@example.com please", "at-neg-email")
    eq(fh.clean("3 apples @ $5 each"), "3 apples @ $5 each", "at-neg-price")


# ---------------------------------------------------------------------------- #
# R2-5. Foreign-script -> REJECT (both sides, >=2 non-Latin letters)
# ---------------------------------------------------------------------------- #
def test_foreign_script():
    cjk = "This means " + chr(0x4F60) + chr(0x597D) + " friend"
    cyr = chr(0x041F) + chr(0x0440) + chr(0x0438) + "vet everyone"
    grk = "the term " + chr(0x03BB) + chr(0x03BF) + "gos here"
    heb = "the letters " + chr(0x05D0) + chr(0x05D1) + " appear"
    ara = "the letters " + chr(0x0627) + chr(0x0628) + " appear"
    for s in (cjk, cyr, grk, heb, ara):
        yes(fh._foreign_script(s), "fs-pos")
    # REJECT wiring: fires on either side.
    no(fh.ok(cjk, VALID), "fs-reject-prompt")
    no(fh.ok(VALID_Q, VALID + " " + cyr), "fs-reject-resp")
    # NEGATIVE -- accented Latin, unit SYMBOLS, and a lone math glyph are spared.
    accented = "cafe " + chr(0xE9) + " resume " + chr(0xF1) + " naive " + chr(0xFC) + " over"
    symbols = "5 " + chr(0xB5) + "m at 20" + chr(0xB0) + "C, then 3 " + chr(0xD7) + " 4"
    one_greek = "the angle " + chr(0x03B8) + " is small"
    for s in (accented, symbols, one_greek, "plain english sentence"):
        no(fh._foreign_script(s), "fs-neg")
    yes(fh.ok(VALID_Q, VALID + " (about 5 " + chr(0xB5) + "m)"), "fs-symbols-ok")


# ---------------------------------------------------------------------------- #
# R2-3. Leaked redaction token: _URL_0 (no trailing underscore) now caught.
# ---------------------------------------------------------------------------- #
def test_url_token():
    yes(fh._URL.search("see _URL_0 for details"), "url-no-trailing-underscore")
    yes(fh._URL.search("see _URL_0_ for details"), "url-with-trailing-underscore")
    yes(fh._URL.search("visit https://example.com now"), "url-http")
    no(fh._URL.search("just plain prose here"), "url-neg")


# ---------------------------------------------------------------------------- #
# 4. Regression guards on neighbouring filters that share the cleaning path.
# ---------------------------------------------------------------------------- #
def test_neighbours_still_ok():
    # _REF_DEP "(?! of)" guard -- idiom survives, real image-ref still caught.
    no(fh._REF_DEP.search("you are the picture of health"), "refdep-neg-idiom")
    yes(fh._REF_DEP.search("notice in the picture"), "refdep-pos")
    # _americanize must not molest the classic false-friends.
    for s in ["surprise", "exercise", "credit", "genre", "acre"]:
        eq(fh._americanize(s), s, f"amer-neg {s!r}")
    # strip_refs still flattens md links / drops _URL_ tokens.
    eq(fh.strip_refs("see [the docs](http://x) _URL_3_ ok"), "see the docs ok",
       "strip_refs")


# ---------------------------------------------------------------------------- #
# 5. End-to-end: a legit multi-sentence answer survives the whole ok() gate, and
#    clean() leaves it (and its question) intact.
# ---------------------------------------------------------------------------- #
def test_valid_answer_survives():
    yes(fh.ok(VALID_Q, VALID), "valid-ok-passes")
    eq(fh.clean(VALID), VALID, "valid-clean-noop")
    eq(fh.clean(VALID_Q), VALID_Q, "valid-q-clean-noop")
    # A markdown-dressed but otherwise clean answer stays valid after stripping.
    dressed = "**Photosynthesis** is how plants make food. " + VALID
    cleaned = fh.clean(dressed)
    yes(fh.ok(VALID_Q, cleaned), "valid-dressed-ok")
    no("**" in cleaned, "valid-dressed-stripped")


# ---------------------------------------------------------------------------- #
# 6. Round-6: forum sign-offs (STRIP) + fabricated references (STRIP + REJECT)
# ---------------------------------------------------------------------------- #
def test_signoff_and_refs():
    # POSITIVE -- trailing forum sign-offs are peeled off by _deref (body survives).
    eq(fh._deref("The dough traps CO2 and rises. Hope this helps :)"),
       "The dough traps CO2 and rises.", "signoff-hope-emoji")
    eq(fh._deref("...so it floats. HTH"), "...so it floats.", "signoff-hth")
    eq(fh._deref("Do step one first. Let me know if you have questions!"),
       "Do step one first.", "signoff-letmeknow")
    eq(fh._deref("That's the gist. Good luck!"), "That's the gist.", "signoff-goodluck")
    # POSITIVE -- reference clauses / source footers stripped.
    eq(fh._deref("It cancels the wave. For more details check this link: how ANC works"),
       "It cancels the wave.", "ref-checklink")
    eq(fh._deref("Lightning can repeat. I highly recommend reading the book on storms"),
       "Lightning can repeat.", "ref-recommend")
    eq(fh._deref("Plants use sunlight.\nSources: 1) an encyclopedia 2) a textbook"),
       "Plants use sunlight.", "ref-sources-tail")
    # NEGATIVE -- legit prose must survive _deref byte-for-byte (the guard rails).
    for s in ["I hope you feel better soon.",
              "Check the oil level before you drive.",
              "The source of the Nile was long debated.",
              "We recommend practicing every day.",
              "See the difference between weather and climate.",
              "Let me know if you're stuck and we will debug it together."]:
        eq(fh._deref(s), s, f"deref-neg {s!r}")
    eq(fh._deref(VALID), VALID, "deref-valid-noop")
    # REJECT wiring -- hard fabrication signatures drop the whole example.
    no(fh.ok(VALID_Q, VALID + " doi: 10.1371/journal.pone.0113098"), "hardref-doi")
    no(fh.ok(VALID_Q, VALID + " [PDF]"), "hardref-pdf")
    no(fh.ok(VALID_Q, VALID + " as noted on wikipedia.org"), "hardref-domain")
    # NEGATIVE -- tech terms without a citation TLD and plain prose don't trip _HARD_REF.
    for s in ["I run Node.js locally", "a 3.5 inch disk", "at 9 a.m. sharp", "the .com era"]:
        no(fh._HARD_REF.search(s), f"hardref-neg {s!r}")
    yes(fh.ok(VALID_Q, VALID), "hardref-neg-valid-passes")


# ---------------------------------------------------------------------------- #
# 7. Round-6b residual sweep: inline Source: / TL;DR / P.S. / as-others (STRIP),
#    figure-table captions (REJECT).
# ---------------------------------------------------------------------------- #
def test_residual_sweep():
    # inline "Source:" citations -- clause-initial + parenthetical stripped.
    eq(fh._deref("Cortisol drops when you relax. Source: IAMA Psychiatric RN"),
       "Cortisol drops when you relax.", "cite-inline-trailing")
    eq(fh._deref("Trade grew fast. (Source: Age of Capital, Eric Hobsbawm.) It shaped Europe."),
       "Trade grew fast. It shaped Europe.", "cite-parenthetical")
    # NEGATIVE -- descriptive "source(s):" mid-clause / topic-label must survive.
    eq(fh._deref("They share the same source: the Columbus story."),
       "They share the same source: the Columbus story.", "cite-neg-descriptive")
    eq(fh._deref("For newer sources: academic work builds on itself."),
       "For newer sources: academic work builds on itself.", "cite-neg-topic")
    # TL;DR recap (leading or trailing).
    eq(fh._deref("Naps help if kept short. TL;DR: keep naps under 20 minutes."),
       "Naps help if kept short.", "tldr-trailing")
    eq(fh._deref("*TL;DR:* short naps only\nThey avoid deep sleep."),
       "They avoid deep sleep.", "tldr-leading")
    # P.S. addendum stripped; "PS4" NOT touched.
    eq(fh._deref("That's the plan. P.S. bring a jacket."), "That's the plan.", "ps-strip")
    eq(fh._deref("I still play games on my PS4 daily."),
       "I still play games on my PS4 daily.", "ps-neg-ps4")
    # as-others self-ref stripped; "as I said" (within-answer) kept.
    eq(fh._deref("As others mentioned, the water helps buoyancy."),
       "The water helps buoyancy.", "asothers-strip")
    eq(fh._deref("As I said earlier, momentum is conserved."),
       "As I said earlier, momentum is conserved.", "asothers-neg-self")
    # Figure/table caption -> REJECT; "figure 8 knot" / "table 2 feet" survive.
    no(fh.ok(VALID_Q, VALID + " Fig. 1. Series of events."), "figure-reject")
    no(fh.ok(VALID_Q, VALID + " See Table 2: results."), "table-reject")
    for s in ["a figure 8 knot is strong", "a table 2 feet wide", "the periodic table shows"]:
        no(fh._FIGURE.search(s), f"figure-neg {s!r}")
    # broadened figure filter (comma / caption-verb forms) -> REJECT.
    no(fh.ok(VALID_Q, VALID + " Figure 1, taken from the study."), "figure-comma-reject")
    no(fh.ok(VALID_Q, VALID + " Figure 2 shows the trend."), "figure-verb-reject")
    # author-year academic citation -> REJECT; dates / no-name years survive.
    no(fh.ok(VALID_Q, VALID + " as Shapiro (2011) demonstrated"), "yearcite-name")
    no(fh.ok(VALID_Q, VALID + " (Smith et al., 2003)"), "yearcite-etal")
    for s in ["The war ended in August (1945).", "born in (1990)", "the year 2011 was key"]:
        no(fh._YEAR_CITE.search(s), f"yearcite-neg {s!r}")
    yes(fh.ok(VALID_Q, VALID), "residual-neg-valid-passes")


def main():
    groups = (test_entities, test_invisible, test_template_marks,
              test_markdown_positive, test_markdown_negative,
              test_smart_punct, test_tex_prompt, test_at_mention,
              test_foreign_script, test_url_token,
              test_neighbours_still_ok, test_valid_answer_survives,
              test_signoff_and_refs, test_residual_sweep)
    for fn in groups:
        fn()
    print(f"OK -- all {_N} assertions passed across {len(groups)} test groups.")


if __name__ == "__main__":
    main()
