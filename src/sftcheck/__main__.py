"""CLI: python -m sftcheck <path> [--dialect D] [--min-severity S] [--strict]

Exit codes: 0 = no ERROR, 1 = at least one ERROR, 2 = file unreadable.
Designed as a training-gate: `sftcheck data.jsonl || exit 1`.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .inspector import inspect_file, inspect_path

_SEVERITY_ORDER = {"INFO": 0, "WARN": 1, "ERROR": 2}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="sftcheck",
        description="训练前 SFT 数据集结构预检（The Mines in the Dataset）",
    )
    parser.add_argument("path", help="数据集文件或目录（.json / .jsonl）")
    parser.add_argument("--dialect", default="auto",
                        choices=["auto", "alpaca", "sharegpt", "openai"],
                        help="方言：默认自动探测")
    parser.add_argument("--min-severity", default="WARN",
                        choices=["INFO", "WARN", "ERROR"],
                        help="显示阈值：低于该级别的 issue 不打印（默认 WARN）")
    parser.add_argument("--strict", action="store_true",
                        help="启用 INFO 级规则（R050 中文质量信号）")
    args = parser.parse_args(argv)

    threshold = _SEVERITY_ORDER[args.min_severity]
    code = 0
    path = Path(args.path)
    if not path.exists():
        print(f"error: 路径不存在：{args.path}", file=sys.stderr)
        return 2
    try:
        reports = list(inspect_path(args.path, dialect=args.dialect, strict=args.strict))
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    for report in reports:
        print(report.summary())
        shown = 0
        for issue in report.issues:
            if _SEVERITY_ORDER[issue.severity] < threshold:
                continue
            location = f"行{issue.line_no}" if issue.line_no is not None else f"样本{issue.sample_index}"
            print(
                f"  [{issue.severity}] {issue.rule} {location} {issue.field}: "
                f"{issue.message}"
                + (f"（如：{issue.excerpt!r}）" if issue.excerpt else "")
            )
            shown += 1
        if not shown:
            print("  （无达到显示阈值的问题）")
        print()
        if any(i.severity == "ERROR" for i in report.issues):
            code = 1
    return code


if __name__ == "__main__":
    sys.exit(main())
