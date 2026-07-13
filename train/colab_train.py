"""Self-contained Colab training + base-vs-tuned generation for the SLM project.

Mirrors the official Unsloth "Qwen3_(4B)-Instruct" notebook API (same model,
get_chat_template, get_peft_model, SFTConfig, train_on_responses_only markers),
so it runs without API-mismatch surprises.

WHAT IT DOES (all outputs to OUTDIR, auto-Drive if mounted)
  1. loads human_dataset.jsonl (the human educational corpus)
  2. generates BASE answers on the eval + regression prompts (before training)
  3. QLoRA fine-tunes Qwen3-4B-Instruct on the corpus
  4. generates TUNED answers on the same prompts (after training)
  5. saves the LoRA adapter
  6. AUTO-converts a merged model to qwen3-human.Q8_0.gguf (ready for Ollama)
Leave with: adapter/, base_outputs.json, tuned_outputs.json, base_regression.json,
tuned_regression.json, qwen3-human.Q8_0.gguf.
Then score: Pangram (human-ness) + eval/accuracy_eval.py + eval/regression_eval.py.

HOW TO RUN IN COLAB
  1. Runtime -> Change runtime type -> GPU (T4 is enough).
  2. Upload to the Colab file panel: this script + human_dataset.jsonl
     (regression prompts are inlined -- nothing else to upload).
  3. Run:  !pip install unsloth
  4. Run:  !python colab_train.py
  5. Download from OUTDIR: qwen3-human.Q8_0.gguf, the *_outputs.json / *_regression.json,
     and adapter/ (zip it). The .gguf drops straight next to train/Modelfile.
If a free T4 OOMs, set BATCH = 1 below and rerun.
"""

import json
import os
import re

# Configurable via env so a larger base model is a one-line switch (no code edit):
#   MODEL=unsloth/Qwen3-8B BATCH=1 python colab_train.py     # 8B QLoRA (see README notes)
# NOTE for 8B: Qwen3-8B is a HYBRID (thinking) model, unlike the 4B-Instruct-2507
# non-thinking variant we default to. To avoid <think> blocks either (a) use a
# non-thinking instruct variant if one exists, or (b) pass enable_thinking=False to the
# apply_chat_template calls below. The GGUF merge also needs >16GB RAM at 8B (Colab Pro).
MODEL = os.getenv("MODEL", "unsloth/Qwen3-4B-Instruct-2507")   # 4B non-thinking instruct
MAX_SEQ = int(os.getenv("MAX_SEQ", "2048"))
EPOCHS = int(os.getenv("EPOCHS", "2"))
BATCH = int(os.getenv("BATCH", "2"))            # drop to 1 for an 8B model on a 15GB T4
GRAD_ACCUM = int(os.getenv("GRAD_ACCUM", "4"))
# Where outputs go. Auto-uses Google Drive if it's mounted (so outputs survive a
# disconnect), else an explicit OUTDIR env, else the current folder.
OUTDIR = os.getenv("OUTDIR") or (
    "/content/drive/MyDrive/slm_outputs" if os.path.isdir("/content/drive/MyDrive") else ".")

# Assistant-identity system prompt, prepended to every training conversation AND
# to generation, so the model learns to answer AS an AI tutor -- not to confabulate
# a human/product identity (round-3 chat claimed to be "Replika"). Keep in sync
# with the SYSTEM block in train/Modelfile.
SYSTEM = ("You are a helpful AI tutor. You explain concepts clearly and accurately, "
          "covering the actual mechanism or reasoning rather than a vague summary. You "
          "help with writing and correct mistakes, in natural, plain language. You are "
          "an AI assistant -- you never claim to be a human, a person, or a product. "
          "Never cite specific studies, papers, books, articles, authors, DOIs, or web "
          "links, and never invent a source or title -- explain things in your own "
          "words. Do not end with sign-offs like \"hope this helps.\"")

# Held-out education prompts (NOT in the training data) -- the eval set.
EVAL_PROMPTS = [
    "Why does the ocean look blue?",
    "Can you explain how vaccines work?",
    "What causes the seasons to change?",
    "Explain what compound interest is and why it matters.",
    "Why do we get hiccups?",
    "How does the internet send a message from my computer to another one?",
    "Why does bread rise when you bake it?",
    "What is the difference between weather and climate?",
    "How do noise-cancelling headphones work?",
    "Why does metal feel colder than wood at the same temperature?",
    "Can you explain what a black hole is without the heavy math?",
    "Why do onions make you cry when you cut them?",
    # --- round-4 behaviours: correction + essay/writing help (items 12-15) ---
    "My textbook says humans only use 10% of their brains. Is that true?",
    "A friend told me lightning never strikes the same place twice. Is that accurate?",
    "Here's the opening of my college essay: \"Ever since I was young, I have always "
    "loved science because it is very interesting and fun.\" How can I make it stronger?",
    "Make the case that public libraries are still essential in the digital age.",
]

