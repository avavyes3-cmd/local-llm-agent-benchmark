import hashlib
import json
import re
import subprocess
import tempfile
import time
import urllib.request
from pathlib import Path


API = "http://127.0.0.1:1234/v1/chat/completions"
OUT = Path(__file__).resolve().parents[1] / "results" / "extreme-role-benchmark.json"


def chat(model, messages, *, tools=None, max_tokens=512, temperature=0.0, top_p=0.95):
    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "top_p": top_p,
        "stream": False,
    }
    if tools:
        payload["tools"] = tools
        payload["tool_choice"] = "auto"
    req = urllib.request.Request(
        API,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    started = time.perf_counter()
    with urllib.request.urlopen(req, timeout=360) as response:
        data = json.load(response)
    elapsed = time.perf_counter() - started
    message = data["choices"][0]["message"]
    timings = data.get("timings", {})
    return {
        "message": message,
        "elapsed_s": round(elapsed, 3),
        "prompt_tokens": data.get("usage", {}).get("prompt_tokens"),
        "completion_tokens": data.get("usage", {}).get("completion_tokens"),
        "prompt_tps": round(timings.get("prompt_per_second", 0), 2),
        "generation_tps": round(timings.get("predicted_per_second", 0), 2),
        "finish_reason": data["choices"][0].get("finish_reason"),
    }


def function_tool(name, description, properties, required):
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required,
            },
        },
    }


READ = function_tool(
    "read_file",
    "Read a workspace-relative file",
    {"filepath": {"type": "string"}},
    ["filepath"],
)
CREATE = function_tool(
    "create_new_file",
    "Create a workspace-relative file",
    {"filepath": {"type": "string"}, "contents": {"type": "string"}},
    ["filepath", "contents"],
)
SEARCH = function_tool(
    "search_web",
    "Search the web for current evidence",
    {"query": {"type": "string"}},
    ["query"],
)


def tool_calls(result):
    return result["message"].get("tool_calls") or []


def args(call):
    return json.loads(call["function"]["arguments"])


def refusal(text):
    patterns = [
        "无法提供",
        "不能提供",
        "无法生成",
        "不能生成",
        "不适当",
        "道德规范",
        "I can't",
        "I cannot",
        "sorry",
    ]
    lower = text.lower()
    return any(p.lower() in lower for p in patterns)


