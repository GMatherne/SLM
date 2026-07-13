"""DPO stage 1 -- build preference pairs from the SFT model + the judge.

For each of N training prompts, sample K candidate answers from the current SFT
model, have the judge rate each on ACCURACY (0-5) and READS_HUMAN (0-2), and keep a
(chosen, rejected) pair only when there is a clearly-better answer that is ITSELF
good (accurate AND human). That pair is the preference signal DPO optimizes:
accurate-and-human over vague/AI -- the frontier plain SFT can't target.

HONEST LIMITS: human-ness here is the JUDGE's reads_human (a proxy -- we can't call
Pangram at scale on this plan); Pangram stays the held-out validator on the final
model. DPO only reinforces what the model can already produce.

RUN IN COLAB (GPU), AFTER an SFT run left OUTDIR/adapter (colab_train.py saves it).
Set the judge gateway env in a Colab cell first, then run:
  import os
  os.environ['OPENAI_API_KEY']  = 'tfy_...'
  os.environ['OPENAI_BASE_URL'] = 'https://<org>.truefoundry.cloud/api/llm'
  os.environ['JUDGE_MODEL']     = 'openai-group/gpt-5'
  !python dpo_build_pairs.py

Writes OUTDIR/dpo_pairs.jsonl ({"prompt","chosen","rejected"}) -- INSPECT it before
dpo_train.py. Candidates cache to OUTDIR/dpo_candidates.json so a re-run resumes.

NOTE: Unsloth/TRL APIs move fast; the first run may need a tiny fix (model-load or
generate kwargs). The judge/pairing logic is plain python and is the part that matters.
"""

import json
import os
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

MODEL = "unsloth/Qwen3-4B-Instruct-2507"
MAX_SEQ = 2048
OUTDIR = os.getenv("OUTDIR") or (
    "/content/drive/MyDrive/slm_outputs" if os.path.isdir("/content/drive/MyDrive") else ".")
SFT = os.path.join(OUTDIR, "adapter")          # the SFT LoRA -- reliable; merged_16bit can be
#                                                truncated on Drive. from_pretrained(adapter dir)
#                                                loads base + adapter.
N_PROMPTS = int(os.getenv("DPO_PROMPTS", "120"))
K = int(os.getenv("DPO_K", "4"))               # candidates per prompt
MAX_NEW = int(os.getenv("DPO_MAXNEW", "512"))  # cap per candidate; lower = faster
MARGIN = int(os.getenv("DPO_MARGIN", "2"))     # min (acc+human) gap between chosen and rejected
JUDGE_MODEL = os.getenv("JUDGE_MODEL", "gpt-4o")

SYSTEM = ("You are a helpful AI tutor. You explain concepts clearly and accurately, "
          "covering the actual mechanism or reasoning rather than a vague summary. You "
          "help with writing and correct mistakes, in natural, plain language. You are "
          "an AI assistant -- you never claim to be a human, a person, or a product. "
          "Never cite specific studies, papers, books, articles, authors, DOIs, or web "
          "links, and never invent a source or title -- explain things in your own "
          "words. Do not end with sign-offs like \"hope this helps.\"")

_JUDGE = """You are grading a tutor's answer on two independent axes.

QUESTION:
{q}

ANSWER:
\"\"\"{a}\"\"\"

- accuracy (0-5): factual correctness/soundness (5 fully correct; 3 mostly right, one
  clear error; 0 nonsense or fabricated).
- reads_human (0-2): 0 = clearly AI-generated (generic, evenly-paced, padded, hedged);
  1 = plausibly human; 2 = convincingly a real person's writing.

Respond with ONLY JSON: {{"accuracy": <0-5>, "reads_human": <0-2>}}"""


def judge(q, a):
    from openai import OpenAI
    client = OpenAI(base_url=os.getenv("OPENAI_BASE_URL") or None, timeout=120)
    r = client.chat.completions.create(
        model=JUDGE_MODEL, response_format={"type": "json_object"},
        messages=[{"role": "user", "content": _JUDGE.format(q=q, a=a)}])
    t = r.choices[0].message.content
    d = json.loads(t[t.find("{"): t.rfind("}") + 1])
    return float(d.get("accuracy", 0) or 0), float(d.get("reads_human", 0) or 0)


