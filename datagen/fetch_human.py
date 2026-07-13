"""Fetch real, pre-AI human EDUCATIONAL text and build (prompt -> human response)
SFT pairs in ShareGPT format.

Round-3 changes over round 2 (see eval/colab_outputs/round2_findings.md, which
found tuned flipped 3/12 to human -- the direct/plain answers -- while longer,
walkthrough-y, or repetitive ones stayed AI):
  - Drop training answers that anaphora-repeat or restate (_repetitive) -- round-2
    tuned output padded to length by looping, which is also an AI tell.
  - Mix biased toward the styles that flipped: more ELI5 (450, casual/direct) and
    AskHistorians (280, narrative prose); less AskScience (150, dense/technical);
    Khan dropped (spoken "Let's say" walkthroughs read AI + kept leaking intros).
  (colab_train.py separately adds repetition_penalty to generation.)

Round-2 changes over round 1 (see eval/colab_outputs/round1_findings.md):
  - Length floor raised to 80-350 words -> fixes terse answers (the model learns
    the length of its targets).
  - Added AskScience + AskHistorians (long, WRITTEN human explanations) -> depth
    without the spoken tics.
  - Khan chunks are longer (~300w) and de-clicked.
  - Tic cleaning: strip leading "So/And/Well/Now", the Khan "let's talk about X"
    opener, and meta-openers ("I'll try", "Great question"); drop tic-heavy answers.
  - Stronger dedup: full-text exact + a cap on how many share the same opener
    (kills the "So let's talk about..." pileup that amplified the tic).

Round-4 additions (broaden narrow explainer -> usable tutor; human-only data):
  - Skeptics.StackExchange added (evidence-based myth-debunking: accuracy + correction).
  - Parked LOCAL datasets converted into two new behaviours:
      * ChangeMyView (essays_cmv.json) -> argumentative WRITING HELP pairs.
      * college essays + feedback (essays_college.json) -> CORRECTION/feedback pairs
        ("here's my essay" -> feedback), with a lower word floor (feedback is short).
  - See CLEANING.md for every cleaning rule; colab_train.py adds an assistant-identity
    system prompt so the model stops confabulating a human/product identity.

Sources (all human, pre-ChatGPT):
  ELI5, AskScience, AskHistorians, 18 educational StackExchange sites (incl. Skeptics)
  via the HF datasets-server; plus CMV + college-essay data from data/ (Khan dropped).

Usage:
  python fetch_human.py            # default volumes (~1,700)
  python fetch_human.py --dry      # print samples, don't write
"""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import time
import unicodedata
from collections import Counter

import requests

BASE = "https://datasets-server.huggingface.co"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "human_dataset.jsonl")
SE = "flax-sentence-embeddings/stackexchange_titlebody_best_voted_answer_jsonl"
SE_TUTORING = ["ell", "english", "physics", "biology", "chemistry", "astronomy",
               "earthscience", "history", "philosophy", "economics", "linguistics",
               "cogsci", "health", "music", "hsm", "matheducators", "academia",
               "skeptics",   # round 4: evidence-based myth-debunking (accuracy + correction)
               # round-4 additions -- subagent-vetted quality >=4 (writers=Writing.SE for the
               # essay behaviour; creative + experiential for voice/breadth). English only.
               # Dropped after vetting: languagelearning (garbled/error-laden), workplace (thin).
               # Dropped non-English language sites (latin/spanish/french): off-domain for an
               # English eval and their correctness can't be verified.
               "writers", "cseducators", "literature",
               "worldbuilding", "cooking", "gardening", "diy", "woodworking",
               "parenting", "bicycles", "outdoors"]
DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

MIN_WORDS, MAX_WORDS = 80, 350
# essay behaviours: feedback is often short & pointed, full essays run long
ESSAY_MIN_WORDS, ESSAY_MAX_WORDS = 40, 650

_URL = re.compile(r"https?://\S+|www\.\S+|_URL_\d+_?|\]\([^)]*\)")  # _URL_0_ AND _URL_0 tokens + md links
_IMG_REF = re.compile(r"\b(see|as shown|refer to)\s+(the\s+)?(image|images|figure|fig|diagram|picture|photo|attachment|above|below|following)\b", re.I)
# Reference-dependent phrases: the answer leans on a link/image/video that isn't
# present (surfaced by subagent QA of the new SE sites -> "here is a link", "notice
# in the picture", "pretty gif for clarification"). REJECT. The `(?! of)` guard
# spares idioms like "the picture of health".
_REF_DEP = re.compile(
    r"\b(?:here'?s|here is|there'?s) (?:a |an |the |my )?(?:link|gif|picture|image|photo|video|diagram|sketch|screenshot|chart)\b"
    r"|\b(?:see|watch|look at|click|follow) (?:the |this |that |my )?(?:link|gif|video|screenshot|attachment)\b"
    r"|\bin (?:the|this|that) (?:picture|image|photo|video|diagram|screenshot|gif|sketch)\b(?! of\b)"
    r"|\bgo (?:to|on) (?:this|the|that) (?:page|link|video|site)\b"
    r"|\bthis (?:image|photo|video|gif|screenshot|diagram|sketch)\b"
    r"|\byoutube\b|\bgif for\b|\bpretty gif\b|\bnotice in the\b", re.I)
# Reddit/AskHistorians moderator + copy-paste meta that isn't an actual answer.
_META_JUNK = re.compile(r"(we don'?t allow|this submission|\br/\w+|/r/|/u/|top-level comment"
                        r"|(?:have|been|was) removed|our (?:subreddit )?rules|read our rules"
                        r"|i'?ll copy my answer|as a reminder,)", re.I)
