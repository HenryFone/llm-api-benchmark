import sys, os, time, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bench_lib import *
import urllib.request

# --- headers per model ---
print("=== response headers ===")
for m in MODELS:
    body = json.dumps({"model":m,"input":"hi","max_output_tokens":8}).encode()
    req = urllib.request.Request(URL, data=body, headers={"Authorization":"Bearer "+TOK,"Content-Type":"application/json"})
    r = urllib.request.urlopen(req, timeout=120); r.read()
    hs = {k:v for k,v in r.getheaders()}
    keep = {k:v for k,v in hs.items() if k.lower() in ("server","date","x-request-id","cf-ray","via","x-served-by","content-type")}
    print(f"  {m:20s} {json.dumps(keep, ensure_ascii=False)}")

# --- deepseek identity repeat ---
print("\n=== deepseek-v4.1-flash identity x6 ===")
q = "只说一句话：你是哪家公司开发的什么模型？不要回避，直接给答案。"
hits = []
for i in range(6):
    r = call("deepseek-v4.1-flash", q, max_out=300, temperature=0, timeout=200)
    t = (r.get("text") or "").strip().replace("\n"," ")
    hits.append(t)
    print(f"  [{i}] {t[:180]}")
for kw in ["Claude","Anthropic","DeepSeek","深度求索","OpenAI","GPT"]:
    print(f"  关键词 {kw:12s} 出现 {sum(1 for h in hits if kw in h)}/6")
json.dump({"deepseek_identity_6": hits}, open(os.path.join(OUT,"05_identity_repeat.json"),"w",encoding="utf-8"), ensure_ascii=False, indent=2)
print("[saved] 05_identity_repeat.json")