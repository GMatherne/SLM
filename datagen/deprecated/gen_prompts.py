"""Prompt diversifier: compose varied writing-TASK prompts by randomly combining
building blocks, so the dataset's inputs stay spontaneous and non-repetitive.

This randomizes the TASK only. The voice stays fixed in persona.md -- never jitter
the persona. The whole reason it's one fixed person is that a fine-tune can only
learn a steady voice, and randomly-varied quirks become their own detectable
signature. So: diverse situations, one consistent writer.

The building-block pools below are meant to be edited. Add your own recipients,
scenarios, moods, and topics; every one you add multiplies the combinations.

Usage:
  python gen_prompts.py                          # 60 prompts -> stdout (JSONL)
  python gen_prompts.py --n 300                   # 300 prompts
  python gen_prompts.py --n 300 --seed 7          # reproducible
  python gen_prompts.py --medium feedback         # one medium only
  python gen_prompts.py --n 300 --out extra.jsonl # write to a file to cull
  python gen_prompts.py --n 50 --append           # append straight to questions.jsonl

Output is deliberately over-generated: cull by hand before training. A prompt that
reads awkward or duplicates the spirit of another one is a reject, same as the
README's quality-gate discipline for generations.
"""

from __future__ import annotations

import argparse
import json
import os
import random

HERE = os.path.dirname(os.path.abspath(__file__))
QUESTIONS = os.path.join(HERE, "questions.jsonl")

RNG = random.Random()


def pick(seq):
    return RNG.choice(seq)


# --------------------------------------------------------------------------
# Building blocks -- edit freely. Each pool is a plain list; add or cut lines.
# --------------------------------------------------------------------------

DURATIONS = ["a few days", "over a week", "almost two weeks", "a month now", "since last Tuesday"]
MOODS_MILD = ["a little annoyed", "getting frustrated", "pretty over it", "trying not to be a pain", "worried it'll get worse"]

EMAIL_AUTHORITY = ["your landlord", "the property manager", "your building's super", "the leasing office"]
EMAIL_REQUESTS = [
    "fix a kitchen faucet that's been leaking",
    "look at the heat that's barely working",
    "deal with a neighbor's dog barking all night",
    "replace a smoke detector that keeps chirping",
    "do something about the mold in the bathroom",
    "fix the front door lock that sticks",
]
EMAIL_ACADEMIC = ["a professor", "your TA", "the course coordinator"]
EMAIL_ACADEMIC_ASK = ["a two-day extension on a paper", "a chance to make up a missed quiz", "clarification on an assignment that's due tomorrow", "a meeting during office hours"]
EXCUSES = ["you were sick", "there was a family emergency", "you double-booked yourself and owned it", "your laptop died mid-week", "you genuinely lost track of the deadline"]
FOLLOWUP_CONTEXT = ["a job interview last week", "sending a proposal a client never answered", "meeting someone at a conference", "an application you haven't heard back on"]
WORKPLACE = ["your manager", "a coworker on another team", "the whole team", "your boss's boss", "a client"]
WORK_ASKS = ["push back a deadline that isn't realistic", "decline a meeting that could've been an email", "ask for time off during a busy stretch", "flag that a project is slipping", "ask for help without sounding like you're drowning"]
COMPANIES = ["your internet provider", "an airline", "a gym", "your insurance company", "a subscription service"]
CHARGES = ["a fee you were never told about", "a double charge on your card", "a price that went up without notice", "a cancellation you were still billed for"]
NEIGHBORISH = ["a neighbor", "the neighbor upstairs", "the people next door"]
NEIGHBOR_ISSUES = ["their car blocking your spot", "noise late on weeknights", "a shared fence that needs fixing", "their tree dropping leaves all over your yard"]

