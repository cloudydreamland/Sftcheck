"""Reproducible performance benchmarks for sftcheck (stdlib only, seeded).

Methodology (stated up front):
- Samples are SYNTHETIC, generated deterministically with random.Random(20261008)
  from fixed Chinese/English pools into .jsonl files. Not real-world corpora.
- Each cell = best/median of 5 runs of inspect_file (full audit incl. R040
  duplicate hashing), time.perf_counter. Numbers are only comparable on the
  same machine/Python; see RESULTS.md for the recorded environment.

Usage:
    cd /path/to/sftcheck
    PYTHONPATH=src python benchmarks/run_bench.py
"""
from __future__ import annotations

import json
import os
import platform
import statistics
import sys
import tempfile
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from sftcheck import inspect_file  # noqa: E402

SEED = 20261008
REPEATS = 5

CN = "的一是不了人我在有他这中大来上国到时要说数据集训练模型样本质量检查"


def make_lines(rng, n: int, bad_every: int) -> list[str]:
    lines = []
    for i in range(n):
        if bad_every and i % bad_every == bad_every - 1:
            sample = {"instruction": "q"}  # R010
        elif i % (bad_every * 7 or 1) == 3:
            sample = {"conversations": [{"from": "human", "value": "hi"},
                                        {"from": "gpt", "value": "yo"}]}
        else:
            sample = {
                "instruction": f"{i}: " + "".join(rng.choice(CN) for _ in range(40)),
                "input": "".join(rng.choice(CN) for _ in range(10)),
                "output": "".join(rng.choice(CN) for _ in range(60)),
            }
        lines.append(json.dumps(sample, ensure_ascii=False))
    return lines


def build_files(tmp: str) -> dict[str, str]:
    rng = __import__("random").Random(SEED)
    out = {}
    for size in (1000, 10000, 50000):
        p = os.path.join(tmp, f"bench_{size}.jsonl")
        with open(p, "w", encoding="utf-8") as fh:
            fh.write("\n".join(make_lines(rng, size, bad_every=max(size // 20, 10))))
        out[f"{size} lines"] = p
    return out


def main() -> None:
    print("== sftcheck benchmark ==")
    print(f"python     : {sys.version.split()[0]} ({platform.architecture()[0]})")
    print(f"platform   : {platform.platform()}")
    print(f"processor  : {os.environ.get('PROCESSOR_IDENTIFIER') or platform.processor() or 'unknown'}")
    print(f"method     : best/median of {REPEATS} runs per cell, time.perf_counter, seeded synthetic jsonl (seed={SEED})")
    print()
    tmp = tempfile.mkdtemp()
    files = build_files(tmp)
    rows = []
    for label, path in files.items():
        n = sum(1 for _ in open(path, encoding="utf-8"))
        times = []
        for _ in range(REPEATS):
            start = time.perf_counter()
            report = inspect_file(path)
            times.append(time.perf_counter() - start)
        best = min(times)
        rows.append((label, n, best * 1000, statistics.median(times) * 1000,
                     n / best, len(report.issues)))
    print(f"{'sample':<14} {'lines':>7}  {'best(ms)':>9}  {'median(ms)':>10}  {'best samples/s':>14}  {'issues':>7}")
    for label, n, best, median, rate, issues in rows:
        print(f"{label:<14} {n:>7}  {best:>9.1f}  {median:>10.1f}  {rate:>14,.0f}  {issues:>7}")
    print("\n(all cells include full rule set R001-R060 except R050/--strict)")


if __name__ == "__main__":
    main()