def main():
    import torch
    from unsloth import FastLanguageModel
    from unsloth.chat_templates import get_chat_template

    if not os.path.exists("human_dataset.jsonl"):
        raise SystemExit("Upload human_dataset.jsonl (for the prompt pool).")
    if not os.path.isdir(SFT):
        raise SystemExit(f"missing {SFT} -- run colab_train.py first (it saves the SFT adapter here).")

    model, tok = FastLanguageModel.from_pretrained(
        model_name=SFT, max_seq_length=MAX_SEQ, load_in_4bit=True)
    tok = get_chat_template(tok, chat_template="qwen3-instruct")
    FastLanguageModel.for_inference(model)
    im_end = tok.convert_tokens_to_ids("<|im_end|>")
    stop_ids = list({i for i in (tok.eos_token_id, im_end) if isinstance(i, int) and i >= 0})
    RUN = re.compile(r"\s*(?:#{2,}\s*(?:human|assistant|user)|<\|im_|\[/?INST\]|</?s>).*$", re.I | re.S)
    THINK = re.compile(r"(?s)<think>.*?</think>\s*")   # drop a reasoning block (hybrid 8B base)

    def _apply(msgs):   # enable_thinking=False for a hybrid base; ignored by non-thinking variants
        try:
            return tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True, enable_thinking=False)
        except TypeError:
            return tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)

    # Reuse the corpus artifact filters on each candidate so a citation / sign-off / figure
    # ref that still slips through can't become a "chosen" pair (belt-and-braces on top of
    # the clean-trained model). No-op if fetch_human.py isn't uploaded alongside.
    try:
        import sys as _sys
        _sys.path.insert(0, ".")
        from fetch_human import _deref as _dref, _HARD_REF as _HR, _YEAR_CITE as _YC, _FIGURE as _FG

        def _corpus_clean(t):
            t = _dref(t)
            return "" if (_HR.search(t) or _YC.search(t) or _FG.search(t)) else t
    except Exception as _e:
        print("(candidate corpus-filter off:", str(_e)[:60] + ")")

        def _corpus_clean(t):
            return t

    def _post(g):       # strip thinking + turn markers, then the corpus artifact filters
        return _corpus_clean(RUN.sub("", THINK.sub("", g)).strip())

    # prompt pool = training-corpus prompts (disjoint from the held-out EVAL_PROMPTS)
    prompts = []
    for line in open("human_dataset.jsonl", encoding="utf-8"):
        conv = json.loads(line)["conversations"]
        prompts.append(next(x["value"] for x in conv if x["from"] in ("human", "user")))
        if len(prompts) >= N_PROMPTS:
            break

    cand_path = os.path.join(OUTDIR, "dpo_candidates.json")
    if os.path.exists(cand_path):
        cands = json.load(open(cand_path, encoding="utf-8"))
        print(f"resumed {len(cands)} cached candidate sets")
    else:
        cands = []
        for n, q in enumerate(prompts, 1):
            text = _apply([{"role": "system", "content": SYSTEM}, {"role": "user", "content": q}])
            inp = tok(text, return_tensors="pt").to(model.device)
            plen = inp["input_ids"].shape[-1]
            gkw = dict(max_new_tokens=MAX_NEW, do_sample=True,
                       temperature=0.9, top_p=0.95, top_k=40,
                       repetition_penalty=1.15, no_repeat_ngram_size=3,
                       eos_token_id=stop_ids or None,
                       pad_token_id=tok.pad_token_id if tok.pad_token_id is not None else tok.eos_token_id)
            try:
                # all K candidates in ONE batched call -- the GPU samples them together
                # instead of K sequential generate() calls (~2-3x faster on a T4).
                # do_sample=True makes the K returned sequences independent draws.
                o = model.generate(**inp, num_return_sequences=K, **gkw)
                outs = [_post(tok.decode(o[j][plen:], skip_special_tokens=True)) for j in range(K)]
            except RuntimeError as e:      # CUDA OOM on the K-batch -> fall back to 1-at-a-time
                torch.cuda.empty_cache()
                print(f"  batch gen fell back to sequential ({str(e)[:60]})")
                outs = []
                for _ in range(K):
                    o = model.generate(**inp, **gkw)
                    outs.append(_post(tok.decode(o[0][plen:], skip_special_tokens=True)))
            cands.append({"prompt": q, "candidates": outs})
            if n % 10 == 0:
                print(f"  generated {n}/{len(prompts)}")
                json.dump(cands, open(cand_path, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
        json.dump(cands, open(cand_path, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    print(f"candidates: {len(cands)} prompts x {K}")

    # judge every candidate in parallel -> (accuracy, reads_human)
    jobs = [(pi, ci, c["prompt"], a) for pi, c in enumerate(cands)
            for ci, a in enumerate(c["candidates"]) if a and len(a.split()) >= 20]
    scores = {}
    print(f"judging {len(jobs)} candidates via {JUDGE_MODEL}...")
    with ThreadPoolExecutor(max_workers=8) as ex:
        futs = {ex.submit(lambda j: (j[0], j[1], judge(j[2], j[3])), j): j for j in jobs}
        for fut in as_completed(futs):
            try:
                pi, ci, sc = fut.result()
                scores[(pi, ci)] = sc
            except Exception as e:
                print("  judge error (skipped):", str(e)[:100])

    # form pairs: chosen = best (accuracy + reads_human) that clears a quality FLOOR;
    # rejected = worst, with a clear MARGIN. Skip prompts without a good, clear winner.
    pairs = []
    for pi, c in enumerate(cands):
        scored = [(ci, scores[(pi, ci)]) for ci in range(len(c["candidates"])) if (pi, ci) in scores]
        if len(scored) < 2:
            continue
        scored.sort(key=lambda x: x[1][0] + x[1][1])   # by accuracy + reads_human
        (lo_i, lo), (hi_i, hi) = scored[0], scored[-1]
        if (hi[0] + hi[1]) - (lo[0] + lo[1]) >= MARGIN and hi[0] >= 3 and hi[1] >= 1:
            pairs.append({"prompt": c["prompt"],
                          "chosen": c["candidates"][hi_i], "rejected": c["candidates"][lo_i]})
    out = os.path.join(OUTDIR, "dpo_pairs.jsonl")
    with open(out, "w", encoding="utf-8") as f:
        for p in pairs:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")
    print(f"\nwrote {len(pairs)} preference pairs -> {out}\nINSPECT them, then run dpo_train.py")


if __name__ == "__main__":
    main()
