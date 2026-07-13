"""DPO stage 2 -- preference-tune the SFT model on dpo_pairs.jsonl.

Loads the SFT adapter (OUTDIR/adapter -- reliable; merged_16bit can truncate on Drive)
and continues training that LoRA via DPO on the (prompt, chosen, rejected) pairs from
dpo_build_pairs.py -- rewarding
accurate-AND-human answers over vague/AI ones. Then generates DPO eval + regression
answers and auto-converts a GGUF, so you score it exactly like the SFT model:
  accuracy_eval.py --tuned .../dpo_outputs.json --base .../base_outputs_round4.json
  regression_eval.py --tuned .../dpo_regression.json
  + Pangram on dpo_outputs.json  + human_eval.py

RUN IN COLAB (GPU) with colab_train.py present (for the shared prompt lists) and
OUTDIR/dpo_pairs.jsonl in place:  !python dpo_train.py
Tunables via env: DPO_EPOCHS (1), DPO_BETA (0.1), DPO_LR (5e-6).

NOTE: Unsloth/TRL DPO API moves fast; the first run may need a tiny fix (DPOConfig
arg names or the PatchDPOTrainer import). The pipeline shape is the durable part.
"""

import json
import os
import re

MODEL = "unsloth/Qwen3-4B-Instruct-2507"
MAX_SEQ = 2048
OUTDIR = os.getenv("OUTDIR") or (
    "/content/drive/MyDrive/slm_outputs" if os.path.isdir("/content/drive/MyDrive") else ".")
SFT = os.path.join(OUTDIR, "adapter")             # SFT LoRA (reliable; merged_16bit can truncate)
PAIRS = os.path.join(OUTDIR, "dpo_pairs.jsonl")
DPO_EPOCHS = float(os.getenv("DPO_EPOCHS", "1"))
BETA = float(os.getenv("DPO_BETA", "0.1"))
LR = float(os.getenv("DPO_LR", "5e-6"))           # DPO uses a much lower LR than SFT

from colab_train import SYSTEM, EVAL_PROMPTS, REGRESSION_PROMPTS   # shared, single source


