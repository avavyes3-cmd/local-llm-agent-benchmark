# Local LLM Agent Benchmark on an RTX 3070 Ti 8GB

Practical evaluation of small local models for an **Agent / Research** role behind an OpenAI-compatible `llama.cpp` server.

The target workflow is:

```text
User → local Agent / Research model → coding model in VS Code → Codex fallback
```

The goal was not to find the highest benchmark score. It was to find a model that can simultaneously:

- select tools and emit real OpenAI `tool_calls`;
- consume tool results and continue correctly;
- issue multiple tool calls when needed;
- synthesize conflicting evidence without trusting a weak preliminary claim;
- follow strict JSON and code-only formats;
- use roughly 15K tokens on an 8GB GPU;
- remain useful for unrestricted, consenting-adult content;
- respond fast enough for an interactive editor workflow.

## Hardware and runtime

- GPU: NVIDIA RTX 3070 Ti, 8GB VRAM
- Runtime: [llama.cpp](https://github.com/ggml-org/llama.cpp) b10666, CUDA 12.4
- Quantization: official or verified `Q4_K_M` GGUF
- Context: 16,384
- Parallel slots: 1
- GPU layers: all (`-ngl 99`)
- Sampling: temperature 0 for older instruct models; vendor-recommended `temperature=1.0`, `top_p=0.95` for Granite 4.2

## Models tested

- NousResearch Hermes 3 Llama 3.1 8B
- Dolphin 3.0 Llama 3.1 8B
- IBM Granite 4.1 8B
- [Mistral Ministral 3 8B Instruct 2512](https://huggingface.co/mistralai/Ministral-3-8B-Instruct-2512)
- [IBM Granite 4.2 8B](https://huggingface.co/ibm-granite/granite-4.2-8b), with thinking disabled and low-effort thinking

## Outcome

**Ministral 3 8B Instruct 2512 was the best overall fit.**

It combined correct evidence synthesis, real and parallel tool calls, exact tool-result continuation, a successful ~15K retrieval test, unrestricted adult-content behavior, and roughly 50–59 generated tokens/s. Its main weakness was adding Markdown fences around otherwise valid structured output; that is much easier to repair in a harness than incorrect reasoning.

Granite 4.1 and 4.2 showed better evidence reasoning or strict code behavior in some tests, but their dense 8B architecture nearly saturated the 8GB card at 16K. Granite 4.1 used about 7,934MB and processed a 13.5K prompt too slowly to finish inside 240 seconds. Granite 4.2 generated only about 7–15 tokens/s without thinking and about 5–8 tokens/s with thinking, refused the adult-content test, and regressed on parallel tool calls.

See [the full results](docs/results.md) and [benchmark methodology](docs/methodology.md).

## Recommended role split

```text
Ministral 3 8B       Agent / Research / tool routing
Qwen2.5-Coder        code editing and implementation
Codex                complex or high-reliability fallback
```

The central lesson is that **correct evidence reasoning matters more than a clean wrapper**. Markdown fences can be stripped. A model that confidently trusts contradicted evidence cannot be made reliable with simple post-processing.

