# WORKLOG — sftcheck

## 2026-10-08 · D-S0-1 立项证据复核（S0 完成）

**交付：`GAP_PROOF.md`——全部关键数字当日实抓复核，未照抄调研稿。**

### 实抓结果与调研稿差异（如实）

- LlamaFactory：调研稿 75,339★/1,172 open issues（2026-10-07）→ 实抓 **75,347★/1,176**（2026-10-08）——一日自然增长，方向与量级一致。
- 四条代表性 issue（#7577/#6878/#2471/#3793）标题、日期、状态逐一复核**全部吻合**（#7577 实抓全称含 "with llama3" 后缀）；时间跨度 2024-02→2025-04 证实同类问题反复出现。
- 新增量化：state:open 搜索 sharegpt=30、alpaca=61、dataset format=109 条——比调研稿的单点案例更有复发面证据。
- 规范锚点实抓：LlamaFactory data/README.md 原文 "Currently we support datasets in alpaca and sharegpt format"；OpenAI messages 为 sharegpt 内常见转换来源（调研稿"三方言"表述据此精确化）。
- ms-swift 实抓 15,787★、pushed 2026-10-07（活跃），佐证"框架内建缓解"论断。

### 遗留给 S1-1

- 命名查证：`datalign` 包名/仓库占用实查（PyPI + GitHub 全站搜索）、负面联想检查、展示名提案（"The X of Y" 风格），记录入本 WORKLOG。

## 2026-10-08 · D-S1-1 命名查证（S1 完成）

**决策：包名 `sftcheck`，展示名 `The Mines in the Dataset — sftcheck`（数据集里的地雷），调研稿原名 datalign 弃用。**

### 查证记录（全部 2026-10-08 实抓）