# Reddit "Edit:"/"Update:" addenda -> STRIP from the marker to the end (the answer
# before it is usually fine). Catches mid-sentence, markdown-wrapped (**Edit**:,
# *edit:), and after-a-word ("Obligatory edit:") forms. The \b before the marker
# means it will NOT fire on cr-edit, edit-or, or com-post etc.
_EDIT_ADDENDUM = re.compile(
    r"[\s*_]*\b(?:edit|edited|update|eta)\b[\s*_]*\d*[\s*_]*[:\-].*$", re.I | re.S)
# Dangling academic citation markers ("[7]", "[132]") that point to a bibliography
# not present in the text -> STRIP (reference-dependent, like image-refs). This is
# the scaffolding the round-3 model imitated in "[soundbites] (1) (2) (3) (4)".
_CITEMARK = re.compile(r"\s?\[\d{1,4}\]")
# ---- Round-6: forum sign-offs + fabricated references ------------------------------ #
# The Reddit/SE corpus that gives a human voice also injects (a) trailing sign-offs
# ("Hope this helps :)") and (b) fabricated references -- "check this link: <title>",
# "recommend reading <fake book>", "Sources: ...", DOIs (round-5 #6/#8/#10/#13). _deref
# STRIPs the trailing sign-off + reference clauses (the answer body survives); ok() then
# REJECTs anything whose HARD fabrication signature (DOI / bare domain / [PDF]) survived.
_SIGNOFF = re.compile(
    r"\s*(?:hope (?:this|that|it) (?:helps|helped|is helpful|is useful)"
    r"|hope this answers[^.!?\n]*"
    r"|hope (?:this|that) makes sense"
    r"|\bHTH\b"
    r"|let me know if (?:you (?:have|need|want|'?d like)|there(?:'?s| is| are)"
    r"|anything else|this (?:helps|works|makes sense))[^.!?\n]*"
    r"|feel free to (?:ask|reach out|comment|message)[^.!?\n]*"
    r"|(?:good|best of) luck(?: with [^.!?\n]*)?"
    r"|happy to (?:help|clarify)[^.!?\n]*"
    r"|cheers)"
    r"[\s.!)]*(?:[:;=]-?[)DdpP])?[\s.!)]*$", re.I)
# A sentence/clause pointing the reader at an external link/article/source -> STRIP.
_REF_CLAUSE = re.compile(
    r"(?:(?<=[.!?\n])|^)\s*(?:"
    r"(?:you (?:can|could|should|may|might) |please |i(?:'d| would| highly)? )?"
    r"recommend (?:reading|watching|checking out|(?:the )?(?:book|article|paper|video|study))[^.!?\n]*"
    r"|(?:you (?:can|could|should) |please )?(?:check (?:out )?|see |read |visit )"
    r"(?:this|the|these|our|my) (?:link|article|page|video|post|thread|website|site|resource|blog|study|paper)s?[^.!?\n]*"
    r"|for (?:more|further) (?:info|information|details|reading|reference)[,]?[^.!?\n]*"
    r"|here'?s (?:a|an|the) (?:link|good (?:article|read|resource|video|paper))[^.!?\n]*"
    r")[.!?]*", re.I)
# A "Sources:" / "Source:" citation footer at the start of a line -> STRIP to the end.
_SOURCES_TAIL = re.compile(r"(?:^|\n)\s*sources?\s*:.*", re.I | re.S)
# Hard fabrication signatures that must NOT survive stripping -> REJECT in ok().
_HARD_REF = re.compile(
    r"\b10\.\d{3,}/\S+"                                 # DOI, e.g. 10.1371/journal.pone.x
    r"|\[PDF\]"                                         # "[PDF]" marker
    r"|\b[a-zA-Z][\w-]*\.(?:com|org|edu|gov)\b",        # bare domain w/o scheme (wikipedia.org)
    re.I)
# Round-6b (residual sweep). INLINE "Source:" citation -- clause-initial or parenthetical
# ONLY, so descriptive "the same source:" / "for newer sources:" (mid-clause) survive.
_CITE = re.compile(
    r"\(\s*(?:info |image )?sources?\s*:[^)\n]*\)"                        # (Source: ...)
    r"|(?:(?<=[.!?])\s+|(?<=\n)\s*|^)(?:info |image )?sources?\s*:[^\n]*",  # clause-initial "Source: ..."
    re.I)
# "TL;DR" recap marker + its line -> STRIP (forum/AI summary tell).
_TLDR = re.compile(r"\*{0,2}\s*\bTL;?\s?DR\b\s*\*{0,2}\s*:?[^\n]*", re.I)
# Trailing "P.S." addendum -> STRIP. Requires "P.S." or "PS:" (a period or colon) so
# "PS4"/"PS5" and other bare "PS" tokens are NOT touched.
_PS = re.compile(r"(?:(?<=[.!?])\s+|(?<=\n)\s*)(?:P\.\s?S\.?|PS\s*:)\s?[^\n]*", re.I)
# Forum self-reference to OTHER commenters -> STRIP the phrase, keep the point. Only
# others/some/many/people (NOT "as I said", which is legit within-answer self-reference).
_ASOTHERS = re.compile(
    r"(?:(?<=[.!?])\s+|(?<=\n)\s*|^)as (?:others|some|many|people|a few|several|someone|already)"
    r"(?: have| already)? (?:said|mentioned|noted|pointed out|stated|explained)[,:]?\s*", re.I)
