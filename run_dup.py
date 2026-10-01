import sys, os, json, itertools, difflib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bench_lib import *

P = [
 "请输出 1 到 10 的所有质数，用逗号分隔，只输出数字。",
 "用一句话解释什么是递归。",
 "把这句话翻译成英文：模型评测需要控制变量。",
]
M7 = ["deepseek-v4-flash","deepseek-v4.1-flash","deepseek-v4-pro","glm-5.3-flash","glm-5.3","kimi-k3","minimax-m3"]
out = {}
for m in M7:
    out[m] = []
    for p in P:
        outs = []
        for rep in range(2):  # repeatability at temp 0
            r = call(m, p, max_out=300, temperature=0, timeout=300)
            outs.append((r.get("text") or "").strip())
        out[m].append(outs)
    print(m, "done", flush=True)

print("\n=== 同槽重复性 (同模型2次是否一致) ===")
for m in M7:
    same = sum(1 for a,b in out[m] if a==b)
    print(f"  {m:20s} {same}/3 完全一致")

print("\n=== 跨模型输出相似度 (平均, 1.0=完全相同) ===")
def sim(m1, m2):
    s = []
    for (a1,b1),(a2,b2) in zip(out[m1], out[m2]):
        s.append(difflib.SequenceMatcher(None, a1, a2).ratio())
    return sum(s)/len(s)
pairs = []
for m1, m2 in itertools.combinations(M7, 2):
    v = sim(m1, m2); pairs.append((v, m1, m2))
for v, m1, m2 in sorted(pairs, reverse=True)[:12]:
    print(f"  {v:.3f}  {m1:20s} <-> {m2}")
json.dump({"outputs": out}, open(os.path.join(OUT,"10_duplicate_probe.json"),"w",encoding="utf-8"), ensure_ascii=False, indent=2)
print("[saved] 10_duplicate_probe.json")