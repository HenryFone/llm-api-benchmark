# -*- coding: utf-8 -*-
import os, json
OUT = os.path.dirname(os.path.abspath(__file__))

FINAL = {
 "deepseek-v4.1-flash": {
   "connectivity": 10.0, "speed": 9.2, "capability": 9.7, "fidelity": 3.0,
   "raw": {"短响应": "2.46 s", "长响应": "33.1 s", "吞吐": "48.8 tok/s",
           "连通": "10/10 + 并发4/4", "长上下文": "7.7k 正常", "身份自认": "DeepSeek 2/8、Claude 5/8",
           "工具调用": "通过", "流式": "思考摘要+正文，逐字", "输出token": 1600}
 },
 "glm-5.3-flash": {
   "connectivity": 10.0, "speed": 6.5, "capability": 9.4, "fidelity": 7.5,
   "raw": {"短响应": "5.64 s", "长响应": "30.9 s", "吞吐": "48.7 tok/s",
           "连通": "10/10 + 并发4/4", "长上下文": "8.4k 正常", "身份自认": "GLM 8/8",
           "工具调用": "通过", "流式": "直接正文，逐字", "输出token": 1505}
 },
 "kimi-k3": {
   "connectivity": 10.0, "speed": 3.0, "capability": 8.8, "fidelity": 9.0,
   "raw": {"短响应": "7.14 s", "长响应": "52.7 s", "吞吐": "28.6 tok/s",
           "连通": "10/10 + 并发4/4", "长上下文": "7.8k 正常", "身份自认": "Kimi 8/8",
           "工具调用": "通过", "流式": "思考摘要+正文，逐字", "输出token": 1501}
 },
}
W = {"connectivity": 0.25, "speed": 0.25, "capability": 0.30, "fidelity": 0.20}
for m, v in FINAL.items():
    v["total"] = round(sum(v[k]*W[k] for k in W), 2)
json.dump({"weights": W, "models": FINAL}, open(os.path.join(OUT, "评分汇总.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=2)

# -------- xlsx scorecard --------
try:
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter
except ImportError:
    print("openpyxl 缺失，跳过 xlsx"); raise SystemExit

wb = Workbook(); ws = wb.active; ws.title = "综合评分"
thin = Side(style="thin", color="BFBFBF")
bd = Border(left=thin, right=thin, top=thin, bottom=thin)
hdr_fill = PatternFill("solid", fgColor="2F5597")
hdr_font = Font(bold=True, color="FFFFFF", size=11)
title_font = Font(bold=True, size=14, color="1F3864")

ws["A1"] = "LLM API Benchmark · 综合评分表"
ws["A1"].font = title_font
ws["A2"] = "权重：连通25% 速度25% 能力30% 原厂相似度20% | 端点与模型名请按本次实测填写"
ws["A2"].font = Font(size=9, color="808080")

cols = ["模型", "连通可用性 (25%)", "速度 (25%)", "能力多维度 (30%)", "原厂相似度 (20%)", "综合总分", "一句话点评"]
r = 4
for i, c in enumerate(cols, 1):
    cell = ws.cell(row=r, column=i, value=c)
    cell.fill = hdr_fill; cell.font = hdr_font; cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True); cell.border = bd
comment = {
 "deepseek-v4.1-flash": "最快、能力满格，但自称Claude比例偏高，身份存疑",
 "glm-5.3-flash": "速度均衡、身份稳定，综合第一",
 "kimi-k3": "身份最干净，但明显慢一档",
}
for i, (m, v) in enumerate(FINAL.items()):
    rr = r+1+i
    vals = [m, v["connectivity"], v["speed"], v["capability"], v["fidelity"], v["total"], comment[m]]
    for j, val in enumerate(vals, 1):
        cell = ws.cell(row=rr, column=j, value=val); cell.border = bd
        cell.alignment = Alignment(horizontal="center" if j in (2,3,4,5,6) else "left", vertical="center", wrap_text=True)
    ws.cell(row=rr, column=6).font = Font(bold=True, size=12)

# detail sheet
ws2 = wb.create_sheet("原始指标")
cols2 = ["模型", "短响应均值", "长响应均值", "吞吐(tok/s)", "连通成功", "并发4路", "身份自认", "工具调用", "流式方式"]
for i, c in enumerate(cols2, 1):
    cell = ws2.cell(row=1, column=i, value=c); cell.fill = hdr_fill; cell.font = hdr_font
    cell.alignment = Alignment(horizontal="center", wrap_text=True); cell.border = bd
for i, (m, v) in enumerate(FINAL.items()):
    rr = 2+i; d = v["raw"]
    vals = [m, d["短响应"], d["长响应"], d["吞吐"], d["连通"], "全部成功", d["身份自认"], d["工具调用"], d["流式"]]
    for j, val in enumerate(vals, 1):
        cell = ws2.cell(row=rr, column=j, value=val); cell.border = bd
        cell.alignment = Alignment(horizontal="center" if j>1 else "left", wrap_text=True)

# dimensions sheet
ws3 = wb.create_sheet("能力明细")
cols3 = ["能力项", "deepseek-v4.1-flash", "glm-5.3-flash", "kimi-k3", "说明"]
for i, c in enumerate(cols3, 1):
    cell = ws3.cell(row=1, column=i, value=c); cell.fill = hdr_fill; cell.font = hdr_font
    cell.alignment = Alignment(horizontal="center", wrap_text=True); cell.border = bd
rows = [
 ("指令遵循", 10, 10, 4, "Kimi 把3条要点挤在一行，未满足换行要求"),
 ("数学推理", 10, 10, 10, "三管道全部答对 24/7"),
 ("代码生成", 10, 10, 10, "最长回文子串，三管道100%通过测试用例"),
 ("代码调试", 10, 9, 9, "三管道都识别出'功能正确'；DeepSeek额外点明 seen 列表内存冗余"),
 ("结构化输出", 10, 10, 10, "JSON Schema 全部合规"),
 ("中文理解", 10, 10, 10, "差点没赶上 = 赶上了，全对"),
 ("幻觉控制", 10, 10, 10, "均识破虚构电影《量子回声》"),
 ("工具调用", 10, 10, 10, "均正确发起 get_weather(北京)"),
 ("困难题×4", 10, 10, 10, "逻辑/连续百分比/长文检索/复合约束，全满分"),
]
for i, row in enumerate(rows):
    rr = 2+i
    for j, val in enumerate(row, 1):
        cell = ws3.cell(row=rr, column=j, value=val); cell.border = bd
        cell.alignment = Alignment(horizontal="left" if j in (1,5) else "center", wrap_text=True)

# simpler widths
for ws_, widths in [(ws,[14,16,12,16,18,12,44]), (ws2,[22,12,12,13,16,12,26,12,26]), (ws3,[14,20,16,12,50])]:
    for i, wd in enumerate(widths, 1):
        ws_.column_dimensions[get_column_letter(i)].width = wd
for ws_ in (ws, ws2, ws3):
    ws_.freeze_panes = "A2" if ws_ is not ws else "A5"
    ws_.row_dimensions[1].height = 24

p = os.path.join(OUT, "评分表.xlsx")
wb.save(p)
print("[saved]", p)