# Figure/table CAPTION or academic (Author YEAR) citation referring to absent/external
# material -> REJECT. NEG-guarded so "figure 8 knot", "table 2 feet", "the periodic table",
# and dates like "(August 1945)" survive.
_FIGURE = re.compile(
    r"\bfig\.\s*\d"                                                          # "Fig. 1"
    r"|\b(?:figure|table)\s+\d+\s*[:.,]"                                     # "Figure 1," / "Table 2:" / "Figure 3."
    r"|\b(?:figure|table)\s+\d+\s+(?:shows?|depicts?|illustrates?|displays?|taken|above|below)"  # "Figure 1 shows/taken"
    r"|\(\s*(?:figure|fig\.?|table)\s*\d",                                   # "(Figure 1" / "(fig 2"
    re.I)
_MONTHS = (r"January|February|March|April|May|June|July|August|September|October|November|December"
           r"|Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday")
# Academic author-year citation -> REJECT (teaches the model to cite/fabricate sources).
# NEG-guarded: a month/day before the year is a DATE, not a citation ("(August 1945)").
_YEAR_CITE = re.compile(
    r"\b(?!(?:" + _MONTHS + r")\b)[A-Z][a-z]{2,}\s+\((?:1[6-9]|20)\d\d\)"    # "Shapiro (2011)"
    r"|\bet al\.?,?\s*\(?(?:1[6-9]|20)\d\d")                                 # "et al. (2011)" / "et al., 2003"
# Forum-interaction / support-sub / self-reference tells -> REJECT the whole answer.
# These are the register bleeds seen in the round-3 chat ("please edit your post",
# "I'm sorry for what happened", "as I very rarely post here").
_FORUM = re.compile(
    r"(edit your post|your posts?\b|post your code|the sidebar|\bthis sub\b|cross-?post"
    r"|\bupvot|\bdownvot|\bkarma\b|\bsubreddit|\bflair\b|\bthe mods?\b"
    r"|sorry (?:for|to hear) (?:what|about)|hope it gets better|hope you feel better"
    r"|you'?re not alone|stay strong"
    r"|rarely post here|long[- ]?time lurker|\blurker|first time post"
    r"|as others (?:have )?(?:said|mentioned|noted|pointed out))", re.I)
# Reddit /u/user or /r/sub tags (slash form -> unambiguous, won't hit "r/min").
# Checked on BOTH prompt and response so forum-context questions are dropped too.
_REDDIT_TAG = re.compile(r"/[ur]/\w+", re.I)
_OP = re.compile(r"\bOP\b")   # Reddit "original poster"; case-sensitive so it skips "op-amp"/"Op."
# Chat-template / instruction-dialogue markers -> REJECT. The CMV data was ChangeMyView
# reformatted as multi-turn "### Human:/### Assistant:" dialogues; the round-4 model
# learned that format and hallucinated a fake debate on the argument prompt (#15).
# Covers "### Human/Assistant/User", "<|im_start|>"/"<|im_end|>", Llama "[INST]"/"[/INST]",
# and BOS/EOS "<s>"/"</s>" (the <s> form is also caught in resp by the html-tag check).
_TEMPLATE_MARK = re.compile(
    r"#{2,}\s*(?:human|assistant|humna|user)\b|<\|im_(?:start|end)"
    r"|\[/?INST\]|</?s>", re.I)
# Reddit thread-title junk in the QUESTION: community addresses ("Biologists of
# Reddit", "of AskScience") + recurring feature threads -> REJECT (not real questions).
_FORUM_TITLE = re.compile(
    r"\bof (?:reddit|askscience|askhistorians|askengineers|askphilosophy|askanthropology|askeconomics)\b"
    r"|\b(?:x-?post|cross-?post)\b|floating feature|monday methods|tuesday trivia|theory thursday"
    r"|feature friday|short answers to simple|megathread|ask me anything|panel ama", re.I)
# Leading Reddit "ELI5:"/"ELIF:" tag -> STRIP.
_ELI5_TAG = re.compile(r"^\s*(?:eli\s?5|elif)\b:?\s*", re.I)
# Leading topic-label prefix -> STRIP, but ONLY when a self-contained capitalized
# wh-question follows ("Yugoslav wars: Why was..."). If the text after the colon is
# lowercase or a pronoun ("Chromatin shearing: what is it"), the label IS the
# subject, so leave it.
_TITLE_PREFIX = re.compile(
    r"^\s*(?![Ww]h|[Hh]ow\b)[A-Za-z][\w &'/\-]{0,44}?:\s+(?=(?:What|Why|How|When|Where|Who|Whom|Whose|Which)\b)")
_DISCOURSE = re.compile(r"^\s*(?:okay|ok|so|and|well|now|right|alright|basically)\b[,]?\s+", re.I)
_KHAN_OPENER = re.compile(r"^\s*let'?s talk(?: a little bit)?(?: more)? about[^.?!]*[.?!]\s+", re.I)
_META_OPENER = re.compile(r"^\s*(?:i'?ll try|let me explain|let me try|great question|good question|sure|certainly|of course|absolutely)\b[.!,]?\s+", re.I)
_GREETING = re.compile(r"^\s*(?:hi|hello|hey)[,]?\s+(?:everyone|everybody|guys|folks|wordsmiths|class)\b[,.!]?\s+", re.I)
# Khan self-intro opener, e.g. "Hi, this is Kim from Khan Academy, and today ...".
_SELFINTRO = re.compile(r"^\s*(?:hi|hello|hey)[,]?\s+(?:this is|i'?m|there)\b[^.?!]{0,90}[.?!]\s+", re.I)
_SENT_SO = re.compile(r"(?:^|[.!?]\s+)(?:so|and)\b", re.I)   # sentence-initial so/and (the tic)
# Khan non-lesson junk to DROP entirely: fundraising, vocab word-of-the-day clips,
# course-intro/meta videos. (Substring match -- no \b, which broke on "wordsmiths".)
_KHAN_JUNK = re.compile(r"(thank you for|thanks for watching|welcome to|please subscrib|donat"
                        r"|wordsmith|word of the day|today'?s word"
                        r"|the word (?:we're|we are|we'll be|i'?m) (?:talking about|going to|exploring)"
                        r"|in these (?:next )?(?:few )?videos|i'?m going to be talking about"
                        r"|khanmigo|ai-powered guide|in this video"
                        r"|khan academy|this video will|teaming up|free online course)", re.I)