REDDIT_QUESTIONS = [
    "whether it's worth upgrading a 3-year-old laptop or just buying new",
    "how to get back into reading after years off",
    "if they should take a lower-paying job they'd actually like",
    "whether a mechanical keyboard is worth the money",
    "how to start running without hating it",
    "if it's normal to still not know what they want to do at 30",
]
AITA_SITUATIONS = ["skip a coworker's wedding", "not split a dinner bill evenly", "tell a friend their business idea is bad", "refuse to lend money to a sibling", "leave a group trip early"]
SUBREDDITS = ["personalfinance", "cooking", "buyitforlife", "askscience", "fitness", "houseplants"]
REDDIT_OPS = ["is clearly overthinking a small decision", "got some bad advice higher in the thread", "is about to make an expensive mistake", "just needs someone to say it's fine"]
BAD_TAKES = ["you should never rent, only buy", "you should quit any job you don't love immediately", "credit cards are always a trap"]

PLACES = ["a small ramen place you tried", "a new coffee shop downtown", "a diner you used to love", "a taco truck near work", "a fancy restaurant for an anniversary", "a brewery that just opened"]
REVIEW_MIXED = ["was great but had a brutal wait", "looked amazing but was overpriced for what you got", "had incredible food and terrible service", "was cozy but way too loud", "you wanted to love but left underwhelmed"]
PRODUCTS = ["a pair of running shoes", "a budget mechanical keyboard", "a robot vacuum", "an air fryer", "a carry-on suitcase", "a cheap pair of earbuds"]
PRODUCT_MIXED = ["felt great at first but wore out fast", "does the job but the app is a nightmare", "is a great deal if you can ignore one flaw", "you'd buy again despite one annoyance", "looked better in the photos than in person"]
SERVICES = ["a hotel", "a haircut place", "a moving company", "a dentist's office", "a car repair shop"]
SERVICE_MIXED = ["it was clean and cheap but the walls were paper-thin", "they did good work but took twice as long as promised", "the staff were kind but the place was disorganized", "everything was fine until the bill showed up"]

FRIENDS = ["a friend", "a close friend", "an old friend you've drifted from", "your best friend", "a friend you see once a year"]
MESSAGE_PURPOSES = [
    "backing out of weekend plans because you're worn out",
    "congratulating them on a new job, so it sounds like you mean it",
    "checking in after they went quiet for a couple weeks",
    "apologizing for forgetting their birthday",
    "asking to borrow something without being awkward about it",
    "telling them you can't make the wedding",
]
GROUPS = ["a group chat", "the family thread", "your friends planning a trip"]
GROUP_TASKS = ["pin down a date for dinner", "settle where to go on vacation", "figure out a gift everyone chips in on", "decide who's hosting the holidays"]
HARD_TEXTS = ["to a friend whose pet just died", "canceling on someone last minute again", "telling a friend you can't lend them money", "letting someone down easy after one date"]

ESSAY_TOPICS = [
    "a place from your childhood that still feels calming to think about",
    "a small habit you'd be a little embarrassed to admit",
    "a smell that drops you straight into a memory",
    "an object you've kept way longer than it makes sense to",
    "the last meal you remember being genuinely happy at",
]
ESSAY_REFLECT = [
    "the last time you changed your mind about something you were sure of",
    "a piece of advice you ignored and later wished you hadn't",
    "a friendship that faded without any fight",
    "something you were afraid of that turned out fine",
]

EXPLAIN_AUDIENCE = ["a friend", "a relative who's not technical", "your parent", "a curious kid", "someone who asked at dinner"]
EXPLAIN_TOPICS = [
    "why their car battery keeps dying in the cold",
    "why they keep getting scam texts and what to do",
    "why the sky is blue without hand-waving it",
    "why their phone storage fills up so fast",
    "why bread goes stale faster in the fridge",
]
EXPLAIN_HOWWORKS = ["what a VPN actually does and whether they need one", "how a credit score is calculated", "what 'the cloud' really is", "how noise-canceling headphones work", "what interest on a loan actually means"]

