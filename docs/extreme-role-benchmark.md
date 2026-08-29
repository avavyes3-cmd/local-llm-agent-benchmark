# Three-model role-limit benchmark

Test date: 2026-08-29/30, Asia/Shanghai. Hardware: RTX 3070 Ti 8GB. Runtime: llama.cpp b10666, one loaded model at a time. Raw adult generations were not saved; the result file retains only length, refusal flags, repetition metrics, and SHA-256 digests.

## Executive result

| Role | Model | Practical rating | Best use | Hard limit observed |
|---|---|---:|---|---|
| Agent / tool routing | Ministral 3 8B | 8/10 | file creation, editing, parallel reads | exact-format compliance and verbose synthesis |
| Research / search | Ministral 3 8B | 6/10 | evidence gathering with user review | query may invent a year; synthesis adds unsupported branches |
| Code / Edit | Qwen2.5-Coder 7B | 7/10 | focused functions and Apply edits | loses the target in a noisy ~12K-token code prompt |
| Adult creative writing | KrakenSakura 12B | 7.5/10 | low-refusal long-form adult fiction | weak exact character/ending/length control |

## Ministral 3 8B: Agent and search

### Passed

- Emitted a real `create_new_file` tool call with the exact relative path and contents.
- Emitted two parallel `read_file` calls for `src/a.py` and `src/b.py`.
- Selected `search_web` before answering a research question.
- Correctly identified the substantive causal chain: R17 preceded the regression, cache misses rose, rollback restored latency, and database saturation was not observed.
- Retrieved `AGENT-CONTEXT-7419` from a 10,951-token prompt.
- Warm tool-call generation measured about 72–75 tokens/s.

### Limits

- The search query appended `2024` even though no year was supplied and the test date was 2026. Search queries therefore require inspection for invented narrowing terms.
- Evidence synthesis was substantively correct but did not consistently preserve requested source labels. It also invented extra unsupported alternatives (hardware and third-party failure) and hit the 320-token output cap.
- Long-context retrieval found the correct marker but returned prose and Markdown instead of only the marker. This is a strict-format failure, not a retrieval failure.
- A cold switch from another multi-gigabyte model on E: took about 64 seconds in this run.

Verdict: strong enough for local Agent work and assisted research, but search conclusions should be reviewed. It is not a fully autonomous research agent.

## Qwen2.5-Coder 7B: code and Edit/Apply

### Passed

- Generated a correct O(n) Python minimum-window-substring implementation.
- The generated function passed six executed edge-case tests.
- Returned valid strict JSON with the required values and key order.
- Warm generation measured about 88 tokens/s.

### Limits

- Wrapped the otherwise correct function in a Markdown fence despite a code-only instruction.
- In a noisy 12,049-token code prompt, it returned the repeated decoy value `17` instead of `CODE-CONTEXT-9137`.
- A larger constructed prompt exceeded the configured 16K context and received HTTP 400. The server limit is real; usable accuracy degrades before the hard limit.

Verdict: fast and effective for focused edits that fit in a few files. Do not dump an entire large repository or huge generated file into one prompt and expect reliable target selection.

## KrakenSakura Maelstrom 12B: adult creative writing

### Passed

- Three consenting-adult prompts completed without refusal or safety lecture.
- The 1,492-token long-form generation completed normally at about 48 tokens/s.
- The long-form output retained a unique 4-gram ratio of 0.8478: some repetition appeared, but it did not collapse into a loop.
- The constrained scene preserved the requested rain/hotel setting and did not trigger the violence-term check.

### Limits

- The nominal 400-character prompt expanded to 851 characters and hit the 768-token cap.
- The constrained prompt missed both required character names and the exact ending, and also hit the token cap.
- It does not emit real file tools. In a tool test it claimed a file was created in ordinary text, without a `tool_call`.
- The first uncached switch from E: plus generation took about 185 seconds; warm generation remained near 47–48 tokens/s.

Verdict: the least censored and best adult-fiction model in this local set, but it needs short, prioritized constraints and generous output limits. It is a creative model, not an Agent.

## Recommended operating rules

1. Use Ministral Agent for direct file creation/editing and searches. Ask it to show the search query and cite evidence; verify dates.
2. Use Qwen7B Edit/Apply on selected files or functions. Keep the prompt well below 12K tokens when precision matters.
3. Use Kraken for adult fiction. Put the most important character and ending constraints first, request shorter scenes, and split long stories into continuations.
4. Avoid frequent model switching. E: is reported as a Realtek PCIe Card Reader, so uncached loads dominate latency even though warm inference is fast.

Machine-readable measurements are in [`results/extreme-role-benchmark.json`](../results/extreme-role-benchmark.json). The reproducible harness is in [`scripts/extreme_benchmark.py`](../scripts/extreme_benchmark.py).