| 检查项 | 结果 |
|---|---|
| PyPI `datalign` | 404 未占用，**但**… |
| 品牌冲突（WebSearch） | **Datalign 已是现有品牌**：[datalign.com](https://datalign.com)（美国金融科技，AI 投顾匹配，Cambridge MA）+ 一家以色列医疗分析公司（2018）——非开发工具领域、直接商标风险低，但 SEO 必然被这两家污染，与"包名承担功能可搜索性"原则冲突 → **弃用 datalign** |
| PyPI `sftcheck` | 404 未占用 ✓ |
| GitHub 全站 `sftcheck in:name` | **total_count = 0**，完全洁净 ✓ |
| GitHub 全站 `datalign in:name` | 12 个仓库，全为 0–1★ 个人小仓（最接近者 JeremyLezmy/datalign 1★ 数据对齐工具，未上 PyPI） |
| 备选 `dataledger` | PyPI 404（备用） |
| 自有命名空间 `cloudydreamland/datalign` | 404 可建（若用旧名）；改用 sftcheck 后同理待建 |

### 展示名决策

- **选定：The Mines in the Dataset**（5 词，与 charaudit "The Ghosts in the Ink" 同意象族——数据集里埋着训练前看不见的雷，逐行排雷正是 sftcheck 的功能隐喻）。
- 备选（未采用）：The Sieve Before Training（微调之筛）；The Quiet Preflight。
- 词源声明：`sftcheck` 为 SFT + check 的功能性合成词，无虚假词源。
- 展示名"the mines in the dataset"短语未做全网穷举（作为 5 词意象标题撞车概率极低，GitHub 搜索无同名仓库）。

### 遗留给 S2-1

- API 草案 + 三方言规范清单（以 LlamaFactory data/README.md 为准绳并记录版本哈希）+ 诚实边界声明草案。

## 2026-10-08 · D-S2-1 设计稿（S2 完成）

**交付：`DESIGN.md`——三方言规范清单（锚点：LlamaFactory commit ce9dc9e072f8 / data/README.md blob e43e0eed0b48…a927，2026-10-08 实抓 475 行原文）、API 草案（inspect_file/inspect_path → Report + Issue；CLI 退出码门禁）、11 条编号规则集（R001–R060，三级 severity）、诚实边界声明草案。**

### 设计要点与取舍（记录理由）

- 规范只锚 LlamaFactory data/README.md 一个准绳并内嵌 spec_version 到每份报告——多框架准绳会漂移，单锚点+跟版是诚实且可维护的做法；axolotl/ms-swift 兼容性明确不承诺。
- 方言字段逐字对齐实抓原文：alpaca 的 instruction/output 必填（对照 #7577 KeyError）、history 元组且 **history response 参与训练**（README 原文强调，值得 WARN 级提示）；sharegpt 奇偶位规则按原文（human/observation 奇位、gpt/function 偶位，1 起算）；openai 为 sharegpt 特例（messages[].role/content）。
- 中文质量信号定为 INFO 且默认关（--strict 才开）：全角空格在排版文本中合法，误报控制优先；R030 偏好字段混入 WARN 直接对照 #3793。
- sdist 附带 tests 的上游默认行为在此项目沿用（与 charaudit 同决策）。
- 定位不变量（sample_index 恒有效、excerpt 恒为值截断前缀）为 fuzz 守护承诺，与 charaudit 偏移不变量同族。

### 遗留给 S3-1

- 包骨架（pyproject/src 布局 0.1.0a1、LICENSE MIT、README 骨架）+ R001/R010/R011 + alpaca 方言 + 测试；sharegpt/openai 与规则集其余部分 S3-2 跟进。

## 2026-10-08 · D-S3-1 包骨架 + alpaca 方言（S3-1 完成）

**交付：pyproject（setuptools/src 布局/0.1.0a1）+ LICENSE(MIT) + README（quickstart 实跑核实）+ `src/sftcheck/{__init__,model,inspector}.py` + `tests/test_alpaca.py` 15 用例。**

### 实现范围（对照 DESIGN §4）

- 已落：R001（JSON 解析失败/jsonl 坏行隔离/顶层非数组）、R010（instruction/output 缺失）、R011（类型错）、R020（空串 WARN）、R023（history 形状 WARN）；方言自动探测（instruction/conversations/messages 特征键）+ 显式指定；未知方言 WARN；Issue/Report 冻结数据类 + spec_version（锚 e43e0eed）。
- 未落（S3-2）：sharegpt/openai 校验、R021/R022/R030/R040/R050/R060、CLI。
- #7577 向量落地：sharegpt 形状样本按 alpaca 检查 → R010×2（instruction/output），报告信息直接引用 #7577。

### 过程记录

- 自测拦截 3 处笔误：测试内废括号语法（GOOD_KEY walrus 残留）、.json 路径漏 line_nos 定义（UnboundLocalError 10 个 error）、inspector 残留无意义行——均为测试/初稿问题，规则实现本身一次通过。
- 行为决策：history 非法项逐项报告（粒度细于"每组一条"），测试期望按库行为修正并注释。
- 验证：`cd /e/n_projects/sftcheck && PYTHONPATH=src python -m unittest discover -s tests` → **Ran 15 tests, OK (0.03s)**；README quickstart 实跑输出逐字核实。

### 遗留给 S3-2

- sharegpt/openai 方言 + R021/R022/R030/R040/R050/R060 + CLI（python -m sftcheck）+ 对应向量测试；DESIGN 若有偏离回改并记录。

## 2026-10-08 · D-S3-2 三方言全量规则 + CLI（S3-2 完成，S3 阶段完成）

**交付：sharegpt/openai 方言校验全量落地 + 跨切面规则 + CLI。规则集 R001–R060 全部实现：R021（sharegpt 奇偶位，human/observation 奇位、gpt/function_call/function 偶位，1 起算）、R022（openai 非法 role ERROR + 首条 assistant WARN）、R030（chosen/rejected 字段 → 疑似偏好数据误用，对照 #3793）、R040（规范化 JSON 哈希重复组）、R050（全角空格/U+FFFD/繁简混杂启发式，INFO，--strict 才启用）、R060（非标准角色 WARN）。CLI `python -m sftcheck`：--dialect/--min-severity/--strict，退出码 0/1/2 训练前门禁。**

### 验证

- 新增 tests/test_sharegpt_openai.py 16 用例（含 CLI 子进程端到端退出码测试），全量 **Ran 31 tests, OK (0.41s)**。
- README 状态行更新为"三方言已实现"+ 新增 CLI 门禁节；quickstart 复跑逐字一致。
- 过程修复 5 处自测问题：CLI 对不存在路径返回 0（补 existence 检查→2）；非法 role 触发首条 WARN 重复报告（改为 elif 仅合法 role 提示）；繁简测试用字不在小词表；auto 方言下未知形状无法套 sharegpt 检查（显式 dialect= 正是文档化用法）；一处取值笔误。库行为两处改进（CLI 存在性检查、role 提示去重），其余为测试修正。

### 遗留给 S4-1

- 边界 fuzz（sample_index 不变量、损坏行隔离、规则编号稳定性、大 jsonl 流式）+ 性能实测 + 失败模式梳理；S5 文档（README.en/CHANGELOG/REPORT）。

## 2026-10-08 · D-S4-1 fuzz + 性能 + 失败模式（S4-1 完成，S4 阶段完成）

**交付：tests/test_fuzz.py 3 用例（60 例种子 fuzz 不变量、三方言规则编号稳定性、100k 行边界）+ benchmarks/run_bench.py + benchmarks/RESULTS.md（真实运行）。全量 34 测试 OK（1.15s）。**

### fuzz 抓到 2 个真问题（库修复，回改 DESIGN 记录理由）

1. **"方言无法识别"WARN 错用 R001**——与"解析失败"语义不同却共用编号，fuzz 计数断言暴露。修复：新编号 **R009**（DESIGN 规则表已加行，新增只增不改义）。
2. **sample_index 不变量破坏**（case=9: 21 not < 21）——坏行位于所有好行之后时，行级 R001 的 sample_index == total_samples。修复：加载后统一钳制 sample_index ≤ total-1（line_no 仍是行级问题主定位），dataclasses.replace 实现，性能无感知（修复前后基准 5.4/52.4/277.5ms → 5.5/55.6/275.3ms，噪声内）。
3. 另修正 fuzz 自身两处：伪不变量"issues≤行数"删除（逐项粒度下一条样本可产多条 issue，文档化行为）；GARBAGE_LINES 语法残迹。

### 性能实测（环境 Python 3.13.2/Win11/13 代酷睿，完整记录见 benchmarks/RESULTS.md）

- **~18 万样本/秒、线性扩展**（1k=5.5ms、10k=55.6ms、50k=275.3ms，全规则）；50k 行全审计 0.28s。
- 失败模式梳理：不可读文件→CLI exit 2；坏扩展名→ValueError 明确降级提示；损坏 jsonl 行→R001 隔离不中断；内存 O(n)（R040 需全样本哈希），超大文件建议 jsonl 分片——均记录 DESIGN §5/RESULTS.md。

### 遗留给 S5

- S5-1：README.en + CHANGELOG + REPORT；S5-2：pyproject 终审/干净 venv/CI（沿用 charaudit 模式）。

## 2026-10-08 · D-S5-1 README.en + CHANGELOG + REPORT（S5-1 完成）

**交付：`README.en.md`（英文首页，与中文版互链；quickstart 输出实跑复验一致）+ `CHANGELOG.md`（0.1.0a1 条目，alpha 措辞）+ `REPORT.md`（评估者报告，引用实测基准与 fuzz 修复记录）。**

### 验证与记录

- quickstart 复跑（clamp 修复后）：输出与两语言 README 引文逐字一致（方言=alpaca、2 ERROR R010×2）。
- 回归：`cd /e/n_projects/sftcheck && PYTHONPATH=src python -m unittest discover -s tests` → **Ran 34 tests, OK**。
- alpha 措辞核查：3 - Alpha / 0.1.0a1，无 stable 宣称 ✓。

### 遗留给 S5-2

- 干净 venv 安装 + quickstart 断言脚本（沿用 charaudit assert_quickstart 模式，含 CRLF 归一化教训）+ CI workflow（ubuntu/windows × 3.10–3.13）+ publish workflow（PUBLISH_ENABLED 门控）+ MANIFEST.in。

## 2026-10-08 · D-S5-2 干净 venv 断言 + CI/publish + 产物终检（S5-2 完成，S5 阶段完成）

**交付：`scripts/assert_quickstart.py`（双层守卫：期望块逐字存在于两语言 README + 实跑相等；demo 临时路径做省略号归一化）+ 干净 venv 全流程验证（**quickstart 断言 2/2：alpaca demo + CLI 训练门禁**，venv 内套件 34 OK）+ `.github/workflows/ci.yml`（ubuntu/windows × 3.10–3.13，测试+干净安装断言，已去除 charaudit 特有的 build_tables 步骤）+ `publish.yml`（PUBLISH_ENABLED 门控）+ `MANIFEST.in`/`scripts/check_dist.py`（sftcheck 结构适配版）。**

### 终检（真实构建，dist_check 即删）

- wheel：sftcheck 4 模块（__init__/inspector/model/__main__）+ dist-info/licenses/LICENSE，零越界条目。
- sdist：pyproject/MANIFEST/双 README/CHANGELOG/DESIGN/GAP_PROOF/REPORT/WORKLOG/LICENSE/benchmarks 全在；无越界。

### 过程记录（断言器连抓三处文档漂移——工具价值自证）

1. README 示例块 issue 行带 2 空格缩进（实际 print 无缩进）——两语言修正；
2. S3-2 改报错文案后截断点变化（"抛出 K"→"抛出 KeyE"）未同步 README——修正（S5-1 教训的机械化复现，assert 脚本从此把该检查固化为 CI 可跑）；
3. CLI 节缺 "Verified output" 块——补自包含片段与实跑输出（exit: 1 / has R010: True）。
- 过程波折：assert 脚本自身的多行期望串经 JSON→bash→python 三层转义损坏两次（语法错误），最终以逐行程序化重建+compile 验证解决；CRLF 归一化沿用 charaudit 教训。
- 回归：**Ran 34 tests, OK (1.26s)**。

### 遗留给 S6/S7

- S6：`git init` + 首次提交 + `gh repo create cloudydreamland/Sftcheck --push` + 实查 CI 矩阵；S7：Release v0.1.0a1（publish 门控同 charaudit）。
