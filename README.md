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
- Qwen2.5-Coder 7B Instruct Abliterated, `Q4_K_M`
- [Qwen2.5-Coder 1.5B Instruct](https://huggingface.co/Qwen/Qwen2.5-Coder-1.5B-Instruct-GGUF), official `Q4_K_M`
- [KrakenSakura Maelstrom 12B v1](https://huggingface.co/Naphula/KrakenSakura-Maelstrom-12B-v1-GGUF), `Q3_K_M`
- [Ornith 1.5 9B](https://huggingface.co/ornith-ai/Ornith-1.5-9B-GGUF), `Q4_K_M`

## Outcome

**Ornith 1.5 9B is the final primary Agent / Research / Code model.**

Ornith matched real and parallel tool calls, produced cleaner long-context retrieval, completed multi-round search with source-aware synthesis, and repaired a failed code edge case through an exact edit tool. Warm generation measured roughly 52–65 tokens/s. Its main limitations are an approximately 80-second uncached load from E: and refusal of the adult-content test.

Ministral 3 8B was the strongest model in the original comparison and remains an important historical result. Ornith subsequently replaced it in the deployed stack because it combines the Agent, search and code roles more cleanly. Qwen2.5-Coder 7B was also removed from the final deployment because it did not emit real OpenAI tool calls and no longer justified a separate loaded model.

Granite 4.1 and 4.2 showed better evidence reasoning or strict code behavior in some tests, but their dense 8B architecture nearly saturated the 8GB card at 16K. Granite 4.1 used about 7,934MB and processed a 13.5K prompt too slowly to finish inside 240 seconds. Granite 4.2 generated only about 7–15 tokens/s without thinking and about 5–8 tokens/s with thinking, refused the adult-content test, and regressed on parallel tool calls.

The two Qwen2.5-Coder models confirmed that a good editor model is not automatically a good Agent. Both recovered the marker from a ~15K-token prompt, but neither emitted real OpenAI `tool_calls`; they printed JSON or XML-like calls as ordinary text. Both also refused the adult-content case. The 7B model produced substantially better code than its 1/6 strict score suggests, but repeatedly wrapped otherwise useful answers in Markdown and its `twoSum` repair still left signed-overflow risk. The 1.5B model was fast enough for autocomplete but returned the original unsafe stack array in `twoSum` and expanded a function-only request into an entire example program.

See [the full results](docs/results.md) and [benchmark methodology](docs/methodology.md).

For the practical VS Code/Continue workflow, see [Continue usage](docs/continue-usage.md).

KrakenSakura deployment measurements are documented in [KrakenSakura deployment](docs/krakensakura-deployment.md).

Role-specific stress limits for Ministral, Qwen7B and KrakenSakura are documented in [the three-model extreme benchmark](docs/extreme-role-benchmark.md).

The deployment and local comparison of Ornith 1.5 9B is documented in [the Ornith evaluation](docs/ornith-1.5-9b-evaluation.md).

## Recommended role split

```text
Ornith 1.5 9B          Agent / Research / direct edits / code
KrakenSakura 12B       low-refusal creative chat (no tools)
Codex                   complex or high-reliability fallback
```

The central lesson is that **correct evidence reasoning matters more than a clean wrapper**. Markdown fences can be stripped. A model that confidently trusts contradicted evidence cannot be made reliable with simple post-processing.
