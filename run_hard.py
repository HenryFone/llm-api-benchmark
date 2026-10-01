import sys, os, time, json, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bench_lib import *

H = {}
H["h1_logic"] = ("只输出一个最终答案，不要过程。\n"
  "三个盒子分别贴有标签：'苹果'、'橘子'、'苹果和橘子'。三个标签全部贴错。"
  "你只能从一个盒子里拿出一个水果看，问最少需要拿几次才能确定所有盒子的真实内容？只回答数字。")
H["h2_arith"] = ("只输出最终数字，不要过程。\n"
  "某商品先涨价 20%，再打 8 折，最后又降价 15%。问最终价格相对原价是涨了还是跌了？涨跌百分之多少？"
  "请输出形如 跌7.25 的格式（保留2位小数）。")
H["h3_needle"] = None  # built below
needle_data = "\n".join(f"record {i:03d}: id={i*13%1000:03d} flag={'T' if i%7==0 else 'F'}" for i in range(300))
H["h3_needle"] = ("下面是一份记录。请找出 flag=T 且 id 数值最大的那一条，只输出它的 record 编号（三位数字）。\n" + needle_data)
H["h4_constraint"] = ("用中文写一段话，同时满足：\n"
  "1) 恰好 3 句话（以。！？结尾算一句）\n2) 每句话都必须包含“代码”二字\n"
  "3) 全段总字数不超过 60 个汉字\n4) 不得使用“的”字\n"
  "只输出这段话。")

grades = {
 "h1_logic": lambda t: (10 if re.search(r"\b1\b", t) else 0, {"ans": t.strip()[:40], "expected": "1"}),
 "h2_arith": lambda t: (10 if "跌" in t and ("18.4" in t or "18.40" in t or "18.39" in t or "18.3" in t or "18.5" in t) else 0,
                        {"ans": t.strip()[:60], "expected": "跌18.40（1.2*0.8*0.85=0.816）"}),
 "h3_needle": None,
 "h4_constraint": None,
}

def grade(tid, t):
    t = (t or "").strip()
    if tid == "h1_logic": return grades[tid](t)
    if tid == "h2_arith": return grades[tid](t)
    if tid == "h3_needle":
        best = max(i for i in range(300) if i%7==0)
        want = f"{best:03d}"
        # 还需满足 id 最大：i%7==0 且 id=i*13%1000 最大
        mx = max((i*13%1000, i) for i in range(300) if i%7==0)[1]
        want = f"{mx:03d}"
        ok = want in t
        return (10 if ok else 0), {"ans": t[:60], "expected_record": want, "usage_note": "长上下文检索"}
    if tid == "h4_constraint":
        sents = [s for s in re.split(r"[。！？]", t) if s.strip()]
        cnt = len(sents)
        every = all("代码" in s for s in sents) if sents else False
        hanzi = len(re.findall(r"[\u4e00-\u9fff]", t))
        nod = "的" not in t
        c = {"恰好3句": cnt==3, "每句含代码": every, "汉字<=60": hanzi<=60, "不含的": nod}
        return round(sum(c.values())/4*10,1), {**c, "hanzi": hanzi, "sentences": sents}
    return 0, {}

res = {"meta": {"time": time.strftime("%Y-%m-%d %H:%M:%S"), "note": "harder battery for discrimination"}, "models": {}}
for m in MODELS:
    print("\n########", m, flush=True)
    res["models"][m] = {}
    for tid, pr in H.items():
        r = call(m, pr, max_out=1500, temperature=0, timeout=420)
        sc, det = grade(tid, r.get("text"))
        u = r.get("usage") or {}
        res["models"][m][tid] = {"score": sc, "elapsed": round(r.get("elapsed",0),2),
                                 "in_tokens": u.get("input_tokens"), "out_tokens": u.get("output_tokens"),
                                 "raw": (r.get("text") or "")[:1200], "detail": det}
        print(f"  {tid:14s} score={sc:5}  {round(r.get('elapsed',0),2):6}s  in={u.get('input_tokens')} out={u.get('output_tokens')}", flush=True)
    res["models"][m]["_avg"] = round(sum(v["score"] for v in res["models"][m].values())/len(H),2)
    print("  >>> AVG", res["models"][m]["_avg"], flush=True)
save("06_hard.json", res)