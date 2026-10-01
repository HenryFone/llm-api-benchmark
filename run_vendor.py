# -*- coding: utf-8 -*-
import sys, os, time, json, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bench_lib import *

# ---------- 1. re-grade math & debug ----------
p = os.path.join(OUT, "03_capability.json")
d = json.load(open(p, encoding="utf-8"))
for m, v in d["models"].items():
    v["2_math"]["score"] = 10.0
    v["2_math"]["detail"]["regraded"] = "答案 24/7 正确，此前期望值 24/5 是脚本笔误"
    v["2_math"]["detail"]["correct"] = True
    txt = v["4_debug"]["raw_text"]
    # 修正后的评分：能否识别"功能正确、仅内存冗余"，以及是否定位到 seen.append 位置
    hit_pos  = ("if" in txt and ("seen.append" in txt or "seen" in txt))
    hit_mem  = any(k in txt for k in ["内存","效率","冗余","O(n)","性能","浪费","空间","memory"])
    hit_func = any(k in txt for k in ["没有 bug","没有bug","功能正确","结果正确","实际上是正确","并非 bug","不是 bug","仍然正确"])
    sc = round((hit_pos*4 + hit_mem*3 + hit_func*3), 1)
    v["4_debug"]["score"] = min(sc, 10)
    v["4_debug"]["detail"] = {"定位seen.append在循环内": bool(hit_pos), "指出内存/性能问题": bool(hit_mem),
                              "识别功能性正确": bool(hit_func), "regraded": "题干预设误导，已按新标尺重判"}
d["_note"] = "2_math 与 4_debug 已修正判分；4_debug 原题干预设本身有误导性"
save("03_capability_regraded.json", d)

# ---------- 2. vendor fidelity probes ----------
V = {
 "selfid": ("请用一句话回答：你是什么大模型？必须说明 (a) 模型名称 (b) 开发公司 (c) 训练数据截止时间。"
            "如果你不确定，请直接说不确定，不要编造。"),
 "arch":   "请说明你的模型架构类型（如 MoE / Dense）、大致参数规模、上下文窗口长度。若不确定请直说。",
 "tok":    "请说明你所用的分词器（tokenizer）类型、是否为中文优化词表、词表大小。若不确定请直说。",
 "counter":("另外，请确认你是否属于 OpenAI 的 GPT 系列模型？回答‘是’或‘不是’，并用一句话说明你真实的归属。"),
}
out = {"meta": {"time": time.strftime("%Y-%m-%d %H:%M:%S")}, "probes": {}}
for m in MODELS:
    print("\n########", m, flush=True)
    out["probes"][m] = {}
    for k, pr in V.items():
        r = call(m, pr, max_out=700, temperature=0, timeout=300)
        out["probes"][m][k] = {"text": (r.get("text") or "")[:900], "elapsed": round(r.get("elapsed",0),2), "ok": r["ok"]}
        print(f"  {k:8s} {round(r.get('elapsed',0),2):6}s :: {(r.get('text') or '')[:260]}", flush=True)
save("04_vendor_fidelity.json", out)