FEEDBACK_PERSON = ["a friend", "a coworker", "a classmate", "someone in a writing group", "a junior teammate"]
FEEDBACK_ARTIFACT = [
    "the personal statement they're sending with a grad-school application",
    "a slide deck they're presenting tomorrow",
    "a short story they posted for critique",
    "a cover letter that's trying too hard",
    "the first draft of a blog post",
    "a resume that buries their best work",
]
FEEDBACK_NOTES = [
    "It's solid but the middle is generic and could be about anyone.",
    "The core idea is strong but it's buried under throat-clearing.",
    "It's good, but the one thing that matters is hard to find.",
    "Be honest about what's not working without crushing them.",
    "They clearly worked hard on it, so lead with what's actually good.",
]
FEEDBACK_JUNIOR = ["a junior teammate", "an intern", "a new hire"]
FEEDBACK_REJECTION = ["their pull request got sent back", "their draft needs another pass", "their proposal didn't get approved"]

TUTOR_MISTAKES = [
    "dropping the negative sign when they distribute in algebra",
    "mixing up 'its' and 'it's' in everything they write",
    "confusing correlation with causation in their essays",
    "forgetting to convert units before plugging into a formula",
]
TUTOR_LEARNER = ["A friend learning to code", "A student in your study group", "Someone you're tutoring"]
TUTOR_TOPICS = ["a function that returns the wrong value", "why their loop runs one time too many", "a proof they can't get started on", "a chemistry problem they keep setting up wrong"]
TUTOR_CONCEPTS = ["the difference between correlation and causation", "how compound interest snowballs", "why the seasons happen", "what a variable actually is in programming", "the three branches of government"]
TUTOR_AUDIENCE = ["a high-schooler", "a curious 10-year-old", "someone studying for a citizenship test", "an adult going back to school"]


# --------------------------------------------------------------------------
# Per-medium composers. Each returns a finished prompt string.
# --------------------------------------------------------------------------

def _email():
    return pick([
        lambda: f"Write a short email to {pick(EMAIL_AUTHORITY)} asking them to {pick(EMAIL_REQUESTS)}. It's been {pick(DURATIONS)} and you're {pick(MOODS_MILD)}, but you want to stay on good terms.",
        lambda: f"Write an email to {pick(EMAIL_ACADEMIC)} asking for {pick(EMAIL_ACADEMIC_ASK)} because {pick(EXCUSES)}. You don't want to sound like you're making it up.",
        lambda: f"Write a follow-up email after {pick(FOLLOWUP_CONTEXT)} that doesn't read like a template.",
        lambda: f"Write an email to {pick(WORKPLACE)} to {pick(WORK_ASKS)}. Keep it brief and don't over-apologize.",
        lambda: f"Write an email to {pick(COMPANIES)} disputing {pick(CHARGES)}. You're in the right, but you know an angry email won't get it fixed.",
        lambda: f"Write an email to {pick(NEIGHBORISH)} about {pick(NEIGHBOR_ISSUES)} without making it hostile.",
    ])()


def _reddit():
    return pick([
        lambda: f"Write a Reddit reply to someone asking {pick(REDDIT_QUESTIONS)}.",
        lambda: f"Write a comment on a thread where someone's asking if they were wrong to {pick(AITA_SITUATIONS)}.",
        lambda: f"Write a reply on r/{pick(SUBREDDITS)} to someone who {pick(REDDIT_OPS)}.",
        lambda: f"Write a Reddit reply gently pushing back on a popular comment saying {pick(BAD_TAKES)}.",
    ])()


def _review():
    return pick([
        lambda: f"Write a review of {pick(PLACES)} that {pick(REVIEW_MIXED)}.",
        lambda: f"Write a review of {pick(PRODUCTS)} that {pick(PRODUCT_MIXED)}.",
        lambda: f"Write a review of {pick(SERVICES)} where {pick(SERVICE_MIXED)}.",
    ])()


