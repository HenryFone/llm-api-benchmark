import sys, os, time, json, re, ast
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bench_lib import *

# ---------------- tasks ----------------
T = {}

T["1_instruction"] = {
 "name": "指令遵循",
 "prompt": ("请严格按以下5条要求输出：\n"
   "1) 第一行必须恰好是 ###BEGIN\n"
   "2) 第二行列出恰好 3 个要点，每条以 -  开头，每条不超过 12 个汉字\n"
   "3) 全部内容使用中文\n"
   "4) 最后一行必须恰好是 ###END\n"
   "5) 除上述内容外不得有任何多余文字\n"
   "主题：如何提高睡眠质量。"),
 "check": None}

T["2_math"] = {
 "name": "数学推理",
 "prompt": ("一个水池有甲、乙两根进水管和一根排水管。单开甲管 6 小时注满，单开乙管 4 小时注满，"
   "单开排水管 8 小时排空。三管同开，注满水池需要多少小时？"
   "只输出最简分数形式的答案，例如 12/5，不要任何其他文字。"),
 "check": lambda t: t.strip().strip('。') in ["24/5","4.8","24/5小时"]}

T["3_code"] = {
 "name": "代码生成",
 "prompt": ("用 Python 实现函数 `def longest_palindrome(s: str) -> str:`，返回 s 中最长的回文子串。"
   "只输出一个 ```python 代码块，不要任何解释文字。"),
 "check": None}

T["4_debug"] = {
 "name": "代码调试",
 "prompt": ("下面这段 Python 代码有 bug，请指出 bug 在哪一行、原因是什么，并给出修正后的那一行。\n"
   "```\n"
   "def dedup_keep_order(seq):\n"
   "    seen = []\n"
   "    out = []\n"
   "    for x in seq:\n"
   "        if x not in seen:\n"
   "            out.append(x)\n"
   "        seen.append(x)\n"
   "    return out\n"
   "```\n"
   "要求：代码本身是正确的，但**运行结果并非预期**。请说明缺陷并给出修正行。"),
 "check": None}

T["5_json"] = {
 "name": "结构化输出",
 "prompt": ("请只输出一个 JSON 对象，不要 markdown 代码块，不要解释。Schema："
   '{"name": string, "age": integer, "tags": [string, string], "active": boolean}。'
   "内容：姓名小明，年龄 28，标签为 python 与 codex，active 为真。"),
 "check": None}

T["6_chinese"] = {
 "name": "中文理解",
 "prompt": ("判断下面句子的含义，只回答一个选项字母，不要解释。\n"
   "『他差点没赶上末班车。』\n"
   "A. 他没赶上  B. 他赶上了  C. 无法判断"),
 "check": lambda t: t.strip()[:1].upper() == "B"}

T["7_hallucination"] = {
 "name": "幻觉控制",
 "prompt": ("请问《星际穿越》导演克里斯托弗·诺兰 2019 年执导的电影《量子回声》获得了第92届奥斯卡最佳影片奖吗？请简短回答。"),
 "check": None}

T["8_toolcall"] = {
 "name": "工具调用",
 "prompt": "北京现在的天气怎么样？",
 "tools": [{"type":"function","name":"get_weather","description":"查询某城市当前天气",
            "parameters":{"type":"object","properties":{"city":{"type":"string","description":"城市名"}},
                          "required":["city"]}}],
 "check": None}

# ---------------- runner ----------------
res = {"meta": {"time": time.strftime("%Y-%m-%d %H:%M:%S"), "base_url": BASE}, "models": {}}

