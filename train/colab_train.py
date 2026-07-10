"""Self-contained Colab training + base-vs-tuned generation for the SLM project.

Mirrors the official Unsloth "Qwen3_(4B)-Instruct" notebook API (same model,
get_chat_template, get_peft_model, SFTConfig, train_on_responses_only markers),
so it runs without API-mismatch surprises.

WHAT IT DOES
  1. loads human_dataset.jsonl (the human educational corpus)
  2. generates BASE answers on held-out education prompts (before training)
  3. QLoRA fine-tunes Qwen3-4B-Instruct on the corpus
  4. generates TUNED answers on the same prompts (after training)
  5. saves the adapter + both output files
Leave with: outputs/adapter/, base_outputs.json, tuned_outputs.json.
Score base vs tuned on Pangram -> does fine-tuning on human text move fraction_ai
off the base model's ~100% AI?

HOW TO RUN IN COLAB
  1. Runtime -> Change runtime type -> GPU (T4 is enough).
  2. Upload to the Colab file panel: this script + human_dataset.jsonl
  3. Run:  !pip install unsloth
  4. Run:  !python colab_train.py
  5. Download: outputs/adapter (zip it), base_outputs.json, tuned_outputs.json
If a free T4 OOMs, set BATCH = 1 below and rerun.
"""

import json
import os

MODEL = "unsloth/Qwen3-4B-Instruct-2507"   # matches the official notebook
MAX_SEQ = 2048
EPOCHS = 2
BATCH = 2
GRAD_ACCUM = 4
OUTDIR = os.getenv("OUTDIR", ".")   # set to a Drive path so outputs survive a disconnect

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

    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=MODEL, max_seq_length=MAX_SEQ,
        load_in_4bit=True, load_in_8bit=False, full_finetuning=False)
    tokenizer = get_chat_template(tokenizer, chat_template="qwen3-instruct")

    def to_msgs(convo):
        return [{"role": "user" if t["from"] in ("human", "user") else "assistant",
                 "content": t["value"]} for t in convo]

    def generate(prompts):
        out = []
        for p in prompts:
            text = tokenizer.apply_chat_template(
                [{"role": "user", "content": p}], tokenize=False, add_generation_prompt=True)
            inp = tokenizer(text, return_tensors="pt").to(model.device)
            o = model.generate(**inp, max_new_tokens=300,
                               temperature=0.7, top_p=0.8, top_k=20)
            gen = tokenizer.decode(o[0][inp["input_ids"].shape[-1]:], skip_special_tokens=True)
            out.append({"prompt": p, "output": gen.strip()})
        return out

    # ---- BASE arm (before any LoRA) ----
    print("generating BASE answers...")
    json.dump(generate(EVAL_PROMPTS), open(os.path.join(OUTDIR, "base_outputs.json"), "w", encoding="utf-8"),
              indent=2, ensure_ascii=False)

    # ---- attach LoRA (matches notebook: r=32) ----
    model = FastLanguageModel.get_peft_model(
        model, r=32,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        lora_alpha=32, lora_dropout=0, bias="none",
        use_gradient_checkpointing="unsloth", random_state=3407)

    def formatting_prompts_func(examples):
        texts = [tokenizer.apply_chat_template(to_msgs(c), tokenize=False, add_generation_prompt=False)
                 for c in examples["conversations"]]
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
    json.dump(generate(EVAL_PROMPTS), open(os.path.join(OUTDIR, "tuned_outputs.json"), "w", encoding="utf-8"),
              indent=2, ensure_ascii=False)

    adapter_dir = os.path.join(OUTDIR, "adapter")
    os.makedirs(adapter_dir, exist_ok=True)
    model.save_pretrained(adapter_dir)
    tokenizer.save_pretrained(adapter_dir)
    print(f"\nDONE. Saved to {os.path.abspath(OUTDIR)}: adapter/, base_outputs.json, tuned_outputs.json")


if __name__ == "__main__":
    main()