def _message():
    return pick([
        lambda: f"Write a text to {pick(FRIENDS)} {pick(MESSAGE_PURPOSES)}.",
        lambda: f"Write a message to {pick(GROUPS)} trying to {pick(GROUP_TASKS)} when nobody's committing.",
        lambda: f"Write a text {pick(HARD_TEXTS)}, without making it weird.",
    ])()


def _essay():
    return pick([
        lambda: f"Write a short personal-essay paragraph about {pick(ESSAY_TOPICS)}.",
        lambda: f"Write a short reflective paragraph about {pick(ESSAY_REFLECT)}.",
    ])()


def _explanation():
    return pick([
        lambda: f"Explain to {pick(EXPLAIN_AUDIENCE)}, casually, {pick(EXPLAIN_TOPICS)}.",
        lambda: f"Explain to {pick(EXPLAIN_AUDIENCE)} {pick(EXPLAIN_HOWWORKS)} without getting too technical.",
    ])()


def _feedback():
    return pick([
        lambda: f"Give {pick(FEEDBACK_PERSON)} feedback on {pick(FEEDBACK_ARTIFACT)}. {pick(FEEDBACK_NOTES)}",
        lambda: f"Reply to {pick(FEEDBACK_JUNIOR)} who asked why {pick(FEEDBACK_REJECTION)}. Point them at the real issue so they catch it next time.",
    ])()


def _tutoring():
    return pick([
        lambda: f"A student keeps {pick(TUTOR_MISTAKES)}. Help them see where it's going wrong without just doing it for them.",
        lambda: f"{pick(TUTOR_LEARNER)} is stuck on {pick(TUTOR_TOPICS)}. Walk them toward it by asking what they've tried, not by handing over the answer.",
        lambda: f"Explain {pick(TUTOR_CONCEPTS)} to {pick(TUTOR_AUDIENCE)} using an everyday example, without sounding like a textbook.",
    ])()


COMPOSERS = {
    "email": _email,
    "reddit": _reddit,
    "review": _review,
    "message": _message,
    "personal essay": _essay,
    "explanation": _explanation,
    "feedback": _feedback,
    "tutoring": _tutoring,
}


def generate(n: int, only: str | None) -> list[dict]:
    mediums = [only] if only else list(COMPOSERS)
    seen: set[str] = set()
    rows: list[dict] = []
    # Cap attempts so a small pool + big --n can't spin forever on dedup.
    attempts = 0
    while len(rows) < n and attempts < n * 50:
        attempts += 1
        medium = pick(mediums)
        prompt = COMPOSERS[medium]()
        if prompt in seen:
            continue
        seen.add(prompt)
        rows.append({"medium": medium, "prompt": prompt})
    return rows


def main() -> None:
    ap = argparse.ArgumentParser(description="Generate diverse writing-task prompts.")
    ap.add_argument("--n", type=int, default=60, help="how many prompts (default 60)")
    ap.add_argument("--seed", type=int, default=None, help="RNG seed for reproducible output")
    ap.add_argument("--medium", choices=list(COMPOSERS), default=None, help="restrict to one medium")
    ap.add_argument("--out", default=None, help="write JSONL to this file instead of stdout")
    ap.add_argument("--append", action="store_true", help="append to questions.jsonl (overrides --out)")
    args = ap.parse_args()

    if args.seed is not None:
        RNG.seed(args.seed)

    rows = generate(args.n, args.medium)
    if len(rows) < args.n:
        # Honest about under-delivery rather than silently returning fewer.
        import sys
        print(f"[note] only {len(rows)} unique prompts available for this selection "
              f"(pool exhausted); add building blocks for more.", file=sys.stderr)

    lines = [json.dumps(r, ensure_ascii=False) for r in rows]
    if args.append:
        with open(QUESTIONS, "a", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
        print(f"appended {len(rows)} prompts to {QUESTIONS}")
    elif args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
        print(f"wrote {len(rows)} prompts to {args.out}")
    else:
        print("\n".join(lines))


if __name__ == "__main__":
    main()