# ---- Invisible unicode + leftover HTML entities -> STRIP (in clean, both sides) ---- #
# Zero-width / invisible / format chars to remove outright. Category "Cf" (unescape,
# soft-hyphen, word-joiner, BOM, the LRM/RLM bidi marks...) covers most; U+2028/U+2029
# (line/paragraph separator) are Zl/Zp so they're listed here explicitly too.
_INVISIBLE = "\u200b\u200c\u200d\ufeff\u00ad\u2060\u2028\u2029"
# Unicode spaces (NBSP U+00A0, en/em/thin spaces, ideographic space...) -> a normal
# space, so the whitespace collapse below can do its job.
_UNI_SPACE = re.compile(r"[\u00a0\u1680\u2000-\u200a\u202f\u205f\u3000]")
# Malformed / unknown HTML entities that survive the html.unescape loop -> STRIP. The
# `&#` (numeric) form is required to start with `#`, so it can't fire on "AT&T"/"3 & 4";
# the named form needs a trailing `;`, so it can't fire on "AT&T is".
_DEAD_ENTITY = re.compile(r"&#x?[0-9A-Fa-f]+;?|&[a-zA-Z]+;|&\s+#x?[0-9A-Fa-f]+;")  # 3rd: space-broken "& #x200B;" (needs ; so "& #1 ranking"/"AT&T" survive)

# ---- Markdown cruft -> STRIP conservatively (in clean, both sides) ----------------- #
# Targeted patterns, NOT blanket removal, so they never touch C#, F#, A*, "5 * 3"
# (single spaced *), "#1" (ranking; no space after #), hyphens, or apostrophes. See the
# NEGATIVE cases in _test_cleaning.py, which lock this in.
_MD_BOLD = re.compile(r"\*\*([^*\n]+)\*\*|__([^_\n]+)__")   # **x**/__x__ -> x (double marks only)
_MD_CODE = re.compile(r"`([^`\n]+)`")                       # `x` -> x (paired single backticks)
_MD_HEAD = re.compile(r"(?m)^[ \t]*#{1,6}[ \t]+")          # line-initial "# ".."###### " (needs a space)
_MD_QUOTE = re.compile(r"(?m)^[ \t]*>[ \t]?")              # line-initial blockquote ">"
_MD_BULLET = re.compile(r"(?m)^[ \t]*[-*+][ \t]+")         # line-initial list bullet (needs a space)

# ---- Smart punctuation -> NORMALIZE to ASCII (in clean, both sides) ---------------- #
# Highest-volume survivor + reconciles a file-drift bug. Character-level, like
# _americanize, so it doesn't touch the structure Pangram reads. Curly quotes -> straight,
# en/em dash -> hyphen, ellipsis -> "...". Already-ASCII ' " - ... are unchanged, and
# legit hyphens are never merged (we only remap the specific unicode dash code points).
_SMART_PUNCT = {
    0x2018: "'", 0x2019: "'", 0x201A: "'", 0x201B: "'",   # single quotes / low-9
    0x201C: '"', 0x201D: '"', 0x201E: '"', 0x201F: '"',   # double quotes / low-9
    0x2032: "'", 0x2033: '"',                              # prime / double-prime
    0x2013: "-", 0x2014: "-", 0x2012: "-", 0x2015: "-",    # en / em / figure / horizontal-bar dash
    0x2026: "...",                                          # horizontal ellipsis
}

# ---- LaTeX / TeX in a PROMPT -> REJECT (the resp $/\\ guard is response-only) ------ #
# Paired inline math REQUIRES a math-operator char between the $...$ so it can't fire on
# a price RANGE ("$5 and $10"); a lone "$5"/"$1,000" has no closing $ so it's safe too.
_TEX = re.compile(
    r"\$[^$\n]*[\\^_={}][^$\n]*\$"                                    # $ ...mathchar... $
    r"|\\(?:frac|sqrt|sum|int|pi|alpha|beta|theta|cdot|times|leq|geq|infty|begin|end)\b"
    r"|\\[a-zA-Z]+\{")                                               # \command{
# Standalone @handle cross-refs -> STRIP (both sides). The (?<!\w) look-behind spares
# e-mail addresses (bob@x.com: @ preceded by a word char) and the [A-Za-z] start spares
# "@ $5" / "@1" (prices/counts). Whitespace collapse in clean() tidies the gap.
_AT_MENTION = re.compile(r"(?<!\w)@[A-Za-z]\w*")