def grade(tid, task, r):
    t = (r.get("text") or "")
    if tid == "1_instruction":
        lines = [l for l in t.strip().splitlines() if l.strip() != ""]
        checks = {
          "首行###BEGIN": bool(lines) and lines[0].strip() == "###BEGIN",
          "末行###END": bool(lines) and lines[-1].strip() == "###END",
          "恰好3条要点": sum(1 for l in lines if l.strip().startswith("-")) == 3,
          "每条<=12汉字": all(len(re.findall(r"[\u4e00-\u9fff]", l)) <= 12 for l in lines if l.strip().startswith("-")),
          "无多余内容": len(lines) == 5,
        }
        return sum(checks.values())/len(checks)*10, checks
    if tid == "2_math":
        ok = task["check"](t) if t else False
        return (10 if ok else 0), {"answer": t.strip()[:40], "expected": "24/5"}
    if tid == "3_code":
        code = None
        m = re.search(r"```(?:python)?\s*(.*?)```", t, re.S)
        code = m.group(1) if m else t
        try:
            ns = {}
            exec(code, ns)
            fn = ns.get("longest_palindrome")
            cases = [("babad", {"bab","aba"}), ("cbbd", {"bb"}), ("a", {"a"}), ("", {""}), ("racecar", {"racecar"})]
            passed = 0
            for inp, exp in cases:
                try:
                    got = fn(inp)
                    if got in exp or (isinstance(got,str) and got in exp): passed += 1
                except Exception:
                    pass
            return round(passed/len(cases)*10, 1), {"passed": passed, "total": len(cases), "code_head": (code or "")[:120]}
        except Exception as e:
            return 0, {"exec_error": f"{type(e).__name__}: {e}", "code_head": (code or "")[:120]}
    if tid == "4_debug":
        keys = {"seen.append": t.find("seen.append") >= 0 or "seen.add" in t,
                "位置": ("循环内" in t) or ("无条件" in t) or ("无论" in t) or ("都执行" in t),
                "去重集合": ("set" in t or "集合" in t)}
        return round(sum(keys.values())/len(keys)*10, 1), keys
    if tid == "5_json":
        raw = t.strip()
        raw = re.sub(r"^```(?:json)?|```$", "", raw, flags=re.M).strip()
        try:
            d = json.loads(raw)
            ok = (isinstance(d.get("name"), str) and isinstance(d.get("age"), int) and not isinstance(d.get("age"), bool)
                  and isinstance(d.get("tags"), list) and len(d["tags"]) == 2
                  and all(isinstance(x,str) for x in d["tags"]) and isinstance(d.get("active"), bool))
            return (10 if ok else 5), {"parsed": True, "schema_ok": ok, "obj": d}
        except Exception as e:
            return 0, {"parsed": False, "err": str(e)[:100], "raw": raw[:150]}
    if tid == "6_chinese":
        ok = task["check"](t) if t else False
        return (10 if ok else 0), {"answer": t.strip()[:20], "expected": "B"}
    if tid == "7_hallucination":
        good = any(k in t for k in ["没有","不存在","未","虚构","无法确认","查不到","并无","不实","误","不确定","未有"])
        bad  = any(k in t for k in ["获得了","荣获","赢得了","是的","确实获得"])
        score = 10 if good and not bad else (4 if "没有" in t or "不存" in t else 0)
        return score, {"said": t.strip()[:160], "uncertainty": good}
    if tid == "8_toolcall":
        calls = [o for o in (r.get("resp") or {}).get("output", []) if o.get("type") == "function_call"]
        ok = any(c.get("name") == "get_weather" and "北京" in str(c.get("arguments","")) for c in calls)
        return (10 if ok else 0), {"function_calls": [{"name": c.get("name"), "args": c.get("arguments")} for c in calls],
                                   "text": t[:120]}
    return 0, {}

for m in MODELS:
    print("\n########", m, flush=True)
    res["models"][m] = {}
    for tid, task in T.items():
        r = call(m, task["prompt"], max_out=1200, temperature=0, tools=task.get("tools"), timeout=300)
        score, detail = grade(tid, task, r)
        res["models"][m][tid] = {"name": task["name"], "score": score,
                                 "elapsed": round(r.get("elapsed",0),2), "ok": r["ok"],
                                 "raw_text": (r.get("text") or "")[:1500], "detail": detail}
        print(f"  {tid:16s} score={score:5} {round(r.get('elapsed',0),2):6}s  {task['name']}", flush=True)
    avg = sum(v["score"] for v in res["models"][m].values())/len(T)
    res["models"][m]["_avg"] = round(avg,2)
    print("  >>> AVG", round(avg,2), flush=True)
save("03_capability.json", res)