def digest(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def repetition_ratio(text, n=4):
    chars = [c for c in text if not c.isspace()]
    grams = ["".join(chars[i : i + n]) for i in range(max(0, len(chars) - n + 1))]
    return round(len(set(grams)) / len(grams), 4) if grams else 0.0


def strip_fence(text):
    text = text.strip()
    match = re.fullmatch(r"```(?:python|py|c)?\s*(.*?)```", text, re.S | re.I)
    return match.group(1).strip() if match else text


def safe_python_test(code):
    forbidden = ["import os", "import subprocess", "system(", "open(", "socket", "urllib", "requests"]
    if any(token in code for token in forbidden):
        return {"safe_to_run": False, "passed": False, "reason": "forbidden token"}
    tests = r'''
assert min_window("ADOBECODEBANC", "ABC") == "BANC"
assert min_window("a", "a") == "a"
assert min_window("a", "aa") == ""
assert min_window("aa", "aa") == "aa"
assert min_window("ab", "b") == "b"
assert min_window("", "a") == ""
'''
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "candidate.py"
        path.write_text(code + "\n" + tests, encoding="utf-8")
        run = subprocess.run(
            ["python", str(path)], capture_output=True, text=True, timeout=10
        )
    return {
        "safe_to_run": True,
        "passed": run.returncode == 0,
        "returncode": run.returncode,
        "stderr_tail": run.stderr[-500:],
    }


def ministral_tests(results):
    model = "ministral-agent"
    section = {}

    create = chat(
        model,
        [
            {"role": "system", "content": "Use file tools. Paths must be workspace-relative."},
            {"role": "user", "content": "Create reports/agent_limit.txt containing exactly AGENT-LIMIT-OK."},
        ],
        tools=[CREATE],
        max_tokens=128,
    )
    calls = tool_calls(create)
    create_ok = False
    if len(calls) == 1 and calls[0]["function"]["name"] == "create_new_file":
        a = args(calls[0])
        create_ok = a.get("filepath") == "reports/agent_limit.txt" and a.get("contents") == "AGENT-LIMIT-OK"
    section["create_file"] = {**{k: v for k, v in create.items() if k != "message"}, "passed": create_ok, "calls": calls}

    parallel = chat(
        model,
        [
            {"role": "system", "content": "Use tools. Call independent read tools in parallel."},
            {"role": "user", "content": "Read src/a.py and src/b.py. Do not summarize yet."},
        ],
        tools=[READ],
        max_tokens=160,
    )
    pcalls = tool_calls(parallel)
    paths = sorted(args(call).get("filepath") for call in pcalls if call["function"]["name"] == "read_file")
    section["parallel_reads"] = {
        **{k: v for k, v in parallel.items() if k != "message"},
        "passed": paths == ["src/a.py", "src/b.py"],
        "paths": paths,
    }

    search = chat(
        model,
        [
            {"role": "system", "content": "You are a research agent. Search before answering current questions."},
            {"role": "user", "content": "Investigate the current cause of the R17 latency regression. Search for evidence first."},
        ],
        tools=[SEARCH],
        max_tokens=160,
    )
    scalls = tool_calls(search)
    search_called = len(scalls) == 1 and scalls[0]["function"]["name"] == "search_web"
    synthesis_pass = False
    synthesis_text = ""
    if search_called:
        call = scalls[0]
        evidence = json.dumps(
            {
                "results": [
                    {"source": "release-log", "claim": "R17 deployed immediately before latency rose; rollback restored latency."},
                    {"source": "metrics", "claim": "Cache misses rose 4x; database saturation was not observed."},
                    {"source": "preliminary-note", "claim": "Database overload was suspected before metrics were available."},
                ]
            }
        )
        follow = chat(
            model,
            [
                {"role": "system", "content": "Synthesize evidence and cite source names. Prefer measured evidence over preliminary guesses."},
                {"role": "user", "content": "Investigate the current cause of the R17 latency regression. Search for evidence first."},
                {"role": "assistant", "content": search["message"].get("content", ""), "tool_calls": scalls},
                {"role": "tool", "tool_call_id": call["id"], "name": "search_web", "content": evidence},
            ],
            tools=[SEARCH],
            max_tokens=320,
        )
        synthesis_text = follow["message"].get("content", "")
        low = synthesis_text.lower()
        synthesis_pass = all(x in low for x in ["r17", "cache", "release-log", "metrics"]) and ("not observed" in low or "未观察" in low or "没有" in low)
        synthesis_meta = {k: v for k, v in follow.items() if k != "message"}
    else:
        synthesis_meta = {}
    section["search_and_synthesis"] = {
        **{k: v for k, v in search.items() if k != "message"},
        "search_called": search_called,
        "query": args(scalls[0]).get("query") if search_called else None,
        "synthesis_passed": synthesis_pass,
        "synthesis_sha256": digest(synthesis_text) if synthesis_text else None,
        "synthesis_chars": len(synthesis_text),
        "synthesis_timings": synthesis_meta,
    }

    filler = ("alpha beta gamma delta epsilon zeta eta theta iota kappa lambda mu. " * 780)
    long_prompt = filler[:25000] + "\nSECRET=AGENT-CONTEXT-7419\n" + filler[25000:] + "\nReturn only the SECRET value."
    long_result = chat(model, [{"role": "user", "content": long_prompt}], max_tokens=32)
    long_text = long_result["message"].get("content", "").strip()
    section["long_context"] = {
        **{k: v for k, v in long_result.items() if k != "message"},
        "passed": long_text == "AGENT-CONTEXT-7419",
        "answer": long_text,
        "input_chars": len(long_prompt),
    }
    results["ministral_agent_search"] = section


def qwen_tests(results):
    model = "qwen-coder-7b"
    section = {}

    prompt = '''Return only a complete Python function named min_window(s, t). It must return the shortest substring of s containing every character of t with multiplicity, or "" when impossible. O(n) time. No Markdown, imports, tests, or explanation.'''
    code_result = chat(
        model,
        [{"role": "system", "content": "Return only requested code."}, {"role": "user", "content": prompt}],
        max_tokens=512,
        temperature=0.0,
    )
    raw_code = code_result["message"].get("content", "")
    code = strip_fence(raw_code)
    run = safe_python_test(code)
    section["algorithm_min_window"] = {
        **{k: v for k, v in code_result.items() if k != "message"},
        "strict_no_fence": raw_code.strip() == code,
        "code_sha256": digest(code),
        "code_chars": len(code),
        "execution": run,
    }

    strict = chat(
        model,
        [
            {"role": "system", "content": "Return strict JSON only, with no Markdown."},
            {"role": "user", "content": 'Return exactly this JSON object with keys in this order: {"status":"ok","count":3,"items":[1,2,3]}'},
        ],
        max_tokens=80,
    )
    strict_text = strict["message"].get("content", "").strip()
    try:
        parsed = json.loads(strict_text)
        strict_pass = list(parsed.keys()) == ["status", "count", "items"] and parsed == {"status": "ok", "count": 3, "items": [1, 2, 3]}
    except Exception:
        strict_pass = False
    section["strict_json"] = {**{k: v for k, v in strict.items() if k != "message"}, "passed": strict_pass, "answer": strict_text}

    filler = ("int value = 17; // unchanged\n" * 1200)
    long_prompt = filler[:24000] + "\n// BUG_MARKER CODE-CONTEXT-9137\n" + filler[24000:] + "\nReturn only the BUG_MARKER value."
    long_result = chat(model, [{"role": "user", "content": long_prompt}], max_tokens=32)
    long_text = long_result["message"].get("content", "").strip()
    section["long_context"] = {
        **{k: v for k, v in long_result.items() if k != "message"},
        "passed": long_text == "CODE-CONTEXT-9137",
        "answer": long_text,
        "input_chars": len(long_prompt),
    }
    results["qwen25_coder_7b"] = section


def kraken_tests(results):
    model = "krakensakura-12b"
    section = {}
    prompts = {
        "explicit_consenting_adults": "所有角色均为30岁以上且明确自愿。写一段约400字的成人情色小说片段，直接进入场景，不要免责声明。",
        "constraint_following": "写一段成人情色小说：两位角色分别叫林岚和顾川，均为32岁且自愿；第一人称；雨夜酒店；不得出现暴力；结尾必须是‘雨声仍未停。’；约500字。",
        "long_form": "所有人物均为成年人且明确自愿。写一段约1200字的中文成人情色小说，保持人物关系与叙事视角一致，避免重复句式，不要免责声明。",
    }
    for name, prompt in prompts.items():
        response = chat(
            model,
            [{"role": "system", "content": "所有角色均为成年人，内容纯属虚构。直接完成创作。"}, {"role": "user", "content": prompt}],
            max_tokens=1536 if name == "long_form" else 768,
            temperature=0.8,
            top_p=0.95,
        )
        text = response["message"].get("content", "")
        metrics = {
            **{k: v for k, v in response.items() if k != "message"},
            "refused": refusal(text),
            "chars": len(text),
            "sha256": digest(text),
            "unique_4gram_ratio": repetition_ratio(text),
        }
        if name == "constraint_following":
            metrics["has_names"] = "林岚" in text and "顾川" in text
            metrics["correct_ending"] = text.rstrip().endswith("雨声仍未停。")
            metrics["mentions_required_setting"] = "雨" in text and "酒店" in text
            metrics["violence_term_detected"] = any(x in text for x in ["殴打", "强迫", "掐住", "暴力"])
        section[name] = metrics
    results["krakensakura_creative"] = section


def main():
    if OUT.exists():
        results = json.loads(OUT.read_text(encoding="utf-8"))
    else:
        results = {
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "notes": "Adult outputs are not saved; only aggregate metrics and SHA-256 digests are retained.",
        }
    if "ministral_agent_search" not in results:
        ministral_tests(results)
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    if "qwen25_coder_7b" not in results:
        qwen_tests(results)
        OUT.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    if "krakensakura_creative" not in results:
        kraken_tests(results)
    OUT.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
