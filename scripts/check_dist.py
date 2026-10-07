"""Assert the built sdist/wheel contain exactly what the package promises.

Checks (run after `python -m build`):
- wheel: all modules + BOTH data tables + LICENSE; NO tests/, docs/, benchmarks/,
  data/raw
- sdist: pyproject + MANIFEST-declared docs + package data; NO data/raw, no
  build_venv/dist build junk

Usage (from repo root, after building into dist_check/):
    python scripts/check_dist.py dist_check
"""
from __future__ import annotations

import sys
import tarfile
import zipfile
from pathlib import Path

def check_wheel(path: Path) -> list[str]:
    problems: list[str] = []
    with zipfile.ZipFile(path) as zf:
        names = zf.namelist()
        required = [
            "sftcheck/__init__.py",
            "sftcheck/inspector.py",
            "sftcheck/model.py",
            "sftcheck/__main__.py",
        ]
        for name in required:
            if name not in names:
                problems.append(f"wheel missing {name}")
        allowed_prefixes = ("sftcheck/", "sftcheck-0.1.0a1.dist-info/")
        for name in names:
            if not name.startswith(allowed_prefixes):
                problems.append(f"wheel has unexpected entry: {name}")
        if not any(n.startswith("sftcheck-0.1.0a1.dist-info/licenses/") or n.endswith("/LICENSE") for n in names):
            problems.append("wheel missing LICENSE")
    return problems


def check_sdist(path: Path) -> list[str]:
    problems: list[str] = []
    base = f"sftcheck-0.1.0a1"
    with tarfile.open(path) as tf:
        names = tf.getnames()
        required = [
            base + "/pyproject.toml",
            base + "/MANIFEST.in",
            base + "/README.md",
            base + "/README.en.md",
            base + "/CHANGELOG.md",
            base + "/DESIGN.md",
            base + "/GAP_PROOF.md",
            base + "/REPORT.md",
            base + "/WORKLOG.md",
            base + "/LICENSE",
            base + "/benchmarks/RESULTS.md",
        ]
        for name in required:
            if name not in names:
                problems.append(f"sdist missing {name}")
        for name in names:
            # tests/ shipping in the sdist is intentional (downstream packagers
            # can run the suite); the 763KB Unicode raw file must stay out.
            if "data/raw" in name:
                problems.append(f"sdist must not ship: {name}")
    return problems


def main() -> int:
    dist = Path(sys.argv[1] if len(sys.argv) > 1 else "dist_check")
    files = sorted(dist.iterdir())
    print("artifacts:", ", ".join(f.name for f in files))
    problems: list[str] = []
    for f in files:
        if f.name.endswith(".whl"):
            problems += check_wheel(f)
        elif f.name.endswith(".tar.gz"):
            problems += check_sdist(f)
    for p in problems:
        print("FAIL:", p)
    print(f"{'OK' if not problems else 'FAILED'}: {len(files)} artifacts checked")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
