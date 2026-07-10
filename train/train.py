"""QLoRA fine-tune of Qwen3-4B-Instruct on the human educational corpus, using
Unsloth. Consumes datagen/data/human_dataset.jsonl (ShareGPT) and writes a LoRA
adapter that the eval harness loads onto the same base.

For Colab, prefer colab_train.py (self-contained; also generates base/tuned
answers for the Pangram eval). This is the plain-box equivalent.

Must run on a GPU. 4B QLoRA fits a free Colab T4 (16GB); it will NOT fit an 8GB
local card -- use the cloud.

Setup on a fresh GPU box:
    pip install unsloth
    # (unsloth pulls compatible torch/transformers/trl/peft/datasets)

Run:
    python train.py

The key rule from the brief: fix a disappointing model in the DATA, not here.
Don't tune these hyperparameters to paper over a data problem. The only knob you
should touch often is EPOCHS (watch for overfitting: if train loss dives toward
0 and outputs start echoing training examples, drop it).
"""

from __future__ import annotations

import json
import os

# --------------------------------------------------------------------------- #
# Config -- keep BASE_MODEL identical to eval/config.py so the adapter loads
# cleanly onto the model the eval harness evaluates.
# --------------------------------------------------------------------------- #
BASE_MODEL = os.getenv("BASE_MODEL", "unsloth/Qwen3-4B-Instruct-2507")
MAX_SEQ_LEN = int(os.getenv("MAX_SEQ_LEN", "2048"))

HERE = os.path.dirname(os.path.abspath(__file__))
DATASET = os.getenv("DATASET", os.path.join(HERE, "..", "datagen", "data", "human_dataset.jsonl"))
ADAPTER_OUT = os.getenv("ADAPTER_OUT", os.path.join(HERE, "..", "outputs", "adapter"))

# LoRA / training knobs. Defaults are the Unsloth-recommended starting point.
LORA_RANK = 16
LORA_ALPHA = 16
EPOCHS = float(os.getenv("EPOCHS", "2"))        # 1-3; small style dataset -> 2 is a fine start
LEARNING_RATE = 2e-4
BATCH_SIZE = 2
GRAD_ACCUM = 4                                    # effective batch = BATCH_SIZE * GRAD_ACCUM = 8
SEED = 3407


def load_conversations(path: str):
    """Read the ShareGPT jsonl into HF Dataset rows keyed 'conversations'."""
    if not os.path.exists(path):
        raise SystemExit(
            f"No dataset at {path}. Run datagen/fetch_human.py first to create it."
        )
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    if len(rows) < 50:
        print(f"WARNING: only {len(rows)} examples. Style SFT usually wants a few "
              f"hundred clean rows; results may be weak.")
    print(f"Loaded {len(rows)} training conversations from {path}")
    return rows


def main():
    import torch
    from datasets import Dataset
    from unsloth import FastLanguageModel
    from unsloth.chat_templates import train_on_responses_only
    from trl import SFTConfig, SFTTrainer

    # ---- model (4-bit QLoRA) --------------------------------------------- #
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=BASE_MODEL,
        max_seq_length=MAX_SEQ_LEN,
        dtype=None,             # auto (bf16 where supported)
        load_in_4bit=True,
    )
    model = FastLanguageModel.get_peft_model(
        model,
        r=LORA_RANK,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                        "gate_proj", "up_proj", "down_proj"],
        lora_alpha=LORA_ALPHA,
        lora_dropout=0,
        bias="none",
        use_gradient_checkpointing="unsloth",
        random_state=SEED,
    )

    # ---- data ------------------------------------------------------------ #
    raw = load_conversations(DATASET)

    def to_text(example):
        # map ShareGPT from/value -> chat messages, render with the model's own
        # template. enable_thinking=False: we want direct conversational replies,
        # not Qwen3 <think> blocks.
        msgs = []
        for turn in example["conversations"]:
            role = "user" if turn["from"] in ("human", "user") else "assistant"
            msgs.append({"role": role, "content": turn["value"]})
        try:
            text = tokenizer.apply_chat_template(
                msgs, tokenize=False, add_generation_prompt=False, enable_thinking=False)
        except TypeError:
            # tokenizers without the enable_thinking kwarg
            text = tokenizer.apply_chat_template(
                msgs, tokenize=False, add_generation_prompt=False)
        return {"text": text}

    dataset = Dataset.from_list(raw).map(to_text)

    # ---- trainer --------------------------------------------------------- #
    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=dataset,
        args=SFTConfig(
            dataset_text_field="text",
            max_seq_length=MAX_SEQ_LEN,
            per_device_train_batch_size=BATCH_SIZE,
            gradient_accumulation_steps=GRAD_ACCUM,
            warmup_steps=5,
            num_train_epochs=EPOCHS,
            learning_rate=LEARNING_RATE,
            logging_steps=1,
            optim="adamw_8bit",
            weight_decay=0.01,
            lr_scheduler_type="linear",
            seed=SEED,
            output_dir=os.path.join(HERE, "..", "outputs", "checkpoints"),
            report_to="none",
        ),
    )

    # Train only on the assistant's replies, so the model learns to PRODUCE the
    # voice rather than to model the input tasks.
    trainer = train_on_responses_only(
        trainer,
        instruction_part="<|im_start|>user\n",
        response_part="<|im_start|>assistant\n",
    )

    trainer.train()

    # ---- save adapter (eval/config.py ADAPTER_PATH points here) ---------- #
    os.makedirs(ADAPTER_OUT, exist_ok=True)
    model.save_pretrained(ADAPTER_OUT)
    tokenizer.save_pretrained(ADAPTER_OUT)
    print(f"\nSaved LoRA adapter -> {os.path.abspath(ADAPTER_OUT)}")

    # ---- quick eyeball --------------------------------------------------- #
    FastLanguageModel.for_inference(model)
    msgs = [{"role": "user", "content": "Write a short email to your landlord asking them to fix a leaking faucet."}]
    try:
        inputs = tokenizer.apply_chat_template(
            msgs, add_generation_prompt=True, return_tensors="pt", enable_thinking=False).to(model.device)
    except TypeError:
        inputs = tokenizer.apply_chat_template(
            msgs, add_generation_prompt=True, return_tensors="pt").to(model.device)
    out = model.generate(inputs, max_new_tokens=300, temperature=0.7, top_p=0.9, do_sample=True)
    print("\n--- sample generation ---")
    print(tokenizer.decode(out[0][inputs.shape[-1]:], skip_special_tokens=True))


if __name__ == "__main__":
    main()
