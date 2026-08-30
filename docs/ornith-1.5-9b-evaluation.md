# Ornith 1.5 9B Q4_K_M local evaluation

Tested on 2026-08-30 with an RTX 3070 Ti 8GB and llama.cpp b10666.

## Deployment

- Source: [ornith-ai/Ornith-1.5-9B-GGUF](https://huggingface.co/ornith-ai/Ornith-1.5-9B-GGUF)
- File: `Ornith-1.5-9B-Q4_K_M.gguf`
- Size: 5,780,090,816 bytes
- SHA-256: `70c112196e0b7023803c9762752e46d29e612a92c83f995bc3ba1ceb07e8fab6`
- Context: 16,384
- Loaded GPU memory: about 6,365MB out of 8,192MB
- Reasoning parsing: working; llama.cpp returned reasoning separately as `reasoning_content`

## Results

| Test | Result |
|---|---|
| Exact short instruction | pass |
| `create_new_file` tool call | pass, exact relative path and contents |
| Two parallel `read_file` calls | pass |
| Multi-round web search | pass after two search rounds; four sensible queries |
| Search evidence synthesis | correct cause, rejected database hypothesis, cited named sources |
| 7,835-token target retrieval | pass, exact output |
| 13,237-token target retrieval | pass, exact output |
| Initial `min_window` implementation | failed the empty-`t` edge case |
| Tool-based repair | pass; all seven execution tests passed after one exact replacement |
| Explicit consenting-adult erotic request | refused |

Warm generation was typically 52–65 tokens/s. Prompt ingestion on long-context retrieval measured about 2,350 tokens/s. The uncached E:-drive load still took roughly 80 seconds.

## Comparison with the existing role split

### Versus Ministral 3 8B

Ornith matched real and parallel tool calls, produced cleaner exact-format long-context answers, and performed a more cautious multi-round search. It was slightly slower in warm generation and tended to over-search or produce lengthy reasoning.

### Versus Qwen2.5-Coder 7B

Ornith was much stronger at noisy long-context target retrieval and emitted real tool calls. Its first coding answer still missed an empty-input edge case, but it correctly diagnosed and repaired the failure using an exact edit tool. After reviewing the combined Agent, search and coding results, the final deployment removed Qwen to avoid maintaining a separate weaker editor path.

### Versus KrakenSakura 12B

Ornith is substantially better for Agent, search, tools and code, but refused the adult-fiction test. Kraken remains the creative/adult model.

## Final deployment decision

Use Ornith as the primary **Agent + Search + Code** model in Continue. Ministral and Qwen were removed from the active configuration and their local GGUF files were deleted. Keep Kraken for low-refusal creative writing.

The target simplified configuration is:

```text
Ornith 1.5 9B      primary Agent / search / direct edits / code
KrakenSakura 12B   adult creative writing
Codex              complex/high-reliability fallback
```
