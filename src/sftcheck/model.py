"""Data models for sftcheck. Issues carry sample_index / line_no evidence."""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

# Spec anchor: LlamaFactory data/README.md, blob e43e0eed0b48f6ed0054382346311550a2a1a927
# (repo commit ce9dc9e072f8, fetched 2026-10-08). Re-anchor + record in WORKLOG
# when following upstream updates.
SPEC_VERSION = "llamafactory-data-readme@e43e0eed"

SEVERITY_ERROR = "ERROR"
SEVERITY_WARN = "WARN"
SEVERITY_INFO = "INFO"


@dataclass(frozen=True)
class Issue:
    """One finding. Invariants (fuzz-guarded): 0 <= sample_index < total_samples,
    excerpt == str(field_value)[:80] prefix."""

    rule: str
    severity: str
    sample_index: int
    line_no: int | None  # physical line for .jsonl; None for .json arrays
    field: str
    message: str
    excerpt: str = ""


@dataclass(frozen=True)
class Report:
    path: str
    dialect: str  # alpaca / sharegpt / openai / unknown
    dialect_confidence: str  # detected / explicit
    total_samples: int
    issues: tuple[Issue, ...] = ()
    spec_version: str = SPEC_VERSION

    def stats(self) -> dict[str, int]:
        """Issue counts per rule id."""
        return dict(Counter(i.rule for i in self.issues))

    def severity_counts(self) -> dict[str, int]:
        return dict(Counter(i.severity for i in self.issues))

    def summary(self) -> str:
        sev = self.severity_counts()
        top = "、".join(
            f"{rule}×{n}"
            for rule, n in sorted(self.stats().items(), key=lambda kv: (-kv[1], kv[0]))[:5]
        )
        return (
            f"文件 {self.path}：方言={self.dialect}（{self.dialect_confidence}），"
            f"样本 {self.total_samples}，问题 {len(self.issues)} 条"
            f"（ERROR {sev.get('ERROR', 0)} / WARN {sev.get('WARN', 0)} / INFO {sev.get('INFO', 0)}）"
            + (f"；Top 规则：{top}" if top else "")
        )
