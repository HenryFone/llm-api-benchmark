import sys, os, time, json, statistics
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bench_lib import *

SHORT = "只输出这一个数字：42"
LONG  = ("请写一篇恰好约400字的中文短文，主题是‘秋天的城市早晨’。"
         "要求：3个自然段，每段一个中心句，语言平实。不要标题，不要解释。")

res = {"meta": {"base_url": BASE, "time": time.strftime("%Y-%m-%d %H:%M:%S"),
                "note": "上游非逐字流式，已用非流式计时；ttft 参考流式首包时间"}, "raw": {}}
for m in MODELS:
    print("=== speed:", m, flush=True)
    entry = {"short": [], "long": [], "stream_probe": None}
    for tag, prompt, mo in [("short", SHORT, 32), ("long", LONG, 1600)]:
        for i in range(3):
            r = call(m, prompt, max_out=mo, temperature=0, timeout=300)
            u = r.get("usage") or {}
            ot = u.get("output_tokens") or 0
            rec = {"ok": r["ok"], "elapsed": round(r.get("elapsed",0),2),
                   "out_tokens": ot, "chars": len(r.get("text") or ""),
                   "tps": round(ot/max(r.get("elapsed",0.001),0.001),2) if ot else None,
                   "err": (r.get("error") or "")[:200]}
            entry[tag].append(rec)
            print(" ", tag, i, json.dumps(rec, ensure_ascii=False), flush=True)
    # stream probe for first-packet time
    r = call(m, LONG, max_out=1600, temperature=0, stream=True, timeout=300)
    entry["stream_probe"] = {"first_packet_s": round(r["ttft"],2) if r.get("ttft") else None,
                             "total_s": round(r.get("elapsed",0),2), "chars": len(r.get("text") or "")}
    print("  stream_probe", json.dumps(entry["stream_probe"], ensure_ascii=False), flush=True)
    res["raw"][m] = entry
    summary = {}
    for tag in ("short", "long"):
        rr = [x for x in entry[tag] if x["ok"]]
        if rr:
            summary[tag] = {
                "total_avg": round(statistics.mean(x["elapsed"] for x in rr), 2),
                "total_min": round(min(x["elapsed"] for x in rr), 2),
                "total_max": round(max(x["elapsed"] for x in rr), 2),
                "out_tokens_avg": round(statistics.mean(x["out_tokens"] for x in rr), 1),
                "tps_avg": round(statistics.mean([x["tps"] for x in rr if x["tps"]]), 2),
            }
    summary["stream_first_packet"] = entry["stream_probe"]["first_packet_s"]
    res.setdefault("summary", {})[m] = summary
    print("SUMMARY", m, json.dumps(summary, ensure_ascii=False), flush=True)
save("02_speed.json", res)