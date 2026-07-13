# Finish the GGUF conversion (from an already-merged model)

`colab_train.py` merges base + adapter and saves a **16-bit HF model** to
`slm_outputs/gguf/` (two `model-0000x-of-00002.safetensors` shards + config +
tokenizer), then tries to convert it to GGUF. If that last step didn't finish
(no `.gguf` file — it dies if the Colab tab sleeps), you do **not** need to
retrain. Just finish the conversion from the merged folder.

## In Colab (Drive mounted, tab kept awake — takes a few minutes, no GPU needed)

```bash
# 0. mount Drive first (Files panel > Mount)
MODEL=/content/drive/MyDrive/slm_outputs/gguf         # the merged 16-bit folder
OUT=/content/drive/MyDrive/slm_outputs                # where the .gguf lands

# 1. get llama.cpp + its python deps
!git clone --depth 1 https://github.com/ggerganov/llama.cpp
!pip -q install -r llama.cpp/requirements.txt

# 2. merged HF weights -> q8_0 GGUF. Pure python, NO C++ build. q8_0 is
#    near-lossless (~4.3 GB) and fits an 8 GB card -- this is the reliable path.
!python llama.cpp/convert_hf_to_gguf.py "$MODEL" \
    --outfile "$OUT/qwen3-human.Q8_0.gguf" --outtype q8_0
```

Download `qwen3-human.Q8_0.gguf` (~4.3 GB).

**Do NOT `cmake --build` all of llama.cpp on Colab's free tier** — the parallel
compile runs out of RAM and the compiler gets OOM-killed
(`Killed signal terminated program cc1plus`). You only need that build for the
smaller `q4_k_m` (~2.7 GB); if you want it, cap parallelism so it doesn't OOM:

```bash
!python llama.cpp/convert_hf_to_gguf.py "$MODEL" --outfile "$OUT/f16.gguf" --outtype f16
!cmake -S llama.cpp -B llama.cpp/build -DCMAKE_BUILD_TYPE=Release
!cmake --build llama.cpp/build --config Release -j 2 --target llama-quantize   # -j 2, not -j
!llama.cpp/build/bin/llama-quantize "$OUT/f16.gguf" "$OUT/qwen3-human.Q4_K_M.gguf" Q4_K_M
```

## Then run it locally with Ollama

```bash
# put the .gguf next to train/Modelfile, then:
ollama create qwen3-4b-human -f Modelfile
ollama run qwen3-4b-human
```

`Modelfile`'s `FROM` already expects `qwen3-human.Q8_0.gguf`, and its params
(temperature 0.7, top_p 0.8, top_k 20, repeat_penalty 1.15) match the round-3
eval, so local output behaves like what we scored. (If you built the q4_k_m
instead, change the `FROM` line to that filename.)

## Shortcut (skip llama.cpp)
Recent Ollama can import safetensors directly and quantize on the way in — if you
download the whole merged `gguf/` folder (~7.5 GB) and point `FROM` at it:
`ollama create qwen3-4b-human -f Modelfile --quantize q4_K_M`. Fewer steps, but a
much bigger download and it depends on your Ollama version supporting Qwen3
import. The Colab route above downloads only the final 2.7 GB and is more reliable.
