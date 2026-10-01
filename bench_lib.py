"""
LLM API benchmark toolkit
=========================

Measures a model endpoint on four axes:

  1. connectivity   - basic / repeated / concurrent / long-context / error handling
  2. speed          - short latency, long latency, throughput, TTFT
  3. capability     - instruction following, math, code, debugging, JSON, etc.
  4. identity drift - does the model claim to be what the endpoint says it is?

The target endpoint is **not hard-coded**. Configure it one of two ways:

  A. Environment variables

       $env:BENCH_BASE_URL = "https://your-endpoint.example/v1"
       $env:BENCH_API_KEY  = "sk-..."
       $env:BENCH_MODELS   = "model-a,model-b,model-c"

  B. A local file `bench.local.json` (git-ignored)

       {
         "base_url": "https://your-endpoint.example/v1",
         "api_key": "sk-...",
         "models": ["model-a", "model-b", "model-c"]
       }

Copy `bench.example.json` to `bench.local.json` and fill it in.
"""
import json, re, os, time, sys, base64, io, contextlib
import urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor

OUT = os.path.dirname(os.path.abspath(__file__))
LOCAL_CFG = os.path.join(OUT, "bench.local.json")


def _load_config():
    cfg = {"base_url": "", "api_key": "", "models": []}

    if os.path.exists(LOCAL_CFG):
        with open(LOCAL_CFG, encoding="utf-8") as f:
            cfg.update(json.load(f))

    cfg["base_url"] = os.environ.get("BENCH_BASE_URL") or cfg.get("base_url") or ""
    cfg["api_key"]  = os.environ.get("BENCH_API_KEY")  or cfg.get("api_key")  or ""

    env_models = os.environ.get("BENCH_MODELS")
    if env_models:
        cfg["models"] = [m.strip() for m in env_models.split(",") if m.strip()]

    cfg["base_url"] = (cfg["base_url"] or "").rstrip("/")
    if not cfg["base_url"]:
        raise SystemExit(
            "No endpoint configured.\n"
            "Set BENCH_BASE_URL / BENCH_API_KEY / BENCH_MODELS, "
            "or copy bench.example.json to bench.local.json and edit it."
        )
    if not cfg["models"]:
        raise SystemExit("No models configured. Set BENCH_MODELS or edit bench.local.json.")

    return cfg


CFG    = _load_config()
BASE   = CFG["base_url"]
TOK    = CFG["api_key"]
URL    = BASE + "/responses"
if os.environ.get("BENCH_API_STYLE", "responses").lower() == "chat":
    URL = BASE + "/chat/completions"
MODELS = CFG["models"]


def raw_call(model, payload_extra, stream=False, timeout=180):
    payload = {"model": model}
    payload.update(payload_extra)
    body = json.dumps(payload).encode()
    h = {"Authorization": "Bearer " + TOK, "Content-Type": "application/json"}
    if stream:
        h["Accept"] = "text/event-stream"
    req = urllib.request.Request(URL, data=body, headers=h)
    t0 = time.time()
    try:
        r = urllib.request.urlopen(req, timeout=timeout)
    except urllib.error.HTTPError as e:
        return {"ok": False, "status": e.code, "error": e.read().decode()[:800],
                "elapsed": time.time() - t0}
    except Exception as e:
        return {"ok": False, "status": None, "error": f"{type(e).__name__}: {e}",
                "elapsed": time.time() - t0}

    if not stream:
        raw = r.read().decode()
        dt = time.time() - t0
        try:
            d = json.loads(raw)
        except Exception:
            return {"ok": False, "status": r.status, "error": raw[:800], "elapsed": dt}
        return {"ok": True, "status": r.status, "elapsed": dt, "resp": d,
                "text": extract_text(d), "usage": d.get("usage")}

    ttft = None
    text_parts = []
    final = None
    while True:
        line = r.readline()
        if not line:
            break
        s = line.decode("utf-8", "replace").strip()
        if not s.startswith("data:"):
            continue
        data = s[5:].strip()
        if data == "[DONE]":
            break
        try:
            ev = json.loads(data)
        except Exception:
            continue
        if ev.get("type") == "response.output_text.delta":
            if ttft is None:
                ttft = time.time() - t0
            text_parts.append(ev.get("delta", ""))
        elif ev.get("type") == "response.completed":
            final = ev.get("response")
    dt = time.time() - t0
    return {"ok": True, "status": r.status, "elapsed": dt, "ttft": ttft,
            "text": "".join(text_parts), "resp": final,
            "usage": (final or {}).get("usage")}


def extract_text(d):
    out = []
    for item in d.get("output", []):
        if item.get("type") == "message":
            for c in item.get("content", []):
                if c.get("type") == "output_text":
                    out.append(c.get("text", ""))
    return "".join(out)


def call(model, prompt, max_out=1024, effort=None, temperature=0, stream=False,
         tools=None, timeout=180, extra=None):
    p = {"input": prompt, "max_output_tokens": max_out}
    if temperature is not None:
        p["temperature"] = temperature
    if effort:
        p["reasoning"] = {"effort": effort}
    if tools:
        p["tools"] = tools
    if extra:
        p.update(extra)
    return raw_call(model, p, stream=stream, timeout=timeout)


def save(name, obj):
    results_dir = os.path.join(OUT, "results")
    out_dir = results_dir if os.path.isdir(results_dir) else OUT
    with open(os.path.join(out_dir, name), "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
    print("[saved]", name, flush=True)