# ---- Foreign-script REJECT (both sides): >=2 non-Latin LETTERS ---------------------- #
# CJK / Cyrillic / Greek / Arabic / Hebrew blocks. Triggers on category-L chars only, so
# it skips punctuation/combining marks inside those blocks. Incidental accented Latin
# (e/n/u with diacritics) is NOT in these blocks; the micro/degree/multiply SYMBOLS are
# category So/Sm (not letters) -> all spared. Threshold 2 spares a lone math glyph (theta).
_FOREIGN_BLOCKS = (
    (0x0370, 0x03FF), (0x1F00, 0x1FFF),               # Greek + Greek Extended
    (0x0400, 0x052F),                                  # Cyrillic (+ supplement)
    (0x0590, 0x05FF),                                  # Hebrew
    (0x0600, 0x06FF), (0x0750, 0x077F), (0x08A0, 0x08FF),  # Arabic (+ supplements)
    (0x3040, 0x30FF),                                  # Hiragana + Katakana
    (0x3400, 0x4DBF), (0x4E00, 0x9FFF),                # CJK ext-A + Unified
    (0xAC00, 0xD7A3), (0xF900, 0xFAFF),                # Hangul syllables + CJK compat
)


def _shouty(t):
    a = sum(c.isalpha() for c in t)
    return a > 0 and sum(c.isupper() for c in t) / a > 0.3


def _foreign_script(t):
    """True if t carries >=2 non-Latin LETTERS from CJK/Cyrillic/Greek/Arabic/Hebrew."""
    n = 0
    for c in t:
        o = ord(c)
        if any(lo <= o <= hi for lo, hi in _FOREIGN_BLOCKS) and unicodedata.category(c)[0] == "L":
            n += 1
            if n >= 2:
                return True
    return False


def _repetitive(resp):
    """True if the answer anaphora-repeats or restates itself.

    Round-2 tuned answers looped ("It's the... It's the same... It's also the
    reason...") -- poor prose AND an AI tell. Drop training targets that do this
    so the model doesn't learn to pad by restating.
    """
    sents = [s.strip() for s in re.split(r"[.!?]+", resp) if s.strip()]
    if len(sents) >= 5:                                   # repeated sentence openers
        openers = [" ".join(s.lower().split()[:2]) for s in sents if s.split()]
        if openers and Counter(openers).most_common(1)[0][1] / len(openers) > 0.35:
            return True
    words = resp.lower().split()
    if len(words) >= 30:                                  # restated trigrams
        tri = [tuple(words[i:i + 3]) for i in range(len(words) - 2)]
        if len(set(tri)) / len(tri) < 0.75:
            return True
    return False


