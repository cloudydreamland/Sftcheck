# The Mines in the Dataset — sftcheck

> *微调数据集的训练前排雷器：alpaca / sharegpt / OpenAI 三方言结构预检，逐行定位、带修复建议。*
>
> English README 在 S5 阶段提供。

[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](pyproject.toml)

**Status: pre-release `0.1.0a1`, not yet on PyPI.** 当前 alpha 已实现全部三方言校验（alpaca / sharegpt / OpenAI）、方言自动探测、规则集 R001–R060（R050 中文质量信号 `--strict` 启用）、CLI 训练前门禁（退出码 0/1/2）与审计报告（`Issue`/`Report`），详见 [DESIGN.md](DESIGN.md) §4。

你的微调数据集里埋着训练前看不见的雷：缺字段的样本要等训练框架抛 `KeyError` 才暴露（[LlamaFactory #7577](https://github.com/hiyouga/LlamaFactory/issues/7577)），role 错位要到转换层才炸，偏好数据被误喂进 SFT 阶段（[#3793](https://github.com/hiyouga/LlamaFactory/issues/3793)）。sftcheck 在训练开始前逐样本排雷，给出**样本序号 + 字段 + 规则编号 + 修复建议**的审计报告。

## 试一下（源码运行）

```bash
git clone https://github.com/cloudydreamland/Sftcheck
cd Sftcheck
PYTHONPATH=src python -c "
from sftcheck import inspect_file
import json, tempfile, os
samples = [
  {'instruction': '把下面的话翻译成英文', 'input': '今天天气不错', 'output': 'The weather is nice today.'},
  {'conversations': [{'from': 'human', 'value': 'hi'}]},
]
p = os.path.join(tempfile.mkdtemp(), 'demo.json')
open(p, 'w', encoding='utf-8').write(json.dumps(samples, ensure_ascii=False))
r = inspect_file(p, dialect='alpaca')
print(r.summary())
for i in r.issues:
    print(i.rule, i.severity, i.field, '|', i.message[:44])
"
```

Verified output（实跑核实）：

```text
文件 …\demo.json：方言=alpaca（explicit），样本 2，问题 2 条（ERROR 2 / WARN 0 / INFO 0）；Top 规则：R010×2
R010 ERROR instruction | alpaca 方言必填字段 instruction 缺失：训练框架会在此处抛出 KeyE
R010 ERROR output | alpaca 方言必填字段 output 缺失：训练框架会在此处抛出 KeyError（
```

第 2 条样本是 sharegpt 形状却被按 alpaca 检查——正是 [#7577](https://github.com/hiyouga/LlamaFactory/issues/7577) 的场景：sftcheck 在训练前把它指出来，而不是让训练在深栈里抛 `KeyError`。

## 训练前门禁（CLI）

```bash
PYTHONPATH=src python -c "
import json, subprocess, sys, tempfile, os
p = os.path.join(tempfile.mkdtemp(), 'bad.jsonl')
open(p, 'w', encoding='utf-8').write(json.dumps({'instruction': 'q'}, ensure_ascii=False))
proc = subprocess.run([sys.executable, '-m', 'sftcheck', p, '--dialect', 'alpaca'],
                      capture_output=True, text=True)
print('exit:', proc.returncode)
print('has R010:', 'R010' in proc.stdout)
"
```

Verified output（实跑核实）：

```text
exit: 1
has R010: True
```

普通 shell 形式：`PYTHONPATH=src python -m sftcheck data.jsonl --dialect sharegpt || echo "数据集未过预检"`。
退出码：0 = 无 ERROR，1 = 有 ERROR（训练前拦截），2 = 文件不可读。`--strict` 启用 INFO 级中文质量信号，`--min-severity` 控制显示阈值。

## 诚实边界

- 结构干净 ≠ 语义优质 ≠ 训练成功；sftcheck 只做结构与规则检查，不评估样本质量。
- 方言规范以 [LlamaFactory data/README.md](https://github.com/hiyouga/LlamaFactory/blob/main/data/README.md) 为准绳（报告内嵌 `spec_version` 哈希，当前锚 `e43e0eed`）；对 axolotl / ms-swift 等其他框架的兼容性不做承诺。
- 重复检测是精确哈希，不做语义去重。
- 0.1.0a1 仅支持 `.json` / `.jsonl`；csv/parquet/arrow 给出明确降级提示。

## 证据与设计

立项证据（LlamaFactory 75,347★、格式类 open issue sharegpt 30/alpaca 61/dataset format 109，全部实抓）：[GAP_PROOF.md](GAP_PROOF.md)。
规范清单与 11 条编号规则（R001–R060）：[DESIGN.md](DESIGN.md)。开发日志：[WORKLOG.md](WORKLOG.md)。

## License

MIT — see [LICENSE](LICENSE).
