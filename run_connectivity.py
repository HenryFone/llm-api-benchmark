import sys, os, time, json, statistics
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bench_lib import *

results = {"connectivity": {}, "speed": {}, "meta": {"base_url": BASE, "time": time.strftime("%Y-%m-%d %H:%M:%S")}}

# ---------- A. Connectivity ----------
print("=== A. Connectivity ===", flush=True)
for m in MODELS:
    rec = {}
    # A1 simple
    r = call(m, "Reply with exactly: OK", max_out=64)
    rec["basic"] = {"ok": r["ok"], "status": r.get("status"), "elapsed": round(r.get("elapsed",0),2),
                    "text": (r.get("text") or "")[:200], "err": r.get("error","")[:200]}
    # A2 10x serial
    ok = 0; lat = []
    for i in range(10):
        rr = call(m, f"Say the number {i}.", max_out=24)
        if rr["ok"] and rr["status"] == 200: ok += 1; lat.append(rr["elapsed"])
    rec["serial_10"] = {"success": ok, "latency_avg": round(statistics.mean(lat),2) if lat else None,
                        "latency_min": round(min(lat),2) if lat else None, "latency_max": round(max(lat),2) if lat else None}
    # A3 concurrent 4
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=4) as ex:
        rs = list(ex.map(lambda _: call(m, "ping", max_out=16), range(4)))
    rec["concurrent_4"] = {"success": sum(1 for x in rs if x["ok"]), "wall": round(time.time()-t0,2)}
    # A4 long context (~8k tokens)
    filler = "\n".join(f"row {i}: value={i*7%97}" for i in range(900))
    rl = call(m, f"Count the number of lines in the data below and reply with just the number.\n{filler}", max_out=64)
    rec["long_ctx"] = {"ok": rl["ok"], "status": rl.get("status"), "elapsed": round(rl.get("elapsed",0),2),
                       "usage_in": (rl.get("usage") or {}).get("input_tokens"), "text": (rl.get("text") or "")[:120],
                       "err": rl.get("error","")[:200]}
    results["connectivity"][m] = rec
    print(m, json.dumps(rec, ensure_ascii=False), flush=True)
save("01_connectivity.json", results)

# ---------- B. Invalid model / error handling ----------
print("\n=== B. Error handling ===", flush=True)
bad = call("not-a-real-model-xyz", "hi", max_out=16)
results["error_handling"] = {"status": bad.get("status"), "error": (bad.get("error") or "")[:400]}
print(json.dumps(results["error_handling"], ensure_ascii=False), flush=True)
save("01_connectivity.json", results)