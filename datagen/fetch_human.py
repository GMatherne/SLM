"""Fetch real, pre-AI human EDUCATIONAL text from the Hugging Face datasets-server
REST API and build (prompt -> human response) SFT pairs in ShareGPT format.

Sources (all human, pre-ChatGPT, on-domain for tutoring/feedback):
  - ELI5  (sentence-transformers/eli5)          -> friendly explanations
  - Educational StackExchange (per-site configs) -> tutoring + feedback prose
      tutoring: physics, biology, chemistry, matheducators, academia
      feedback: codereview, writing
  - Khan Academy transcripts (iblai/...)        -> patient teacher explanations

Yahoo Answers was dropped: reading samples showed ~1/3 was off-domain (sports
opinions, relationship advice) rather than educational.

We filter to everyday-prose length and light-clean, but do NOT rewrite (rewriting
reintroduces the AI signal). Targets pass Pangram because they ARE human.

Usage:
    python fetch_human.py                 # default volumes
    python fetch_human.py --dry           # print samples, don't write
"""

from __future__ import annotations

import argparse
import json
import os
import re

import requests

BASE = "https://datasets-server.huggingface.co"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "human_dataset.jsonl")
SE = "flax-sentence-embeddings/stackexchange_titlebody_best_voted_answer_jsonl"

SE_TUTORING = ["ell", "english", "physics", "biology", "chemistry", "astronomy",
               "earthscience", "history", "philosophy", "economics", "linguistics",
               "cogsci", "health", "music", "hsm", "matheducators", "academia"]
SE_FEEDBACK = ["writing"]  # codereview dropped: code-laden, and we want prose only

_URL = re.compile(r"https?://\S+|www\.\S+")
_IMG_REF = re.compile(r"\b(see|as shown|refer to)\s+(the\s+)?(image|images|figure|fig|diagram|picture|photo|attachment|above|below|following)\b", re.I)


def _shouty(t: str) -> bool:
    alpha = sum(c.isalpha() for c in t)
    return alpha > 0 and sum(c.isupper() for c in t) / alpha > 0.3


def clean(text: str) -> str:
    text = text.replace("\r", " ").replace("<br />", "\n").strip()
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def clean_vtt(raw: str) -> str:
    """Strip WebVTT captions to plain prose."""
    out = []
    for ln in raw.splitlines():
        ln = ln.strip()
        if not ln or ln.startswith(("WEBVTT", "Kind:", "Language:")) or "-->" in ln or re.match(r"^\d+$", ln):
            continue
        out.append(re.sub(r"^-\s*(\[[^\]]+\]\s*)?", "", ln))  # strip caption dash / speaker tag
    return re.sub(r"\s+", " ", " ".join(out)).strip()


def first_chunk(text: str, max_words: int = 180) -> str:
    """Take the opening as a self-contained explanation, cut at a sentence end."""
    words = text.split()
    if len(words) <= max_words:
        chunk = text
    else:
        chunk = " ".join(words[:max_words])
        cut = max(chunk.rfind(". "), chunk.rfind("? "), chunk.rfind("! "))
        if cut > 200:
            chunk = chunk[:cut + 1]
    return chunk.strip()


def ok(prompt: str, resp: str) -> bool:
    if not prompt or not resp:
        return False
    words = len(resp.split())
    if words < 25 or words > 300:
        return False
    if _URL.search(resp) or _IMG_REF.search(resp) or _shouty(resp):
        return False
    if "�" in resp:
        return False
    if "```" in resp or "{" in resp or "}" in resp:          # code blocks / braces
        return False
    if "$" in resp or "\\" in resp:                          # LaTeX / escapes
        return False
    if re.search(r"==|!=|\+\+|::|\bprintf\b|console\.|#include|</?[a-z]+>", resp):  # code-ish
        return False
    if sum(c.isascii() for c in resp) / max(1, len(resp)) < 0.97:
        return False
    return True


def api_rows(dataset, config, split, offsets):
    for off in offsets:
        try:
            r = requests.get(f"{BASE}/rows", params={"dataset": dataset, "config": config,
                             "split": split, "offset": off, "length": 100}, timeout=60).json()
        except Exception as e:
            print(f"    {dataset}/{config} off {off}: {type(e).__name__}"); continue
        for row in r.get("rows", []):
            yield row["row"]


def trunc_prompt(p: str, max_words: int = 90) -> str:
    w = p.split()
    return p if len(w) <= max_words else " ".join(w[:max_words])


def collect(cap_eli5, cap_se_site, cap_khan):
    rows, seen = [], set()

    def add(source, prompt, resp):
        prompt, resp = clean(trunc_prompt(prompt)), clean(resp)
        if not ok(prompt, resp):
            return False
        key = resp[:60].lower()
        if key in seen:
            return False
        seen.add(key)
        rows.append({"source": source, "prompt": prompt, "response": resp})
        return True

    print("ELI5 ...")
    n = 0
    for d in api_rows("sentence-transformers/eli5", "pair", "train", list(range(0, 300000, 12000))):
        if n >= cap_eli5: break
        if add("eli5", d.get("question", ""), d.get("answer", "")): n += 1
    print(f"  kept {n}")

    for site in SE_TUTORING + SE_FEEDBACK:
        reg = "feedback" if site in SE_FEEDBACK else "tutoring"
        n = 0
        for d in api_rows(SE, site, "train", [0, 2000, 6000, 14000, 30000, 60000]):
            if n >= cap_se_site: break
            if add(f"se-{site}({reg})", d.get("title_body", ""), d.get("upvoted_answer", "")): n += 1
        print(f"SE {site} [{reg}]: kept {n}")

    print("Khan ...")
    n = 0
    for d in api_rows("iblai/ibl-khanacademy-transcripts", "default", "train", list(range(0, 7700, 300))):
        if n >= cap_khan: break
        snip = first_chunk(clean_vtt(d.get("content", "")))
        title = (d.get("title") or "").strip()
        if title and add("khan", f"Can you explain {title.lower()}?", snip):
            n += 1
    print(f"  kept {n}")
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--eli5", type=int, default=250)
    ap.add_argument("--se-per-site", type=int, default=50)
    ap.add_argument("--khan", type=int, default=300)
    ap.add_argument("--dry", action="store_true")
    args = ap.parse_args()

    rows = collect(args.eli5, args.se_per_site, args.khan)
    from collections import Counter
    print("\nby source:", dict(Counter(r["source"] for r in rows)))
    print("total:", len(rows))
    for r in rows[:2] + rows[-2:]:
        print(f"\n[{r['source']}] Q: {r['prompt'][:80]}\n           A: {r['response'][:160]}")

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
