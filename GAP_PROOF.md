# GAP_PROOF — sftcheck（SFT 微调数据集预检器）

状态：S0 立项（2026-10-08，D-S0-1）。本文件是"为什么做这个项目"的证据档案：全部关键数字与来源均为当日实抓，非沿用调研稿。结构对齐 charaudit/GAP_PROOF.md。

## 1. 需求侧：数据集格式问题是大规模反复出现的真实痛点

**锚点仓库**：[hiyouga/LlamaFactory](https://github.com/hiyouga/LlamaFactory)——微调框架中事实上的数据集格式集散地。2026-10-08 实抓：**75,347★、open issues（含 PR）1,176、最近 push 2026-09-28**（2026-10-07 调研抓数为 75,339★/1,172，一日之差如实记录）。

格式类问题在 issue 区**高频复发**（2026-10-08 search API 实抓，state:open）：

| 搜索词 | 命中 open issues |
|---|---|
| `sharegpt` | 30 |
| `alpaca` | 61 |
| `dataset format` | 109 |

**代表性个案（四条逐一复查，标题/日期/状态与调研稿一致）**：

| Issue | 标题（实抓） | 日期 | 状态 |
|---|---|---|---|
| [#7577](https://github.com/hiyouga/LlamaFactory/issues/7577) | KeyError: 'instruction' when using local sharegpt formatted dataset with llama3 | 2025-04-02 | closed |
| [#6878](https://github.com/hiyouga/LlamaFactory/issues/6878) | sharegpt dataset convert error | 2025-02-10 | closed |
| [#2471](https://github.com/hiyouga/LlamaFactory/issues/2471) | Sharegpt datasets not working. Error during dataset conversion: Unsupported cast | 2024-02-12 | closed |
| [#3793](https://github.com/hiyouga/LlamaFactory/issues/3793) | 偏好数据集 Supervised Fine-Tuning 有问题 | 2024-05-17 | closed |

时间跨度 2024-02 → 2025-04 仍在出现（#2471 → #7577），同类错误以不同措辞反复被报告——用户在训练失败后才拿到一条框架深层报错，而不是训练前拿到一份"第 N 条样本、字段 X、问题 Y"的预检报告。

## 2. 规范侧：三方言的事实标准定义

LlamaFactory 官方 [data/README.md](https://github.com/hiyouga/LlamaFactory/blob/main/data/README.md)（2026-10-08 实抓）：**"Currently we support datasets in alpaca and sharegpt format"**，文件类型 json/jsonl/csv/parquet/arrow；alpaca（instruction/input/output 三字段族）与 sharegpt（conversations + tags 族）为主方言，OpenAI messages 格式是 sharegpt 内最常见的转换来源。sftcheck 的校验规范以此文档为准绳（不自行发明标准），版本随上游更新在 WORKLOG 记录。

## 3. 供给侧：训练前独立预检确属空白

- **框架内建缓解**：ms-swift（[modelscope/ms-swift](https://github.com/modelscope/ms-swift)，实抓 15,787★、最近 push 2026-10-07，活跃）等框架在加载阶段过滤/报错——但那发生在**训练启动时**，报错信息深埋在 Arrow/框架栈里，且各框架只认自家方言组合。
- **独立、训练前、跨方言的预检小件**：调研与本次复查均未发现同类物（不宣称"不存在于全世界"，只声明"我们没找到"；若发现先例将如实补充）。
- sftcheck 的差异化：**逐行错误定位 + 修复建议的审计报告**（行号/样本序号、字段、违规类型、建议动作），与组合内 siftan 正交（那边查 eval 泄漏，这边查训练集结构）。

## 4. 形态与范围（S2 细化）

- 输入：json/jsonl 目录或单文件；方言自动探测 + 显式指定。
- 校验层级：JSON 合法性 → 方言字段结构 → 规则类（role 交替、空消息、stage 匹配、样本重复哈希、中文文本质量信号如全角空格混入/繁简混杂/乱码）。
- 输出：逐行审计报告 + 汇总统计；零必装依赖（json/csv/arrow 中 arrow 类型起步仅支持 json/jsonl，csv/parquet 降级说明）。
- 风险（调研稿原文仍有效）：单品价值感知偏低，需靠"训练前必查"心智与 LlamaFactory 社区导流；方言规则随上游演进需跟版维护。

## 5. 来源清单（全部 2026-10-08 实抓）

| 来源 | 内容 | 抓取方式 |
|---|---|---|
| api.github.com/repos/hiyouga/LlamaFactory | 75,347★ / 1,176 open issues / pushed 2026-09-28 | REST API |
| api.github.com issues #7577 #6878 #2471 #3793 | 标题、日期、状态逐一复核 | REST API |
| api.github.com search/issues ×3 | sharegpt 30 / alpaca 61 / dataset format 109（open） | Search API |
| LlamaFactory data/README.md | alpaca/sharegpt 双方言声明与字段规范 | contents API |
| api.github.com/repos/modelscope/ms-swift | 15,787★ / pushed 2026-10-07 | REST API |
