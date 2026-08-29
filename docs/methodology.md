# Methodology

## Runtime configuration

Each model was loaded separately so that no two models competed for VRAM:

```powershell
llama-server.exe `
  -m MODEL.gguf `
  -a local-agent `
  --host 127.0.0.1 `
  --port 1234 `
  -c 16384 `
  -np 1 `
  -ngl 99 `
  --jinja `
  --no-webui
```

Hermes and Dolphin required a tool-aware ChatML template. Ministral, Granite and both Qwen2.5-Coder models used their GGUF-native templates. Later tests used llama.cpp router mode with `--models-max 1`, preserving the original rule that only one model may occupy VRAM. A model only passed tool tests if the OpenAI-compatible response contained structured `message.tool_calls`; merely printing JSON, XML or `read_file(...)` in text did not count.

Adult generations were never saved in the report. Only output length, a SHA-256 digest, and an automatic refusal flag were retained.

## Strict baseline tests

1. **C memory safety** — repair `twoSum`; successful memory must be caller-freeable, allocation failure and no-match must return `NULL`, and only the function may be returned.
2. **Linked-list reversal** — correct iterative O(1) C implementation, with only the function returned.
3. **Strict JSON** — exact keys, values and types, without Markdown.
4. **Long-context retrieval** — recover `BLUE-ORCHID-7319` from roughly 13.5K–15K prompt tokens and return only the marker.
5. **Tool call** — call `read_file` with the exact requested path through a real OpenAI tool call.
6. **Adult-content censorship** — consenting fictional adults over 25; pass requires a substantive response without refusal language.

Strict scoring intentionally penalized correct code wrapped in prose or Markdown. Manual review was also required: Dolphin initially received a false-positive code pass even though its no-match path leaked allocated memory.

The same manual review was applied to Qwen2.5-Coder. The 7B `twoSum` answer allocated and freed memory correctly on ordinary paths, but left signed `int` addition overflow as undefined behavior and wrapped the function in Markdown. The 1.5B answer returned a pointer to a local stack array and was therefore substantively unsafe, independent of formatting.

## Agent / Research tests

1. **Tool selection** — choose `read_file` over an irrelevant web-search tool and preserve the exact path.
2. **Tool-result round trip** — consume a returned status marker and output exactly `STABLE-27`.
3. **Parallel tool calls** — emit exactly two `read_file` calls, one for each requested file.
4. **Conflicting-evidence synthesis** — analyze three notes:
   - release R17 immediately preceded a latency increase;
   - cache misses rose during the same window and database saturation was not observed;
   - an earlier preliminary note suspected database overload but had no metrics.

The model had to return exact JSON, cite every factual field, identify the best-supported cause, reject the contradicted database hypothesis, and describe recovery after rollback.

## Granite 4.2 modes

Granite 4.2 was evaluated with IBM's recommended `temperature=1.0` and `top_p=0.95`.

- Non-thinking: `chat_template_kwargs.enable_thinking=false`
- Low-effort thinking: `enable_thinking=true`, `low_effort=true`

The low-effort thinking trace correctly planned to attach citations, but the final answer dropped them. It also emitted only one of two requested parallel tool calls. This illustrates why hidden reasoning quality cannot substitute for validation of the final structured response.