def clean(text):
    prev = None
    while prev != text:                              # loop undoes double-encoding (&amp;#x200B;)
        prev = text
        text = html.unescape(text)                   # &amp; &quot; &gt; -> & " >
    text = _DEAD_ENTITY.sub("", text)                # malformed/unknown entities that survived
    text = "".join(c for c in text                   # drop zero-width / invisible / format chars
                   if c not in _INVISIBLE and unicodedata.category(c) != "Cf")
    text = _UNI_SPACE.sub(" ", text)                 # NBSP & other unicode spaces -> normal space
    text = text.translate(_SMART_PUNCT)              # curly quotes/dashes/ellipsis -> ASCII
    text = _AT_MENTION.sub("", text)                 # standalone @handle cross-refs -> removed
    text = text.replace("\r", " ").replace("<br />", "\n").strip()
    text = _MD_BOLD.sub(lambda m: m.group(1) or m.group(2), text)   # **x**/__x__ -> x
    text = _MD_CODE.sub(r"\1", text)                 # `x` -> x
    text = _MD_HEAD.sub("", text)                    # line-initial "#".."######" heading marks
    text = _MD_QUOTE.sub("", text)                   # line-initial blockquote ">"
    text = _MD_BULLET.sub("", text)                  # line-initial list bullet (-, *, +)
    text = re.sub(r"[ \t]+", " ", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def clean_vtt(raw):
    out = []
    for ln in raw.splitlines():
        ln = ln.strip()
        if not ln or ln.startswith(("WEBVTT", "Kind:", "Language:")) or "-->" in ln or re.match(r"^\d+$", ln):
            continue
        out.append(re.sub(r"^-\s*(\[[^\]]+\]\s*)?", "", ln))
    return re.sub(r"\s+", " ", " ".join(out)).strip()


def first_chunk(text, max_words=300):
    words = text.split()
    if len(words) <= max_words:
        return text.strip()
    chunk = " ".join(words[:max_words])
    cut = max(chunk.rfind(". "), chunk.rfind("? "), chunk.rfind("! "))
    return (chunk[:cut + 1] if cut > 300 else chunk).strip()


def strip_refs(t):
    """Flatten markdown links -> their text and drop _URL_N_ redaction tokens.
    Used on prompts (Reddit selftext carries these); responses with them are
    rejected outright by ok()."""
    t = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", t)   # [text](url) -> text
    t = re.sub(r"_URL_\d+_?", "", t)
    return re.sub(r"[ \t]+", " ", t).strip()


def _deref(t):
    """Round-6 STRIP (response side): trailing forum sign-offs + fabricated link/source
    reference clauses. ok() then REJECTs anything whose hard fabrication signature
    (DOI / bare domain / [PDF]) survived, or that got gutted below min_words."""
    t = _SOURCES_TAIL.sub("", t)             # line-start "Sources: ..." footer to end
    t = _CITE.sub("", t)                     # inline / parenthetical "Source:" citations
    t = _REF_CLAUSE.sub("", t)               # "check this link / recommend reading ..." clauses
    t = _TLDR.sub("", t)                     # "TL;DR:" recap line
    t = _PS.sub("", t)                       # trailing "P.S." addendum
    t = _ASOTHERS.sub("", t)                 # "as others said" forum self-reference
    prev = None
    while prev != t:                         # peel stacked trailing sign-offs
        prev = t
        t = _SIGNOFF.sub("", t)
    t = re.sub(r"[ \t]+", " ", t).strip()
    return (t[:1].upper() + t[1:]) if t else t   # re-capitalize if a leading phrase was peeled


def declick(t):
    """Strip leading discourse markers / Khan opener / meta-openers, iteratively."""
    prev = None
    while prev != t:
        prev = t
        t = _SELFINTRO.sub("", t)
        t = _GREETING.sub("", t)
        t = _DISCOURSE.sub("", t)
        t = _KHAN_OPENER.sub("", t)
        t = _META_OPENER.sub("", t)
    return (t[:1].upper() + t[1:]) if t else t


def khan_map(d):
    """(prompt, response) for a Khan transcript, or ('','') to drop non-lessons."""
    title = (d.get("title") or "").strip()
    text = first_chunk(clean_vtt(d.get("content", "")))
    if not title or _KHAN_JUNK.search(title) or _KHAN_JUNK.search(text[:160]):
        return ("", "")
    return (f"Can you explain {title.lower()}?", text)


def ok(prompt, resp, max_words=MAX_WORDS, min_words=MIN_WORDS):
    if not prompt or not resp:
        return False
    if (_REDDIT_TAG.search(prompt) or _REDDIT_TAG.search(resp)
            or _OP.search(prompt) or _OP.search(resp)):          # forum-context Q or A
        return False
    if _FORUM.search(prompt) or _FORUM_TITLE.search(prompt):     # forum-meta / thread-title question
        return False
    if _URL.search(prompt) or _IMG_REF.search(prompt) or _REF_DEP.search(prompt):  # image/link-dependent question
        return False
    if _TEMPLATE_MARK.search(prompt) or _TEMPLATE_MARK.search(resp):   # chat-template / dialogue contamination
        return False
    if _TEX.search(prompt):                                  # LaTeX/TeX prompt (resp already rejects $/\\)
        return False
    if _foreign_script(prompt) or _foreign_script(resp):     # >=2 non-Latin letters (CJK/Cyrillic/...)
        return False
    words = len(resp.split())
    if words < min_words or words > max_words:
        return False
    if (_URL.search(resp) or _IMG_REF.search(resp) or _META_JUNK.search(resp)
            or _FORUM.search(resp) or _REF_DEP.search(resp) or _shouty(resp)
            or _HARD_REF.search(resp) or _FIGURE.search(resp)   # round-6: fabrication / figure captions
            or _YEAR_CITE.search(resp)):                        # round-6b: academic author-year citation
        return False
    if "�" in resp or "```" in resp or "{" in resp or "}" in resp:
        return False
    if "$" in resp or "\\" in resp:
        return False
    if re.search(r"==|!=|\+\+|::|\bprintf\b|console\.|#include|</?[a-z]+>", resp):
        return False
    if sum(c.isascii() for c in resp) / max(1, len(resp)) < 0.97:
        return False
    if len(_SENT_SO.findall(resp)) > 2:            # tic-heavy (sentence-initial so/and)
        return False
    if _repetitive(resp):                          # anaphora / restating (round 3)
        return False
    return True


def api_rows(dataset, config, split, offsets):
    for off in offsets:
        data = None
        for attempt in range(4):                     # retry through rate-limits
            try:
                j = requests.get(f"{BASE}/rows", params={"dataset": dataset, "config": config,
                                 "split": split, "offset": off, "length": 100}, timeout=60).json()
                if "rows" in j:
                    data = j["rows"]; break
            except Exception:
                pass
            time.sleep(2 * (attempt + 1))            # backoff on throttle/error
        if not data:
            continue
        for row in data:
            yield row["row"]
        time.sleep(0.25)                             # gentle pacing between calls


def best_answer(row):
    ans = row.get("answers") or {}
    txt = ans.get("text") or []
    sc = ans.get("score") or []
    if not txt:
        return ""
    i = max(range(len(txt)), key=lambda k: sc[k]) if len(sc) == len(txt) and sc else 0
    return txt[i]


def ask_prompt(row):
    t = (row.get("title") or "").strip()
    st = (row.get("selftext") or "").strip()
    if st and st.lower() not in ("[removed]", "[deleted]") and st != t:
        return (t + "\n" + st)
    return t


def trunc_prompt(p, max_words=90):
    w = p.split()
    return p if len(w) <= max_words else " ".join(w[:max_words])


# ---- Round-4 essay behaviours: writing help (CMV) + correction/feedback (college) --- #
def _fix_mojibake(t):
    # the college-essay dump lost curly apostrophes -> replacement char. It's almost
    # always a possessive/contraction apostrophe ("you<?>ve" -> "you've").
    return t.replace("�", "'")


def _load_local(fname):
    p = os.path.join(DATA, fname)
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else []


# Varied framings so the model doesn't overfit one phrasing (cycled by index).
_CMV_ASKS = [
    'Someone argues: "{v}" How would you respond?',
    "Make the case against this view: {v}",
    "Write a persuasive response to this claim: {v}",
    'A friend says: "{v}" What is the counterargument?',
]
_FEEDBACK_ASKS = [
    "Can you give me feedback on this essay?",
    "Here's my college essay -- how can I improve it?",
    "What do you think of my personal statement?",
    "Please review my essay and suggest what to fix.",
    "I wrote this essay. What is working and what isn't?",
]


# ---- British -> American spelling normalisation (round 4) ----------------------- #
# Character-level only, so it's safe for the "reads human" signal (both spellings are
# human) while matching the American-English preference. Regular classes use
# root-WHITELISTED suffix rules so they NEVER touch surprise/exercise/genre/acre/
# four/hour/analysis/emphasis; the rest is a curated dict. "programmed"/"programmer"
# are correct American, so only the noun "programme" is mapped (via the dict).
_OUR_RX = re.compile(
    r"\b(?:col|behavi|fav|hon|neighb|lab|flav|hum|vap|od|rum|harb|savi|endeav|splend"
    r"|cand|clam|val|tum|arm|parl|ferv|rig|vig|demean|succ)our", re.I)
_ISE_RX = re.compile(
    r"\b(organ|real|recogn|apolog|emphas|critic|summar|categor|special|minim|maxim"
    r"|memor|character|standard|general|symbol|colon|civil|stabil|util|visual|steril"
    r"|hypothes|sympath|priorit|modern|normal|final|local|central|rational)(is)"
    r"(e|es|ed|ing|ation|ations|able|er|ers)\b", re.I)
_YSE_RX = re.compile(r"\b(analy|paraly|cataly|dialy|electroly)(s)(e|es|ed|ing)\b", re.I)
_RE_RX = re.compile(
    r"\b(kilomet|millimet|centimet|nanomet|cent|met|lit|theat|fib|calib|somb|spect"
    r"|lust|meag|sab|scept)(re)(s)?\b", re.I)
_GREY_RX = re.compile(r"\bgrey(ish|ed|s)?\b")     # lowercase only -> skips "Grey" (Earl Grey, surnames)
_PROG_RX = re.compile(r"\bprogramme(s)?\b")       # lowercase only -> skips org names ("... Programme")


def _case(src, dst):
    if src.isupper():
        return dst.upper()
    if src[:1].isupper():
        return dst[:1].upper() + dst[1:]
    return dst


_AMER = {
    "defence": "defense", "defences": "defenses", "offence": "offense", "offences": "offenses",
    "licence": "license", "licences": "licenses", "pretence": "pretense",
    "practise": "practice", "practised": "practiced", "practising": "practicing",
    "travelling": "traveling", "travelled": "traveled", "traveller": "traveler", "travellers": "travelers",
    "cancelled": "canceled", "cancelling": "canceling", "labelled": "labeled", "labelling": "labeling",
    "modelling": "modeling", "modelled": "modeled", "fuelled": "fueled", "fuelling": "fueling",
    "signalling": "signaling", "signalled": "signaled", "marvellous": "marvelous",
    "counsellor": "counselor", "counsellors": "counselors", "jewellery": "jewelry",
    "aluminium": "aluminum", "aeroplane": "airplane", "aeroplanes": "airplanes", "maths": "math",
    "sceptic": "skeptic", "sceptics": "skeptics", "sceptical": "skeptical", "scepticism": "skepticism",
    "mould": "mold", "moulds": "molds", "moulded": "molded", "moulding": "molding", "mouldy": "moldy",
    "moustache": "mustache", "moustaches": "mustaches", "plough": "plow", "ploughs": "plows",
    "ploughed": "plowed", "ploughing": "plowing", "draught": "draft", "draughts": "drafts",
    "storey": "story", "storeys": "stories", "kerb": "curb", "kerbs": "curbs",
    "cheque": "check", "cheques": "checks", "pyjamas": "pajamas", "manoeuvre": "maneuver",
    "manoeuvres": "maneuvers", "manoeuvred": "maneuvered", "manoeuvring": "maneuvering",
    "sulphur": "sulfur", "cosy": "cozy", "gaol": "jail", "artefact": "artifact", "artefacts": "artifacts",
    "foetus": "fetus", "foetal": "fetal", "oestrogen": "estrogen", "anaesthesia": "anesthesia",
    "anaesthetic": "anesthetic", "paediatric": "pediatric", "paediatrician": "pediatrician",
    "haemoglobin": "hemoglobin", "haemorrhage": "hemorrhage", "diarrhoea": "diarrhea",
    "oesophagus": "esophagus", "coeliac": "celiac", "anaemia": "anemia", "anaemic": "anemic",
    "leukaemia": "leukemia", "orthopaedic": "orthopedic", "encyclopaedia": "encyclopedia",
}
_AMER_RX = re.compile(r"\b(" + "|".join(sorted(_AMER, key=len, reverse=True)) + r")\b", re.I)


def _americanize(t):
    t = _OUR_RX.sub(lambda m: m.group(0)[:-2] + m.group(0)[-1], t)                       # colour->color
    t = _ISE_RX.sub(lambda m: m.group(1) + ("IZ" if m.group(2).isupper() else "iz") + m.group(3), t)
    t = _YSE_RX.sub(lambda m: m.group(1) + ("Z" if m.group(2).isupper() else "z") + m.group(3), t)
    t = _RE_RX.sub(lambda m: m.group(1) + ("ER" if m.group(2).isupper() else "er") + (m.group(3) or ""), t)
    t = _GREY_RX.sub(lambda m: "gray" + (m.group(1) or ""), t)
    t = _PROG_RX.sub(lambda m: "program" + (m.group(1) or ""), t)
    t = _AMER_RX.sub(lambda m: _case(m.group(0), _AMER[m.group(0).lower()]), t)
    return t


def collect(caps):
    rows, seen_full, opener_counts = [], set(), {}

    def add(source, prompt, resp, max_words=MAX_WORDS, trunc=True, min_words=MIN_WORDS):
        prompt = _EDIT_ADDENDUM.sub("", strip_refs(clean(trunc_prompt(prompt) if trunc else prompt)))
        prompt = _TITLE_PREFIX.sub("", _ELI5_TAG.sub("", prompt)).strip()
        resp = _deref(_CITEMARK.sub("", _EDIT_ADDENDUM.sub("", declick(clean(resp))))).strip()
        prompt, resp = _americanize(prompt), _americanize(resp)   # British -> American spelling
        if not ok(prompt, resp, max_words, min_words):
            return False
        fk = re.sub(r"\s+", " ", resp.lower()).strip()
        if fk in seen_full:
            return False
        op = " ".join(fk.split()[:5])
        if opener_counts.get(op, 0) >= 3:          # cap identical openers
            return False
        seen_full.add(fk)
        opener_counts[op] = opener_counts.get(op, 0) + 1
        rows.append({"source": source, "prompt": prompt, "response": resp})
        return True

    def pull(name, gen, mapper, cap):
        n = 0
        for d in gen:
            if n >= cap:
                break
            p, r = mapper(d)
            if add(name, p, r):
                n += 1
        print(f"{name}: kept {n}")

    pull("eli5", api_rows("sentence-transformers/eli5", "pair", "train", list(range(0, 300000, 10000))),
         lambda d: (d.get("question", ""), d.get("answer", "")), caps["eli5"])
    pull("askscience", api_rows("Pavithree/askScience", "default", "train", list(range(0, 60000, 400))),
         lambda d: (ask_prompt(d), best_answer(d)), caps["asksci"])
    pull("askhistorians", api_rows("Pavithree/askHistorians", "default", "train", list(range(0, 40000, 400))),
         lambda d: (ask_prompt(d), best_answer(d)), caps["askhist"])
    for site in SE_TUTORING:
        pull(f"se-{site}", api_rows(SE, site, "train", [0, 2000, 6000, 14000, 30000, 60000]),
             lambda d: (d.get("title_body", ""), d.get("upvoted_answer", "")), caps["se"])
    if caps["khan"]:      # dropped by default in round 3 (spoken walkthroughs read AI)
        pull("khan", api_rows("iblai/ibl-khanacademy-transcripts", "default", "train", list(range(0, 7700, 200))),
             khan_map, caps["khan"])

    # Round-4 essay behaviours from the parked LOCAL datasets (not the HF API):
    # CMV -> argumentative writing help; college essays + feedback -> correction.
    # trunc=False keeps the whole essay in the prompt; ESSAY_MAX_WORDS allows longer
    # responses. Both still run through the full forum/edit/dedup cleaning.
    n = 0
    for i, e in enumerate(_load_local("essays_cmv.json")):
        if n >= caps.get("cmv", 0):
            break
        ask = _CMV_ASKS[i % len(_CMV_ASKS)].format(v=trunc_prompt(clean(e.get("prompt", "")), 100))
        if add("cmv", ask, e.get("response", ""), max_words=ESSAY_MAX_WORDS, trunc=False):
            n += 1
    if caps.get("cmv"):
        print(f"cmv: kept {n}")

    n = 0
    for i, e in enumerate(_load_local("essays_college.json")):
        if n >= caps.get("essayfb", 0):
            break
        essay = _fix_mojibake(clean(e.get("essay", "")))
        if add("essay-feedback", _FEEDBACK_ASKS[i % len(_FEEDBACK_ASKS)] + "\n\n" + essay,
               _fix_mojibake(e.get("feedback", "")), max_words=ESSAY_MAX_WORDS,
               trunc=False, min_words=ESSAY_MIN_WORDS):
            n += 1
    if caps.get("essayfb"):
        print(f"essay-feedback: kept {n}")
    return rows


def main():
    ap = argparse.ArgumentParser()
    # Round-4 mix: bias toward RIGOROUS, mechanism-carrying sources to raise accuracy
    # + information retention (AskScience + AskHistorians up; thin/loose ELI5 down),
    # while keeping enough ELI5 for the casual voice that flipped Pangram. This is the
    # voice<->accuracy frontier test -- measure both Pangram and accuracy after.
    ap.add_argument("--eli5", type=int, default=250)
    ap.add_argument("--asksci", type=int, default=350)
    ap.add_argument("--askhist", type=int, default=300)
    ap.add_argument("--se-per-site", type=int, default=30)   # 32 sites now; 30 keeps SE < half the mix
    ap.add_argument("--khan", type=int, default=0)
    # Round-4 essay behaviours (parked local datasets): CMV writing help + college feedback.
    # CMV dropped: essays_cmv.json is ChangeMyView reformatted as instruction dialogues
    # (### Human:/### Assistant: markers) -> contaminated the model (#15). Re-add only
    # with a CLEAN argumentative source. college-essay feedback stays (correction behaviour).
    ap.add_argument("--cmv", type=int, default=0)
    ap.add_argument("--essayfb", type=int, default=60)
    ap.add_argument("--dry", action="store_true")
    args = ap.parse_args()

    caps = {"eli5": args.eli5, "asksci": args.asksci, "askhist": args.askhist,
            "se": args.se_per_site, "khan": args.khan,
            "cmv": args.cmv, "essayfb": args.essayfb}
    rows = collect(caps)

    from collections import Counter
    lens = [len(r["response"].split()) for r in rows]
    print("\nby source:", dict(Counter(r["source"].split("-")[0] if r["source"].startswith("se-") else r["source"] for r in rows)))
    print(f"total: {len(rows)} | resp words: min {min(lens)}, median {sorted(lens)[len(lens)//2]}, max {max(lens)}")
    for r in rows[:2] + rows[-2:]:
        print(f"\n[{r['source']}] Q: {r['prompt'][:70]}\n           A: {r['response'][:170]}")

    if args.dry:
        print("\n(dry -- nothing written)"); return
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps({"conversations": [{"from": "human", "value": r["prompt"]},
                    {"from": "assistant", "value": r["response"]}]}, ensure_ascii=False) + "\n")
    with open(OUT.replace(".jsonl", "_full.jsonl"), "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"\nwrote {len(rows)} -> {OUT}")


if __name__ == "__main__":
    main()
