"""Assert every README "Verified output" block is real — charaudit's guard, ported.

Two layers:
1. each expected block must appear VERBATIM in BOTH README.md and README.en.md;
2. the snippet runs with the current interpreter (clean venv: the installed
   package) and stdout must match exactly (CRLF-normalized).

Run: python scripts/assert_quickstart.py
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

DEMO = """
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
"""
DEMO_EXPECTED_HEADER = r"文件 …\demo.json：方言=alpaca（explicit），样本 2，问题 2 条（ERROR 2 / WARN 0 / INFO 0）；Top 规则：R010×2"
DEMO_EXPECTED_LINES = (
    "R010 ERROR instruction | alpaca 方言必填字段 instruction 缺失：训练框架会在此处抛出 KeyE",
    "R010 ERROR output | alpaca 方言必填字段 output 缺失：训练框架会在此处抛出 KeyError（",
)
DEMO_EXPECTED = DEMO_EXPECTED_HEADER + "\n" + "\n".join(DEMO_EXPECTED_LINES) + "\n"

GATE = """
import json, subprocess, sys, tempfile, os
p = os.path.join(tempfile.mkdtemp(), 'bad.jsonl')
open(p, 'w', encoding='utf-8').write(json.dumps({'instruction': 'q'}, ensure_ascii=False))
proc = subprocess.run([sys.executable, '-m', 'sftcheck', p, '--dialect', 'alpaca'],
                      capture_output=True, text=True, encoding='utf-8',
                      env={**os.environ, 'PYTHONIOENCODING': 'utf-8'})
print('exit:', proc.returncode)
print('has R010:', 'R010' in proc.stdout)
"""
GATE_EXPECTED = "exit: 1\nhas R010: True\n"


def main() -> int:
    failures = 0
    readme_text = {
        name: (ROOT / name).read_text(encoding="utf-8")
        for name in ("README.md", "README.en.md")
    }
    env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
    env["PYTHONIOENCODING"] = "utf-8"
    checks = [
        ("alpaca demo", DEMO, DEMO_EXPECTED),
        ("CLI training gate", GATE, GATE_EXPECTED),
    ]
    for title, snippet, expected in checks:
        proc = subprocess.run([sys.executable, "-c", snippet.strip("\n")],
                              capture_output=True, env=env, cwd=ROOT)
        got = proc.stdout.decode("utf-8").replace("\r\n", "\n")
        # the demo prints a temp path that differs per run; normalize it to the
        # elided form quoted in the READMEs
        if title == "alpaca demo":
            import re
            got = re.sub(r"文件 .*demo\.json", lambda m: "文件 …\\demo.json", got)
        if proc.returncode != 0:
            print(f"FAIL (crashed): {title}\n{proc.stderr.decode('utf-8')}")
            failures += 1
            continue
        if got != expected:
            print(f"FAIL (output drift): {title}\n--- expected ---\n{expected}--- got ---\n{got}")
            failures += 1
        else:
            print(f"ok (run):    {title}")
        for name, text in readme_text.items():
            if expected.strip("\n") not in text:
                print(f"FAIL (docs drift): expected block missing from {name}: {title}")
                failures += 1

    total = len(checks)
    print(f"\n{total - failures}/{total} quickstart blocks verified against both READMEs")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
