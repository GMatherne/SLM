# Training

QLoRA fine-tune of Qwen3-4B-Instruct on the human educational corpus, via Unsloth.
Input: `datagen/data/dataset.jsonl`. Output: a LoRA adapter at `outputs/adapter`.

## Where to run: 4B needs cloud

Your local RTX 4060 laptop has **8GB VRAM**. That's enough to *run* a 4-bit 4B
model (Ollama does this fine), but **not enough to QLoRA-train 4B** — training
adds gradients, optimizer state, and activations and realistically wants
~10-12GB, so 8GB will OOM. Train 4B on a **cloud GPU** (Modal / RunPod / Colab
with an L4 or A100).

(If you ever want fully-local training, drop to `BASE_MODEL=Qwen/Qwen3-1.7B` and
it fits your 8GB card — but then re-pull `qwen3:1.7b` in Ollama and set the eval
to match, so all three stay on the same base.)

## Run (Colab / Modal / RunPod)

```bash
pip install unsloth
python train.py
```

Or override the defaults:

```bash
BASE_MODEL=Qwen/Qwen3-1.7B EPOCHS=2 python train.py
```

## The one contract that matters

`BASE_MODEL` here **must equal** `BASE_MODEL` in `eval/config.py`. The adapter is
trained against that base and the eval loads it back onto the same base. If they
differ, the adapter won't line up.

The script writes the adapter to `../outputs/adapter`. The eval's default
`ADAPTER_PATH` is `outputs/adapter` (relative to where you run it), so from
`eval/` you'll want:

```bash
ADAPTER_PATH=../outputs/adapter python run_eval.py
```

## What it does, and what to touch

- Loads the base in 4-bit, attaches a rank-16 LoRA on the attention + MLP
  projections.
- Renders each ShareGPT conversation with the model's own chat template,
  `enable_thinking=False` (we want direct replies, not Qwen3 `<think>` blocks).
- Trains **only on the assistant turns** (`train_on_responses_only`), so it
  learns to produce the voice, not to model the student's questions.
- Saves the adapter and prints one sample generation to eyeball.

**Don't tune hyperparameters to fix a bad model.** Per the brief, a disappointing
result is almost always a data problem. The only knob to touch routinely is
`EPOCHS` (1-3). Overfitting tell: train loss diving toward 0 and the model
parroting training examples verbatim. If you see that, lower `EPOCHS` (1 is often
enough for a style/voice tune) rather than adding regularization.

## After training

Back in `eval/`, run the base-vs-tuned comparison:

```bash
cd ../eval
ADAPTER_PATH=../outputs/adapter python run_eval.py
```

That produces the numbers that tell you whether the tune actually moved
reads-human / Pangram over the base.

By default the base arm runs locally through Ollama and the tuned arm runs from
the adapter via transformers. That's fine for iterating, but the two arms are at
different precisions. For the honest headline number, put both on the same
backend (see next section).

## Run the tuned model in Ollama (honest eval + the demo)

To get the tuned model onto your local machine alongside the base — both then
scored through the same Ollama backend, and ready for the demo:

```bash
# 1. merge the LoRA adapter into the base weights (do this on the GPU box)
#    Unsloth one-liner:
python -c "from unsloth import FastLanguageModel; \
m,t=FastLanguageModel.from_pretrained('outputs/adapter',load_in_4bit=False); \
m.save_pretrained_gguf('outputs/gguf', t, quantization_method='q4_k_m')"

# 2. download outputs/gguf/*.gguf to your machine, then register it with Ollama
#    (write a Modelfile pointing FROM the .gguf), e.g.:
#      printf 'FROM ./outputs/gguf/unsloth.Q4_K_M.gguf\n' > Modelfile
ollama create qwen3-4b-human -f Modelfile

# 3. point the eval's tuned arm at it
#    in eval/config.py: TUNED_BACKEND="ollama"  (OLLAMA["tuned_model"] is already
#    "qwen3-4b-human"), then re-run run_eval.py
```

Now `ollama run qwen3-4b-human` is your demo, and both eval arms are local GGUF
at matching precision.
