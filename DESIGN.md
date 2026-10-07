# DESIGN — The Mines in the Dataset（sftcheck）

状态：S2 设计稿（2026-10-08，D-S2-1）。S3 实现以本文件为基准；实现中发现设计错误时回改本文件并在 WORKLOG 记录理由。
包名：`sftcheck`（S1 已查证：GitHub 重名 0、PyPI 未占用）；展示名：The Mines in the Dataset。

## 1. 定位与边界（先说不是什么）

- **是**：SFT 微调数据集的**训练前结构预检器**——对 alpaca / sharegpt / OpenAI 三方言做 JSON 结构校验与规则检查，产出逐行（逐样本）定位、含修复建议的审计报告。
- **不是**：不是语义质量评估器（不判断样本"好不好"）；不是训练成功的保证书（结构干净≠训练收敛）；不是数据清洗器（只报告，不改动数据）；不覆盖 preference/DPO/KTO 等非 SFT 数据形态（v0.1 只做 SFT，遇之明确提示 stage 不匹配）。
- 诚实总纲：**"0 issue" 只表示 "本规则集、本方言规范版本下零命中"**，不等于数据集干净。

## 2. 方言规范清单（准绳与版本锚点）

准绳：LlamaFactory 官方 `data/README.md`。锚点（2026-10-08 实抓）：仓库 commit `ce9dc9e072f8`（2026-09-28），文件 blob `e43e0eed0b48f6ed0054382346311550a2a1a927`（475 行）。规范随上游演进，sftcheck 每次跟版在 WORKLOG 记录新哈希；报告内嵌 `spec_version` 字符串。

### 2.1 alpaca（SFT）

| 字段 | 要求 | 缺失处理 |
|---|---|---|
| `instruction` | **必填**，字符串 | ERROR（对照 #7577 KeyError: 'instruction'） |
| `output` | **必填**，字符串（CoT 以 `<think>…</think>` 置于 response 内） | ERROR |
| `input` | 可选，字符串 | — |
| `system` | 可选，字符串 | — |
| `history` | 可选，`[[user, model], …]` 二元组列表；**history 的 response 也参与训练** | 元组非二元/元素非字符串 → WARN |

### 2.2 sharegpt（SFT）

| 字段 | 要求 |
|---|---|
| `conversations` | **必填**，对象列表，每对象 `{from, value}`（字段名可经 dataset_info 重映射——v0.1 只支持标准名，重映射提示为 INFO） |
| 角色 | `human / function_call / observation / gpt`；规范原文："human and observation should appear in odd positions, while gpt and function should appear in even positions"（奇偶位按 1 起算） |
| `system` / `tools` | 顶层可选字符串 |

### 2.3 openai（sharegpt 特例）

| 字段 | 要求 |
|---|---|
| `messages` | **必填**，`{role, content}` 列表；role ∈ `system/user/assistant`；首条可为 system（否则首条应为 user） |

## 3. API 草案（v0 草案，实现期允许微调签名）

```python
@dataclass(frozen=True)
class Issue:
    rule: str            # "R010" 等稳定编号
    severity: str        # ERROR / WARN / INFO
    sample_index: int    # 0 起；jsonl 为物理行号-1
    line_no: int | None  # jsonl 时的物理行号；json 数组为 None
    field: str           # "instruction" / "conversations[2].from" …
    message: str         # 中文，含修复建议
    excerpt: str         # 违规值截断摘录（≤80 字符），证据可回看

@dataclass(frozen=True)
class Report:
    path: str
    dialect: str             # alpaca / sharegpt / openai / unknown
    dialect_confidence: str  # detected / explicit
    total_samples: int
    issues: tuple[Issue, ...]
    spec_version: str        # 如 "llamafactory-data-readme@e43e0eed"
    def stats(self) -> dict[str, int]   # 按 rule 计数
    def summary(self) -> str            # 中文摘要（数量、Top 规则、退出码建议）

def inspect_file(path, *, dialect: str = "auto") -> Report     # .json/.jsonl 按扩展名+内容探测
def inspect_path(path, **kw) -> Iterator[Report]               # 目录/通配，流式逐文件
def load_dataset(path) -> tuple[list|None, list[Issue]]        # R001 层暴露
```

- CLI：`python -m sftcheck data.json [--dialect alpaca] [--min-severity WARN]`；退出码 0=无 ERROR，1=有 ERROR，2=文件不可读——便于接 CI/训练前门禁。
- **偏移/定位不变量**（fuzz 守护，与 charaudit 同族承诺）：`issue.sample_index` 恒指向真实存在的样本；`issue.excerpt` 恒为该字段值的截断前缀。

## 4. 规则集（编号稳定，新增只增不改义）

| 编号 | 规则 | 级别 |
|---|---|---|
| R001 | JSON 解析失败 / jsonl 行损坏 | ERROR |
| R009 | 方言无法识别（自动探测无特征键；用 dialect= 显式指定） | WARN |
| R010 | 方言必填字段缺失（alpaca.instruction、alpaca.output、sharegpt.conversations、openai.messages） | ERROR |
| R011 | 字段类型错误（字符串位置给了数字/对象等） | ERROR |
| R020 | 空消息 / 空白字符串（instruction、output、value、content） | WARN |
| R021 | sharegpt 奇偶位违规（human/observation 未落奇位，gpt/function 未落偶位） | ERROR |
| R022 | openai role 非法值 / 首条非 system 非 user | ERROR |
| R023 | history 元组非二元或元素非字符串 | WARN |
| R030 | stage 疑似不匹配：检测到 chosen/rejected 等偏好字段（对照 #3793） | WARN |
| R040 | 样本重复（全样本规范化 JSON 哈希相同；只报组，不报每条） | WARN |
| R050 | 中文质量信号：全角空格混入、疑似乱码（替换符 U+FFFD 密度）、繁简混杂（启发式） | INFO |
| R060 | 非标准角色值（如 "bot"/"ai"——上游 tags 可映射，但裸文件常见错误） | WARN |

设计取舍：中文质量信号放 INFO——它们可能是合规数据特征（全角空格在排版文本中合法），误报控制优先于覆盖；规则默认集只开 ERROR+WARN，`--strict` 才启用 INFO。

## 5. 诚实边界声明（S5 进 README）

- 结构干净不等于语义优质，更不等于训练成功；
- 规范以 LlamaFactory 为准绳，其他框架（axolotl、ms-swift）方言兼容性不做承诺；上游演进会导致规则跟版，报告内嵌 spec_version 供追溯；
- 重复检测是精确哈希，不做近似去重（语义重复是语义问题，见 §1 边界）；
- arrow/parquet/csv 起步不支持：给出明确降级提示而非报错崩溃。

## 6. 实现与测试预告（S3/S4）

- 纯 stdlib（json/csv 不需要、hashlib、dataclasses、argparse）；单遍流式解析，大文件逐行读 jsonl。
- 已知向量：GAP_PROOF 四条 issue 对应的构造样本（KeyError instruction、role 错位、cast 类型错、偏好字段混入）——每个向量对应一条规则编号。
- fuzz：R001–R060 编号稳定性、sample_index 不变量、损坏 jsonl 行不中断整体审计（隔离为 R001 单行 ERROR）。