def main():
    from unsloth import FastLanguageModel, PatchDPOTrainer
    PatchDPOTrainer()
    from datasets import Dataset
    from trl import DPOTrainer, DPOConfig
    from unsloth.chat_templates import get_chat_template

    if not os.path.exists(PAIRS):
        raise SystemExit(f"missing {PAIRS} -- run dpo_build_pairs.py first.")
    base = SFT if os.path.isdir(SFT) else MODEL
    if base == MODEL:
        print("WARNING: no SFT adapter found -> DPO-ing the untuned base, not the SFT model.")

    # Loading the adapter dir gives base + the SFT LoRA already attached and trainable;
    # DPO continues training THAT LoRA (no second get_peft_model -- that would stack a
    # fresh LoRA on top). If base==MODEL (no adapter) we must attach one to have
    # trainable params. If your Unsloth build loads the adapter read-only and DPOTrainer
    # reports "no trainable parameters", flip NEED_LORA to True.
    NEED_LORA = (base == MODEL)
    model, tok = FastLanguageModel.from_pretrained(
        model_name=base, max_seq_length=MAX_SEQ, load_in_4bit=True)
    tok = get_chat_template(tok, chat_template="qwen3-instruct")
    if NEED_LORA:
        model = FastLanguageModel.get_peft_model(
            model, r=32,
            target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
            lora_alpha=32, lora_dropout=0, bias="none",
            use_gradient_checkpointing="unsloth", random_state=3407)

    # ---- generation (same stopping fix as colab_train) ----
    im_end = tok.convert_tokens_to_ids("<|im_end|>")
    stop_ids = list({i for i in (tok.eos_token_id, im_end) if isinstance(i, int) and i >= 0})
    RUN = re.compile(r"\s*(?:#{2,}\s*(?:human|assistant|user)|<\|im_|\[/?INST\]|</?s>).*$", re.I | re.S)
    THINK = re.compile(r"(?s)<think>.*?</think>\s*")   # drop a reasoning block (hybrid 8B base)

    def _apply(msgs):   # enable_thinking=False for a hybrid base; ignored by non-thinking variants
        try:
            return tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True, enable_thinking=False)
        except TypeError:
            return tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)

    def generate(prompts):
        out = []
        for p in prompts:
            text = _apply([{"role": "system", "content": SYSTEM}, {"role": "user", "content": p}])
            inp = tok(text, return_tensors="pt").to(model.device)
            o = model.generate(**inp, max_new_tokens=512, temperature=0.7, top_p=0.8, top_k=20,
                               repetition_penalty=1.15, no_repeat_ngram_size=3,
                               eos_token_id=stop_ids or None,
                               pad_token_id=tok.pad_token_id if tok.pad_token_id is not None else tok.eos_token_id)
            g = tok.decode(o[0][inp["input_ids"].shape[-1]:], skip_special_tokens=True)
            out.append({"prompt": p, "output": RUN.sub("", THINK.sub("", g)).strip()})
        return out

    def dump(o, f):
        json.dump(o, open(os.path.join(OUTDIR, f), "w", encoding="utf-8"), indent=2, ensure_ascii=False)

    # ---- DPO dataset: prompt = templated system+user; chosen/rejected = responses ----
    def fmt(ex):
        return {"prompt": _apply([{"role": "system", "content": SYSTEM}, {"role": "user", "content": ex["prompt"]}]),
                "chosen": ex["chosen"], "rejected": ex["rejected"]}
    pairs = [json.loads(l) for l in open(PAIRS, encoding="utf-8")]
    ds = Dataset.from_list([fmt(p) for p in pairs])
    print(f"DPO on {len(ds)} pairs | beta={BETA} lr={LR} epochs={DPO_EPOCHS}")

    trainer = DPOTrainer(
        model=model, ref_model=None, tokenizer=tok, train_dataset=ds,
        args=DPOConfig(
            per_device_train_batch_size=1, gradient_accumulation_steps=4, warmup_steps=5,
            num_train_epochs=DPO_EPOCHS, learning_rate=LR, logging_steps=5, optim="adamw_8bit",
            beta=BETA, lr_scheduler_type="linear", seed=3407, output_dir="outputs/dpo",
            report_to="none", max_length=MAX_SEQ, max_prompt_length=1024))
    trainer.train()

    print("generating DPO-tuned answers...")
    dump(generate(EVAL_PROMPTS), "dpo_outputs.json")
    dump(generate(REGRESSION_PROMPTS), "dpo_regression.json")
    dpo_dir = os.path.join(OUTDIR, "adapter_dpo")
    os.makedirs(dpo_dir, exist_ok=True)
    model.save_pretrained(dpo_dir)
    tok.save_pretrained(dpo_dir)

    # ---- auto GGUF (merge -> q8_0, no build) ----
    try:
        merged = os.path.join(OUTDIR, "merged_dpo_16bit")
        model.save_pretrained_merged(merged, tok, save_method="merged_16bit")
        gguf = os.path.join(OUTDIR, "qwen3-human-dpo.Q8_0.gguf")
        os.system("git clone --depth 1 https://github.com/ggerganov/llama.cpp /tmp/llamacpp "
                  "&& pip -q install -r /tmp/llamacpp/requirements.txt")
        rc = os.system(f'python /tmp/llamacpp/convert_hf_to_gguf.py "{merged}" '
                       f'--outfile "{gguf}" --outtype q8_0')
        print("GGUF ->", gguf if rc == 0 else f"convert rc={rc}; merged at {merged}")
    except Exception as e:
        print("auto-GGUF skipped (adapter_dpo still saved):", repr(e)[:200])

    print(f"\nDONE. adapter_dpo/, dpo_outputs.json, dpo_regression.json, "
          f"qwen3-human-dpo.Q8_0.gguf -> {OUTDIR}")


if __name__ == "__main__":
    main()
