# KrakenSakura Maelstrom 12B deployment

## Deployed configuration

- Model: [Naphula/KrakenSakura-Maelstrom-12B-v1-GGUF](https://huggingface.co/Naphula/KrakenSakura-Maelstrom-12B-v1-GGUF)
- Quantization: `Q3_K_M` (6,083,108,256 bytes)
- Runtime: llama.cpp b10666
- Context: 8,192
- Chat template: ChatML
- GPU: RTX 3070 Ti 8GB

The embedded/default template produced unrelated output. ChatML fixed instruction following and is required for this deployment.

## Measured behavior

| Test | Result |
|---|---|
| Short Chinese instruction | Correct after switching to ChatML |
| Warm generation speed | roughly 30–51 tokens/s |
| Explicit consenting-adult fiction request | completed without refusal |
| Dark/violent fictional writing | accepted |
| Native OpenAI `create_new_file` tool call | failed; claimed the file was created in plain text |

KrakenSakura is therefore configured in Continue as **Creative Chat (No Tools)**. It is useful for low-refusal creative writing but must not be used as the coding Agent.

## Continue role split after deployment

```text
KrakenSakura 12B       low-refusal creative chat, no file tools
Ministral 3 8B         Agent, direct file creation/editing, verification
Qwen2.5-Coder 7B       Edit/Apply code generation
Codex                   complex/high-reliability fallback
```

Ministral passed fresh smoke tests for both `create_new_file` and exact replacement with workspace-relative paths. Its warm tool-call generation measured about 68–74 tokens/s. Qwen2.5-Coder 7B produced a correct code-only repair at about 86 tokens/s.

## Storage limitation

The model directory is on the E: volume, which Windows reports as a Realtek PCIe Card Reader rather than the NVMe system disk. Warm inference is fast. An uncached model switch took roughly 50–90 seconds because only one model fits in 8GB VRAM and each switch reloads several gigabytes from E:. A subsequent OS-cached Ministral reload completed in about six seconds. The active model is now retained for one hour of idle time to reduce unnecessary reloads.
