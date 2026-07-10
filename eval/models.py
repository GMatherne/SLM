"""Model interface: generate completions for a scenario from the base model and
the tuned (base + LoRA adapter), behind one interface.

Two backends, chosen per arm in config:
- "transformers": HF weights on a GPU (+ peft adapter for the tuned arm).
- "ollama": a local GGUF served by your Ollama server (no GPU cloud needed).

Both backends expose .load() and .generate(scenario). Eval is decoupled from
training: you can also skip generation entirely and feed a precomputed
outputs.jsonl to run_eval.py with --outputs.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

import config


def _build_prompt(scenario: dict) -> list[dict]:
    """Turn a scenario row into chat messages. No system prompt by default: the
    training data is (task -> piece) with no system message, so the tuned model
    learns the voice unconditionally. Matching that here (bare user task) keeps
    the base-vs-tuned comparison fair and consistent with how the model trained.
    A scenario may still set its own 'system' to override."""
    msgs = []
    if scenario.get("system"):
        msgs.append({"role": "system", "content": scenario["system"]})
    msgs.append({"role": "user", "content": scenario["prompt"]})
    return msgs


@dataclass
class Generator:
    """Loads one model (optionally with a LoRA adapter) and generates text."""

    model_id: str
    adapter_path: str | None = None
    _model: object = None
    _tok: object = None

    def load(self) -> "Generator":
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer

        self._tok = AutoTokenizer.from_pretrained(self.model_id)
        self._model = AutoModelForCausalLM.from_pretrained(
            self.model_id,
            torch_dtype=torch.bfloat16,
            device_map="auto",
        )
        if self.adapter_path:
            from peft import PeftModel

            self._model = PeftModel.from_pretrained(self._model, self.adapter_path)
        self._model.eval()
        return self

    def generate(self, scenario: dict) -> str:
        import torch

        assert self._model is not None, "call .load() first"
        torch.manual_seed(config.GEN["seed"])
        messages = _build_prompt(scenario)
        inputs = self._tok.apply_chat_template(
            messages, add_generation_prompt=True, return_tensors="pt"
        ).to(self._model.device)
        with torch.no_grad():
            out = self._model.generate(
                inputs,
                max_new_tokens=config.GEN["max_new_tokens"],
                temperature=config.GEN["temperature"],
                top_p=config.GEN["top_p"],
                do_sample=config.GEN["do_sample"],
                pad_token_id=self._tok.eos_token_id,
            )
        text = self._tok.decode(out[0][inputs.shape[-1]:], skip_special_tokens=True)
        return text.strip()


@dataclass
class OllamaGenerator:
    """Generates via a local Ollama server. Nothing to load into this process --
    the server holds the model."""

    model_tag: str

    def load(self) -> "OllamaGenerator":
        return self

    def generate(self, scenario: dict) -> str:
        import requests

        messages = _build_prompt(scenario)
        payload = {
            "model": self.model_tag,
            "messages": messages,
            "stream": False,
            "think": config.OLLAMA["think"],
            "options": {
                "temperature": config.GEN["temperature"],
                "top_p": config.GEN["top_p"],
                "num_predict": config.GEN["max_new_tokens"],
                "seed": config.GEN["seed"],
            },
        }
        url = config.OLLAMA["host"].rstrip("/") + "/api/chat"
        try:
            r = requests.post(url, json=payload, timeout=300)
            r.raise_for_status()
        except requests.HTTPError:
            # older Ollama builds reject the "think" field -- retry without it
            payload.pop("think", None)
            r = requests.post(url, json=payload, timeout=300)
            r.raise_for_status()
        text = r.json()["message"]["content"]
        # strip any stray <think>...</think> if the server ignored think=false
        text = re.sub(r"<think>.*?</think>", "", text, flags=re.S)
        return text.strip()


def base_generator():
    if config.BASE_BACKEND == "ollama":
        return OllamaGenerator(config.OLLAMA["base_model"])
    return Generator(config.BASE_MODEL)


def tuned_generator():
    if config.TUNED_BACKEND == "ollama":
        return OllamaGenerator(config.OLLAMA["tuned_model"])
    return Generator(config.BASE_MODEL, adapter_path=config.ADAPTER_PATH)
