# REPORT — The Mines in the Dataset (sftcheck) · 0.1.0a1

项目报告（2026-10-08）。面向评估者：这是什么、做到什么程度、证据在哪、边界在哪。开发过程账目见 `WORKLOG.md`，路线见 `DESIGN.md`/`GAP_PROOF.md`。

## 1. 一句话定位

SFT 微调数据集的**训练前结构预检器**：alpaca / sharegpt / OpenAI 三方言，逐样本定位 + 规则编号 + 修复建议的审计报告；CLI 退出码可直接做训练门禁。中文优先。

## 2. 能力清单（34 测试全绿）

- **方言**：alpaca / sharegpt / OpenAI 自动探测 + 显式指定；规范锚定 LlamaFactory `data/README.md`（blob `e43e0eed…`，报告内嵌 `spec_version`）。
- **规则 R001–R060**：解析失败（jsonl 坏行隔离）、方言不可识别（R009）、必填字段缺失（R010，对照 #7577 KeyError）、类型错误、空消息、role 奇偶位违规（R021）、OpenAI role 合法性、history 形状、偏好字段混入 SFT（R030，对照 #3793）、精确重复组（R040）、中文质量信号（R050，`--strict`）、非标准角色（R060）。
- **CLI 门禁**：退出码 0（无 ERROR）/ 1（有 ERROR，拦截训练）/ 2（不可读）。
- **证据模型**：`sample_index` 不变量（< total_samples，fuzz 守护——尾行坏行场景由 fuzz 抓出并修复）；`excerpt` 为违规值截断前缀。

## 3. 实测性能（2026-10-08，Python 3.13.2 / Win11 / 13 代酷睿；完整环境与命令见 benchmarks/RESULTS.md）

- **~18 万样本/秒、线性扩展**（1k=5.5ms / 10k=55.6ms / 50k=275.3ms，全规则）。
- 内存 O(n)（R040 全样本哈希 + json 数组整体加载）；超大文件建议 jsonl 分片——限制如实记录。

## 4. 可审计证据链

- 需求侧：LlamaFactory 75,347★，格式类 open issues 实抓（sharegpt 30 / alpaca 61 / dataset format 109），四条代表性 issue 逐一复核——见 GAP_PROOF.md 来源清单。
- 规范侧：以 data/README.md 原文为准绳并记录 blob 哈希；上游演进跟版并更新 spec_version。
- fuzz 修复记录：R009 编号拆分与 sample_index 钳制均为 fuzz 发现后修复，WORKLOG 如实记录（含修复前后基准对照）。
- 基准：种子化合成数据，命令可复跑。

## 5. 诚实边界（完整清单见 DESIGN §5）

- 结构干净 ≠ 语义优质 ≠ 训练成功；不做语义去重（精确哈希 only）；不承诺 axolotl/ms-swift 方言兼容。
- alpha（0.1.0a1），未上 PyPI；csv/parquet/arrow 明确降级提示。

## 6. 下一步

S5 收尾（干净 venv + quickstart 断言 + CI，沿用 charaudit 模式）→ S6/S7 发布（建仓 push 可执行；PyPI 等 Trusted Publisher）。