# Regression prompts (off-domain / format-constrained) -- INLINED so base/tuned
# regression outputs are ALWAYS generated (no separate upload to forget). Keep this
# list in sync + same ORDER as eval/regression_prompts.jsonl (regression_eval.py
# matches by index for the pass-criterion of each task).
REGRESSION_PROMPTS = [
    "Write a Python function is_prime(n) that returns True if n is prime.",
    "What is 17 times 23? Give just the number.",
    "Summarize this in one sentence: The city council voted 6-3 to approve the new bike "
    "lane project after months of debate, with construction set to begin in the spring.",
    "Return the three primary colors as a JSON array of strings, nothing else.",
    "In one word, what is the capital of Japan?",
    "Write a one-sentence professional email asking to reschedule Friday's meeting to Monday.",
    "Write a two-line rhyming couplet about the sea.",
    "A movie starts at 7:15 pm and runs 105 minutes. What time does it end?",
    "Explain what a noun is in exactly one sentence.",
    "Just the answer, no explanation: what year did the Berlin Wall fall?",
    "Give a markdown table with two rows, Mercury and Earth, and their number of moons.",
    "Is the sentiment of this review positive or negative? 'The food was cold and the "
    "service was slow.' Answer with one word.",
]


def main():
    from unsloth import FastLanguageModel
    from unsloth.chat_templates import get_chat_template, train_on_responses_only
    from datasets import Dataset
    from trl import SFTConfig, SFTTrainer

    if not os.path.exists("human_dataset.jsonl"):
        raise SystemExit("Upload human_dataset.jsonl to the Colab file panel first.")
    rows = [json.loads(l) for l in open("human_dataset.jsonl", encoding="utf-8")]
    print(f"training examples: {len(rows)}")
    os.makedirs(OUTDIR, exist_ok=True)
    print(f"outputs -> {os.path.abspath(OUTDIR)}")

    # REGRESSION set (inlined -> always generated): base+tuned answers on off-domain /
    # format-constrained prompts, so eval/regression_eval.py can measure whether
    # fine-tuning broke general ability (over-explaining, wrong format, register bleed).
    reg_prompts = REGRESSION_PROMPTS
    print(f"regression prompts: {len(reg_prompts)}")

    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=MODEL, max_seq_length=MAX_SEQ,
        load_in_4bit=True, load_in_8bit=False, full_finetuning=False)
    tokenizer = get_chat_template(tokenizer, chat_template="qwen3-instruct")

    # enable_thinking=False = the "hard switch" that makes a HYBRID base (Qwen3-8B)
    # behave as a non-thinking instruct model (no <think> blocks). It is harmlessly
    # ignored by non-thinking variants (4B-Instruct-2507), so this stays backward-
    # compatible; the try/except covers any template that rejects the kwarg.
    def _apply(msgs, add_gen):
        try:
            return tokenizer.apply_chat_template(msgs, tokenize=False,
                                                 add_generation_prompt=add_gen, enable_thinking=False)
        except TypeError:
            return tokenizer.apply_chat_template(msgs, tokenize=False, add_generation_prompt=add_gen)

    def to_msgs(convo):
        return [{"role": "system", "content": SYSTEM}] + [
            {"role": "user" if t["from"] in ("human", "user") else "assistant",
             "content": t["value"]} for t in convo]

    # Stop at the ChatML turn end so generation can't overrun into a fabricated next
    # turn (round-4 #15 hallucinated a whole "### Human:/### Assistant:" debate). The
    # _RUNAWAY trim is a belt-and-braces net for any turn marker leaked as plain text.
    _im_end = tokenizer.convert_tokens_to_ids("<|im_end|>")
    _stop_ids = list({i for i in (tokenizer.eos_token_id, _im_end) if isinstance(i, int) and i >= 0})
    _RUNAWAY = re.compile(
        r"\s*(?:#{2,}\s*(?:human|assistant|user)|<\|im_|\[/?INST\]|</?s>).*$", re.I | re.S)

    def generate(prompts):
        out = []
        for p in prompts:
            text = _apply([{"role": "system", "content": SYSTEM}, {"role": "user", "content": p}], True)
            inp = tokenizer(text, return_tensors="pt").to(model.device)
            # repetition_penalty/no_repeat_ngram_size cut restating; eos_token_id makes it
            # STOP at the turn boundary (it was overrunning at max_new_tokens=512).
            o = model.generate(**inp, max_new_tokens=512,
                               temperature=0.7, top_p=0.8, top_k=20,
                               repetition_penalty=1.15, no_repeat_ngram_size=3,
                               eos_token_id=_stop_ids or None,
                               pad_token_id=(tokenizer.pad_token_id
                                             if tokenizer.pad_token_id is not None else tokenizer.eos_token_id))
            gen = tokenizer.decode(o[0][inp["input_ids"].shape[-1]:], skip_special_tokens=True)
            gen = re.sub(r"(?s)<think>.*?</think>\s*", "", gen)   # drop a thinking block if a hybrid base emits one
            gen = _RUNAWAY.sub("", gen).strip()   # cut any leaked turn-continuation
            out.append({"prompt": p, "output": gen})
        return out

    def dump(obj, fname):
        json.dump(obj, open(os.path.join(OUTDIR, fname), "w", encoding="utf-8"),
                  indent=2, ensure_ascii=False)

    # ---- BASE arm (before any LoRA) ----
    print("generating BASE answers...")
    dump(generate(EVAL_PROMPTS), "base_outputs.json")
    if reg_prompts:
        dump(generate(reg_prompts), "base_regression.json")

    # ---- attach LoRA (matches notebook: r=32) ----
    model = FastLanguageModel.get_peft_model(
        model, r=32,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        lora_alpha=32, lora_dropout=0, bias="none",
        use_gradient_checkpointing="unsloth", random_state=3407)

    def formatting_prompts_func(examples):
        texts = [_apply(to_msgs(c), False) for c in examples["conversations"]]
        return {"text": texts}

    dataset = Dataset.from_list(rows).map(formatting_prompts_func, batched=True)

    trainer = SFTTrainer(
        model=model, tokenizer=tokenizer, train_dataset=dataset, eval_dataset=None,
        args=SFTConfig(
            dataset_text_field="text",
            per_device_train_batch_size=BATCH, gradient_accumulation_steps=GRAD_ACCUM,
            warmup_steps=5, num_train_epochs=EPOCHS, learning_rate=2e-4,
            logging_steps=5, optim="adamw_8bit", weight_decay=0.001,
            lr_scheduler_type="linear", seed=3407,
            output_dir="outputs/checkpoints", report_to="none"))
    trainer = train_on_responses_only(
        trainer, instruction_part="<|im_start|>user\n", response_part="<|im_start|>assistant\n")
    trainer.train()

    # ---- TUNED arm (after training) ----
    print("generating TUNED answers...")
    dump(generate(EVAL_PROMPTS), "tuned_outputs.json")
    if reg_prompts:
        dump(generate(reg_prompts), "tuned_regression.json")

    adapter_dir = os.path.join(OUTDIR, "adapter")
    os.makedirs(adapter_dir, exist_ok=True)
    model.save_pretrained(adapter_dir)
    tokenizer.save_pretrained(adapter_dir)

    # ---- AUTOMATIC GGUF for Ollama: merge to 16-bit, then llama.cpp -> q8_0 ----
    # No manual .safetensors step. Uses the RELIABLE path: q8_0 conversion is pure
    # python (convert_hf_to_gguf.py), so there's no cmake build to OOM/stall -- the
    # old save_pretrained_gguf(q4_k_m) kept dying mid-convert. Leaves a ready-to-run
    # qwen3-human.Q8_0.gguf (the exact name train/Modelfile's FROM expects) on Drive.
    try:
        merged = os.path.join(OUTDIR, "merged_16bit")
        print("merging to 16-bit ->", merged)
        model.save_pretrained_merged(merged, tokenizer, save_method="merged_16bit")
        gguf = os.path.join(OUTDIR, "qwen3-human.Q8_0.gguf")
        print("converting to q8_0 GGUF (no build) ->", gguf)
        os.system("git clone --depth 1 https://github.com/ggerganov/llama.cpp /tmp/llamacpp "
                  "&& pip -q install -r /tmp/llamacpp/requirements.txt")
        rc = os.system(f'python /tmp/llamacpp/convert_hf_to_gguf.py "{merged}" '
                       f'--outfile "{gguf}" --outtype q8_0')
        print("GGUF ->", gguf if rc == 0 else f"convert rc={rc}; merged model at {merged} (convert manually)")
    except Exception as e:
        print("auto-GGUF skipped (adapter+merged still saved):", repr(e)[:200])

    print(f"\nDONE. Saved to {os.path.abspath(OUTDIR)}: adapter/, base_outputs.json, "
          f"tuned_outputs.json, base_regression.json, tuned_regression.json, "
          f"qwen3-human.Q8_0.gguf (auto-converted)")


if __name__ == "__main__":
    main()
