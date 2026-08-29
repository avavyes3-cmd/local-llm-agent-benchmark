# Results

## Strict baseline

| Model | Score | Long context | Real tools | Adult test | Approx. generation speed |
|---|---:|---|---|---|---:|
| Hermes 3 8B | 4/6 | pass | pass | no refusal | ~90 tok/s |
| Dolphin 3.0 8B | 4/6 after manual correction | pass | pass | no refusal | ~92 tok/s |
| Granite 4.1 8B | 2/6 | over 240 s | pass | refused | ~17–24 tok/s |
| Ministral 3 8B | 3/6 | ~15K in 7.1 s | pass | no refusal | ~50–59 tok/s |
| Granite 4.2 8B, non-thinking | 4/6 | over 60 s | pass | refused | ~7–15 tok/s |

Granite 4.2 achieved the cleanest strict C and JSON outputs. Ministral lost strict points mainly because it added Markdown fences, while its `twoSum` also leaked memory when `n < 2` after a successful allocation.

## Agent / Research

| Model | Tool selection | Tool round trip | Two tool calls | Evidence synthesis | Score |
|---|---:|---:|---:|---|---:|
| Hermes 3 8B | pass | fail | pass | incorrect central conclusion | 2/4 |
| Dolphin 3.0 8B | pass | fail | pass | incorrect central conclusion | 2/4 |
| Granite 4.1 8B | pass | pass | pass | semantically correct; one missing citation | 3/4 |
| Ministral 3 8B | pass | pass | pass | semantically correct and cited; fenced JSON | 3/4 |
| Granite 4.2 8B, non-thinking | pass | pass | fail | correct conclusion; all citations missing | 2/4 |

Granite 4.2 low-effort thinking took about 46 seconds for the evidence task. Its reasoning trace explicitly planned the required citations, but the final JSON omitted them. A low-effort parallel-tool test took about 19 seconds and still emitted only the first file call.

## Model-by-model notes

### Hermes 3 8B

- Fast and capable of valid structured tool calls with the correct template.
- Good strict JSON and long-context retrieval.
- Failed the most important evidence-conflict test by trusting the unsupported database hypothesis.
- Code answers were verbose and one memory-safety repair was logically wrong.

### Dolphin 3.0 8B

- Fast, unrestricted and capable of parallel tool calls.
- Evidence synthesis was worse than Hermes: missing citations, Markdown despite explicit prohibition, and an incorrect rollback description.
- A superficially plausible C repair leaked memory on the no-match path.

### Granite 4.1 8B

- Major improvement in grounded evidence synthesis and exact tool-result continuation.
- Correctly rejected database overload and connected the release, cache misses and rollback.
- Too slow at 16K on this 8GB card; the 13.5K prompt exceeded 240 seconds.
- Refused the adult-content test.

### Ministral 3 8B Instruct 2512

- Best evidence explanation of the group, with correct source use and citations.
- Passed single and parallel tools, tool-result continuation, adult behavior and ~15K retrieval.
- Much faster than Granite while still materially smarter than the Llama 3.1 fine-tunes in research tasks.
- Frequently added Markdown fences despite exact-format instructions. A JSON grammar or small response normalizer is recommended.

### Granite 4.2 8B

- Native reasoning is a real upgrade rather than a minor version change.
- Excellent strict C and JSON behavior in non-thinking mode.
- Did not improve this particular Agent workflow: only one of two tools was called and citations disappeared from the final research answer.
- Thinking made latency substantially worse without fixing those failures.
- Same practical 8GB/16K throughput limitation as Granite 4.1 and the same adult refusal behavior.

## Final recommendation

Use **Ministral 3 8B Instruct 2512** as the local Agent / Research model. Add deterministic output cleanup or a JSON grammar at the harness boundary. Keep coding responsibility in a dedicated coder model, and escalate high-risk or complex conclusions to a stronger hosted model.

