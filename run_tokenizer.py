import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bench_lib import *

# identical payloads -> input_tokens delta reveals tokenizer
samples = {
 "zh_short":  "今天天气很好。",
 "zh_long":   "人工智能技术的快速发展正在深刻改变着人类社会的生产方式和生活方式，从医疗诊断到自动驾驶，从智能客服到科学发现，各个领域都在经历前所未有的变革。" * 2,
 "en_short":  "The quick brown fox jumps over the lazy dog.",
 "en_long":   "Artificial intelligence is transforming how we work, learn, and communicate. From healthcare to transportation, the impact is profound and far-reaching. " * 2,
 "code":      "def fibonacci(n):\n    return n if n < 2 else fibonacci(n-1) + fibonacci(n-2)\n",
 "mix":       "请分析这段代码 def f(x): return x**2 + 1 的时间复杂度。",
}
MODELS2 = ["deepseek-v4-flash","deepseek-v4.1-flash","deepseek-v4-pro","glm-5.3-flash","glm-5.3","kimi-k3","minimax-m3"]
res = {"meta": {"time": __import__("time").strftime("%Y-%m-%d %H:%M:%S"),
                "method": "input_tokens (含固定 ~520 注入提示)；看相对差异"}, "tokens": {}, "shapes": {}}
# baseline: minimal prompt
for m in MODELS2:
    row = {}
    r0 = call(m, "x", max_out=4, temperature=0, timeout=180)
    base = (r0.get("usage") or {}).get("input_tokens")
    row["_base(x)"] = base
    for k, s in samples.items():
        r = call(m, s, max_out=4, temperature=0, timeout=180)
        row[k] = (r.get("usage") or {}).get("input_tokens")
    res["tokens"][m] = row
    # chars per token using zh_long
    if row.get("zh_long") and base:
        n_chars = len(samples["zh_long"])
        res["shapes"][m] = {"zh_chars": n_chars, "zh_tokens_net": row["zh_long"] - base,
                            "chars_per_token": round(n_chars / max(row["zh_long"] - base, 1), 2),
                            "base_overhead": base}
    print(f'{m:20s} base={base}  ' + "  ".join(f'{k}={row[k]}' for k in samples), flush=True)
save("09_tokenizer_fingerprint.json", res)
print()
print("=== 家族指纹（中文净 token 数越接近说明分词器越像）===")
for m, v in res["shapes"].items():
    print(f'  {m:20s} base_overhead={v["base_overhead"]:5}  zh_net_tokens={v["zh_tokens_net"]:5}  chars/token={v["chars_per_token"]}')