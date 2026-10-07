# The Mines in the Dataset — sftcheck

> *Pre-flight structural auditing for SFT fine-tuning datasets: alpaca / sharegpt /
> OpenAI dialects, row-level findings with fix suggestions.*

[中文文档](README.md) | English

[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](pyproject.toml)

**Status: pre-release `0.1.0a1`, not yet on PyPI.** This alpha implements all three
dialect checks (alpaca / sharegpt / OpenAI), automatic dialect detection, rule set
R001–R060 (R050 Chinese-quality signals behind `--strict`), and a CLI training gate
with exit codes 0/1/2 — see [DESIGN.md](DESIGN.md) §4.

Your fine-tuning dataset hides mines you only find when training crashes: samples
missing required fields surface as a deep `KeyError` ([LlamaFactory
#7577](https://github.com/hiyouga/LlamaFactory/issues/7577)), role misalignment dies
in a conversion layer, preference data gets fed into SFT ([#3793](https://github.com/hiyouga/LlamaFactory/issues/3793)).
sftcheck sweeps the dataset **before** training and reports per-sample findings:
sample index + field + rule id + fix suggestion.

## Try it from a source checkout

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

Verified output (real run):

```text
文件 …\demo.json：方言=alpaca（explicit），样本 2，问题 2 条（ERROR 2 / WARN 0 / INFO 0）；Top 规则：R010×2
R010 ERROR instruction | alpaca 方言必填字段 instruction 缺失：训练框架会在此处抛出 KeyE
R010 ERROR output | alpaca 方言必填字段 output 缺失：训练框架会在此处抛出 KeyError（
```

The second sample is sharegpt-shaped but checked as alpaca — exactly the #7577
scenario: sftcheck points at it before training instead of letting the trainer
throw `KeyError` from deep inside.

## Training gate (CLI)

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

Verified output (real run):

```text
exit: 1
has R010: True
```

Plain shell form: `PYTHONPATH=src python -m sftcheck data.jsonl --dialect sharegpt || echo failed`.
Exit codes: 0 = no ERROR, 1 = ERROR found (block the run), 2 = file unreadable.
`--strict` enables INFO-level Chinese-quality signals (R050);
`--min-severity` controls display threshold.

## What it checks

Rule set R001–R060 (full table in [DESIGN.md](DESIGN.md) §4): JSON parsing with
broken-line isolation (R001), undetectable dialect (R009), missing required fields
per dialect (R010), type errors (R011), empty messages (R020), sharegpt role-parity
violations (R021), OpenAI role validity (R022), history shape (R023), preference
fields inside SFT data (R030), exact-duplicate groups (R040), Chinese-quality
signals — fullwidth spaces, U+FFFD runs, traditional/simplified mixing — as
strict-only INFO (R050), and non-standard roles (R060).

Measured on synthetic seeded data: **~180k samples/second, linear** (50k-line file
fully audited in 0.28s; environment and commands in
[benchmarks/RESULTS.md](benchmarks/RESULTS.md)).

## Honest boundaries

- Clean structure ≠ good samples ≠ successful training; sftcheck checks structure
  and rules only, never sample quality.
- The spec is anchored to [LlamaFactory data/README.md](https://github.com/hiyouga/LlamaFactory/blob/main/data/README.md)
  (every report embeds `spec_version`, currently `e43e0eed`); compatibility with
  axolotl / ms-swift dialects is not promised.
- Duplicate detection is exact-hash; semantic near-duplicates are out of scope.
- 0.1.0a1 supports `.json` / `.jsonl` only; csv/parquet/arrow get an explicit
  downgrade message.

## Evidence & design

Why this library exists (LlamaFactory 75,347★; open issues mentioning sharegpt:
30, alpaca: 61, "dataset format": 109 — all fetched 2026-10-08):
[GAP_PROOF.md](GAP_PROOF.md). Rule table and correctness standards:
[DESIGN.md](DESIGN.md). Development log: [WORKLOG.md](WORKLOG.md).

## License

MIT — see [LICENSE](LICENSE).
