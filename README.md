# LLM API Benchmark

一套**可复现的第三方大模型 API 测评工具**，回答一个很实际的问题：

> 我买的中转 API，模型到底是不是它自称的那个？速度、能力、身份，到底靠不靠谱？

市面上大部分测评是"发一条消息看它像不像"，结论不可复现、也无法证伪。这个工具把测评拆成**四个可量化的维度**，每一项都有原始数据落盘，任何人都能重跑。

## 四个测评维度

| 维度 | 权重（可改） | 测什么 |
| --- | --- | --- |
| 连通可用性 | 25% | 基础请求、连续 10 次、并发 4 路、长上下文、非法模型名的报错是否正确 |
| 速度 | 25% | 短答延迟、长答延迟、吐字速度 (tok/s)、首字延迟 (TTFT)、抖动 |
| 能力 | 30% | 指令遵循、数学、代码生成、代码调试、JSON Schema、中文理解、幻觉控制、工具调用 |
| 原厂相似度 | 20% | 同一身份问题问 8 次，看模型是否稳定地自称同一个厂商 |

> 权重只是默认值，在 `make_scorecard.py` 的 `W` 字典里改。

## 一个真实发现（说明这个工具能挖出什么）

用这套方法测某个中转端点时，出现了**同一次测试内自相矛盾**的情况：

- 同一个模型槽位，问 8 次身份，有几次说自己是 DeepSeek，有几次说自己是 Anthropic Claude；
- 架构问题回答自己是 Claude，归属问题又回答 DeepSeek；
- 换一个版本槽位，自称 Claude 的比例更高。

同时也有反向证据值得注意：不同模型的 **input_token 计数**在相同输入下逐字节一致，说明**分词数由网关统一计算，不能当成"模型同源"的铁证**。所以报告里区分"事实"和"推测"——这是这套工具的设计原则。

## 快速开始

### 1. 配置端点（二选一）

**方式 A：环境变量**

```powershell
$env:BENCH_BASE_URL = "https://your-endpoint.example/v1"
$env:BENCH_API_KEY  = "sk-..."
$env:BENCH_MODELS   = "model-a,model-b,model-c"
```

**方式 B：本地配置文件**

```powershell
Copy-Item bench.example.json bench.local.json
notepad bench.local.json
```

`bench.local.json` 已经写进 `.gitignore`，不会被提交。

### 2. 跑测评

```powershell
python run_connectivity.py    # 连通性
python run_speed.py           # 速度
python run_capability.py      # 能力
python run_vendor.py          # 原厂相似度 / 身份
python run_tokenizer.py       # 分词器指纹
python make_scorecard.py      # 汇总成 xlsx + 评分汇总.json
```

每个脚本都会把原始 JSON 写进 `results/`。**保留原始数据是刻意的设计**：结论可以被复查、被推翻、被重新判分（本仓库就带着一次"重新判分"的记录，见下）。

### 3. 看结果

```powershell
python make_scorecard.py
```

生成 `评分表.xlsx`（综合评分 / 原始指标 / 能力明细三个 sheet）和 `评分汇总.json`。

## 目录说明

| 路径 | 内容 |
| --- | --- |
| `bench_lib.py` | 请求封装、配置加载、流式解析 |
| `run_*.py` | 各维度测评脚本 |
| `make_scorecard.py` | 汇总打分、生成 xlsx |
| `results-sample/` | 一份脱敏后的样例输出，给你看数据长什么样 |
| `bench.example.json` | 配置模板 |

## 设计原则

1. **端点不写死**：代码里没有任何私有域名，全部走配置。
2. **原始数据留档**：每个结论都能追溯到原始响应。
3. **区分事实与推测**：报告里明确标注哪些是实测事实、哪些只是推测。
4. **允许重新判分**：本题库保留了一次真实的"判分修正"记录（数学题的期望值写错了，复判时改为正确答案，并把 `03_capability_regraded.json` 一并留档）。**测评工具本身出错也是要留痕的。**

## 已知边界

- 只测 Responses API 风格；如要测 Chat Completions，把 `BENCH_API_STYLE=chat` 打开（基础封装支持，脚本未逐一适配）。
- 身份题的结论**不是权重鉴定**，只能作为"需要警惕"的信号，不能作为"这个模型就是 X"的证明。
- 速度受上游共享额度、网络、时段影响，只代表测试时点的值。
- 能力题区分度有限（多数强模型都是满分），要进一步区分需要更难的题，成本也会上升。

## License

MIT