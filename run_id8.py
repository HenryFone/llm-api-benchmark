import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bench_lib import *

Q = "只说一句话：你是哪家公司开发的什么模型？"
TARGETS = ["deepseek-v4-flash","deepseek-v4.1-flash","glm-5.3-flash","glm-5.3","deepseek-v4-pro","kimi-k3","minimax-m3"]
res = {}
for m in TARGETS:
    hits = []
    for i in range(8):
        r = call(m, Q, max_out=200, temperature=0, timeout=200)
        hits.append((r.get("text") or "").strip().replace("\n"," "))
    c = lambda kw: sum(1 for h in hits if kw in h)
    res[m] = {"n": 8, "Claude": c("Claude"), "Anthropic": c("Anthropic"),
              "DeepSeek": c("DeepSeek")+c("深度求索"), "GLM": c("GLM")+c("智谱")+c("Z.ai"),
              "Kimi": c("Kimi")+c("月之暗面")+c("Moonshot"), "MiniMax": c("MiniMax")+c("稀宇"),
              "samples": hits[:4]}
    print(f'{m:20s} Claude={res[m]["Claude"]}/8 Anthropic={res[m]["Anthropic"]}/8 DeepSeek={res[m]["DeepSeek"]}/8 GLM={res[m]["GLM"]}/8 Kimi={res[m]["Kimi"]}/8 MiniMax={res[m]["MiniMax"]}/8', flush=True)
    print("     样例:", " || ".join(h[:60] for h in hits[:3]), flush=True)
with open(os.path.join(OUT,"11_identity_determinism.json"),"w",encoding="utf-8") as f:
    json.dump(res, f, ensure_ascii=False, indent=2)
print("[saved] 11_identity_determinism.json")