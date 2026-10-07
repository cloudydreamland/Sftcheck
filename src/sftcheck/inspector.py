"""inspect_file / inspect_path: load and audit SFT datasets.

Dialects: alpaca / sharegpt / openai (spec anchor: LlamaFactory data/README.md
blob e43e0eed, see model.SPEC_VERSION). Rules R001-R060 per DESIGN.md §4;
R050 (INFO) only runs with strict=True.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Iterator

from .model import (
    SEVERITY_ERROR,
    SEVERITY_INFO,
    SEVERITY_WARN,
    Issue,
    Report,
    SPEC_VERSION,
)

_EXCERPT_MAX = 80

_ALPACA_REQUIRED_STR = ("instruction", "output")
_ALPACA_OPTIONAL_STR = ("input", "system")
_SHAREGPT_ODD_ROLES = {"human", "observation"}
_SHAREGPT_EVEN_ROLES = {"gpt", "function_call", "function"}
_SHAREGPT_KNOWN_ROLES = _SHAREGPT_ODD_ROLES | _SHAREGPT_EVEN_ROLES | {"system"}
_OPENAI_ROLES = {"system", "user", "assistant"}
_PREFERENCE_HINT_KEYS = {"chosen", "rejected", "chosen_score", "rejected_score"}
# Heuristic traditional/simplified mixing probe (documented in DESIGN.md §4):
# tiny hand-picked forms that exist in exactly one script variant.
_TRAD_ONLY = set("個學時間電腦資訊們來後開關長門馬鳥書車東員語書灣")
_SIMP_ONLY = set("个学时间电脑资讯们来后开关长门马鸟书车东员语湾")


def _excerpt(value: object) -> str:
    if value is None:
        return ""
    text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
    return text[:_EXCERPT_MAX]


def _issue(rule: str, severity: str, sample_index: int, line_no: int | None,
           field: str, message: str, value: object = None) -> Issue:
    return Issue(rule, severity, sample_index, line_no, field, message, _excerpt(value))


def _detect_dialect(samples: list) -> str:
    for s in samples:
        if isinstance(s, dict):
            if "instruction" in s or "output" in s or "history" in s:
                return "alpaca"
            if "conversations" in s:
                return "sharegpt"
            if "messages" in s:
                return "openai"
    return "unknown"


def _check_alpaca(samples: list, line_nos: list[int | None], strict: bool) -> list[Issue]:
    issues: list[Issue] = []
    for idx, sample in enumerate(samples):
        line = line_nos[idx]
        if not isinstance(sample, dict):
            issues.append(_issue("R011", SEVERITY_ERROR, idx, line, "<root>",
                                 "样本必须是 JSON 对象（{...}），实际为 "
                                 f"{type(sample).__name__}", sample))
            continue
        for name in _ALPACA_REQUIRED_STR:
            if name not in sample:
                issues.append(_issue(
                    "R010", SEVERITY_ERROR, idx, line, name,
                    f"alpaca 方言必填字段 {name} 缺失：训练框架会在此处抛出 "
                    f"KeyError（参见 LlamaFactory #7577）。补齐字段或改用 sharegpt 方言"))
        for name in _ALPACA_REQUIRED_STR + _ALPACA_OPTIONAL_STR:
            if name in sample and not isinstance(sample[name], str):
                issues.append(_issue(
                    "R011", SEVERITY_ERROR, idx, line, name,
                    f"字段 {name} 应为字符串，实际为 {type(sample[name]).__name__}",
                    sample[name]))
        for name in _ALPACA_REQUIRED_STR:
            if isinstance(sample.get(name), str) and not sample[name].strip():
                issues.append(_issue(
                    "R020", SEVERITY_WARN, idx, line, name,
                    f"字段 {name} 为空或纯空白：训练时将产生空 prompt/空回复样本",
                    sample[name]))
        history = sample.get("history")
        if history is not None:
            if not isinstance(history, list):
                issues.append(_issue(
                    "R023", SEVERITY_WARN, idx, line, "history",
                    f"history 应为 [user, model] 二元组列表，实际为 "
                    f"{type(history).__name__}", history))
            else:
                for h_idx, pair in enumerate(history):
                    if (not isinstance(pair, (list, tuple)) or len(pair) != 2
                            or not all(isinstance(x, str) for x in pair)):
                        issues.append(_issue(
                            "R023", SEVERITY_WARN, idx, line,
                            f"history[{h_idx}]",
                            "history 每项应为 [user, model] 二元组且均为字符串；"
                            "注意 history 中的回复也参与训练", pair))
        issues += _check_chinese_quality(idx, line, sample, strict)
    return issues


def _check_sharegpt(samples: list, line_nos: list[int | None], strict: bool) -> list[Issue]:
    issues: list[Issue] = []
    for idx, sample in enumerate(samples):
        line = line_nos[idx]
        if not isinstance(sample, dict):
            issues.append(_issue("R011", SEVERITY_ERROR, idx, line, "<root>",
                                 "样本必须是 JSON 对象（{...}），实际为 "
                                 f"{type(sample).__name__}", sample))
            continue
        if "conversations" not in sample:
            issues.append(_issue(
                "R010", SEVERITY_ERROR, idx, line, "conversations",
                "sharegpt 方言必填字段 conversations 缺失"))
            continue
        convs = sample["conversations"]
        if not isinstance(convs, list):
            issues.append(_issue(
                "R011", SEVERITY_ERROR, idx, line, "conversations",
                f"conversations 应为对象列表，实际为 {type(convs).__name__}", convs))
            continue
        if not convs:
            issues.append(_issue(
                "R020", SEVERITY_WARN, idx, line, "conversations",
                "conversations 为空列表：该样本不含任何对话内容", convs))
        for pos, item in enumerate(convs, start=1):
            if not isinstance(item, dict):
                issues.append(_issue(
                    "R011", SEVERITY_ERROR, idx, line, f"conversations[{pos - 1}]",
                    "对话项必须是对象 {from, value}", item))
                continue
            role = item.get("from")
            value = item.get("value")
            if not isinstance(role, str):
                issues.append(_issue(
                    "R011", SEVERITY_ERROR, idx, line, f"conversations[{pos - 1}].from",
                    f"from 应为字符串，实际为 {type(role).__name__}", role))
            elif role not in _SHAREGPT_KNOWN_ROLES:
                issues.append(_issue(
                    "R060", SEVERITY_WARN, idx, line, f"conversations[{pos - 1}].from",
                    f"非标准角色值 {role!r}（规范角色：human/gpt/observation/"
                    "function_call/function/system；上游 tags 可映射，裸文件中通常是错字）",
                    role))
            elif (role in _SHAREGPT_ODD_ROLES) != (pos % 2 == 1):
                issues.append(_issue(
                    "R021", SEVERITY_ERROR, idx, line, f"conversations[{pos - 1}].from",
                    f"奇偶位违规：{role} 应出现在{'奇' if role in _SHAREGPT_ODD_ROLES else '偶'}数位"
                    f"（当前第 {pos} 位，1 起算；规范原文见 LlamaFactory data/README.md）",
                    role))
            if not isinstance(value, str):
                if value is not None:
                    issues.append(_issue(
                        "R011", SEVERITY_ERROR, idx, line,
                        f"conversations[{pos - 1}].value",
                        f"value 应为字符串，实际为 {type(value).__name__}", value))
            elif not value.strip():
                issues.append(_issue(
                    "R020", SEVERITY_WARN, idx, line, f"conversations[{pos - 1}].value",
                    "对话内容为空或纯空白", value))
        issues += _check_chinese_quality(idx, line, sample, strict)
    return issues


def _check_openai(samples: list, line_nos: list[int | None], strict: bool) -> list[Issue]:
    issues: list[Issue] = []
    for idx, sample in enumerate(samples):
        line = line_nos[idx]
        if not isinstance(sample, dict):
            issues.append(_issue("R011", SEVERITY_ERROR, idx, line, "<root>",
                                 "样本必须是 JSON 对象（{...}），实际为 "
                                 f"{type(sample).__name__}", sample))
            continue
        if "messages" not in sample:
            issues.append(_issue(
                "R010", SEVERITY_ERROR, idx, line, "messages",
                "openai 方言必填字段 messages 缺失"))
            continue
        messages = sample["messages"]
        if not isinstance(messages, list):
            issues.append(_issue(
                "R011", SEVERITY_ERROR, idx, line, "messages",
                f"messages 应为对象列表，实际为 {type(messages).__name__}", messages))
            continue
        if not messages:
            issues.append(_issue(
                "R020", SEVERITY_WARN, idx, line, "messages",
                "messages 为空列表：该样本不含任何对话内容", messages))
        for pos, item in enumerate(messages, start=1):
            if not isinstance(item, dict):
                issues.append(_issue(
                    "R011", SEVERITY_ERROR, idx, line, f"messages[{pos - 1}]",
                    "消息必须是对象 {role, content}", item))
                continue
            role = item.get("role")
            value = item.get("content")
            if not isinstance(role, str):
                issues.append(_issue(
                    "R011", SEVERITY_ERROR, idx, line, f"messages[{pos - 1}].role",
                    f"role 应为字符串，实际为 {type(role).__name__}", role))
            elif role not in _OPENAI_ROLES:
                issues.append(_issue(
                    "R022", SEVERITY_ERROR, idx, line, f"messages[{pos - 1}].role",
                    f"openai 方言非法 role {role!r}（允许 system/user/assistant）",
                    role))
            elif pos == 1 and role == "assistant":
                issues.append(_issue(
                    "R022", SEVERITY_WARN, idx, line, "messages[0].role",
                    "首条消息应为 system 或 user（规范原文：the first message may "
                    "be a system prompt）", role))
            if "content" in item and not isinstance(value, str):
                issues.append(_issue(
                    "R011", SEVERITY_ERROR, idx, line, f"messages[{pos - 1}].content",
                    f"content 应为字符串，实际为 {type(value).__name__}", value))
            elif isinstance(value, str) and not value.strip():
                issues.append(_issue(
                    "R020", SEVERITY_WARN, idx, line, f"messages[{pos - 1}].content",
                    "消息内容为空或纯空白", value))
        issues += _check_chinese_quality(idx, line, sample, strict)
    return issues


def _check_preference_hints(samples: list, line_nos: list[int | None]) -> list[Issue]:
    issues: list[Issue] = []
    for idx, sample in enumerate(samples):
        if isinstance(sample, dict) and (set(sample) & _PREFERENCE_HINT_KEYS):
            issues.append(_issue(
                "R030", SEVERITY_WARN, idx, line_nos[idx],
                "、".join(sorted(set(sample) & _PREFERENCE_HINT_KEYS)),
                "样本含 chosen/rejected 系字段：疑似偏好（DPO/ reward）数据被用于 "
                "SFT 校验；LlamaFactory #3793 即为此类误用", sample))
    return issues


def _check_duplicates(samples: list, line_nos: list[int | None]) -> list[Issue]:
    groups: dict[str, list[int]] = {}
    for idx, sample in enumerate(samples):
        digest = hashlib.sha256(
            json.dumps(sample, sort_keys=True, ensure_ascii=False).encode("utf-8")
        ).hexdigest()[:16]
        groups.setdefault(digest, []).append(idx)
    issues: list[Issue] = []
    for digest, indices in groups.items():
        if len(indices) >= 2:
            issues.append(_issue(
                "R040", SEVERITY_WARN, indices[0], line_nos[indices[0]], "<root>",
                f"完全重复样本组（规范化 JSON 哈希 {digest}）：样本 "
                f"{indices} 共 {len(indices)} 条——精确哈希去重，不含语义重复"))
    return issues


def _check_chinese_quality(idx: int, line: int | None, sample: dict, strict: bool) -> list[Issue]:
    """R050 INFO signals; only with strict=True (DESIGN.md §4: default off)."""
    if not strict:
        return []
    issues: list[Issue] = []
    strings = [v for v in sample.values() if isinstance(v, str)]
    for item in sample.values():
        if isinstance(item, list):
            strings += [v for v in item if isinstance(v, str)]
    joined = "".join(strings)
    if "\u3000" in joined:
        issues.append(_issue("R050", SEVERITY_INFO, idx, line, "<text>",
                             "检测到全角空格（U+3000）：排版文本中合法，精确匹配管线需注意",
                             joined))
    if joined.count("\ufffd") > 0:
        issues.append(_issue("R050", SEVERITY_INFO, idx, line, "<text>",
                             f"检测到 {joined.count(chr(0xFFFD))} 个替换符 U+FFFD：疑似乱码",
                             joined))
    trad = sum(1 for ch in joined if ch in _TRAD_ONLY)
    simp = sum(1 for ch in joined if ch in _SIMP_ONLY)
    if trad and simp:
        issues.append(_issue("R050", SEVERITY_INFO, idx, line, "<text>",
                             f"繁简混杂嫌疑（简体特征字 {simp} 个、繁体特征字 {trad} 个；"
                             "小词表启发式，非判定）", joined))
    return issues


_CHECKERS = {"alpaca": _check_alpaca, "sharegpt": _check_sharegpt, "openai": _check_openai}


def _load_jsonl(text: str) -> tuple[list, list[Issue], list[int | None]]:
    samples: list = []
    issues: list[Issue] = []
    line_nos: list[int | None] = []
    for line_no, raw in enumerate(text.splitlines(), start=1):
        if not raw.strip():
            continue
        try:
            samples.append(json.loads(raw))
            line_nos.append(line_no)
        except json.JSONDecodeError as exc:
            # sample_index points at the nearest parsed sample (line_no is the
            # primary locator); clamped post-load to keep sample_index < total.
            issues.append(_issue(
                "R001", SEVERITY_ERROR, len(samples), line_no, "<line>",
                f"JSONL 第 {line_no} 行解析失败（已隔离，不影响其余行）：{exc.msg}",
                raw[:40]))
    return samples, issues, line_nos


def inspect_file(path: str | Path, *, dialect: str = "auto", strict: bool = False) -> Report:
    """Audit one .json / .jsonl dataset file."""
    p = Path(path)
    suffix = p.suffix.lower()
    if suffix not in (".json", ".jsonl"):
        raise ValueError(
            f"sftcheck 0.1.0a1 只支持 .json / .jsonl，收到 {suffix or '(无扩展名)'}；"
            "csv/parquet/arrow 请先转换格式（降级说明见 DESIGN.md §5）"
        )
    text = p.read_text(encoding="utf-8")
    if suffix == ".jsonl":
        samples, issues, line_nos = _load_jsonl(text)
    else:
        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            issues = [_issue("R001", SEVERITY_ERROR, 0, None, "<root>",
                             f"JSON 解析失败：{exc.msg}（第 {exc.lineno} 行）", "")]
            return Report(str(p), "unknown", "detected", 0, tuple(issues))
        if not isinstance(data, list):
            issues = [_issue("R001", SEVERITY_ERROR, 0, None, "<root>",
                             "顶层必须是样本数组 [...]，实际为 "
                             f"{type(data).__name__}；单样本请包成数组", data)]
            return Report(str(p), "unknown", "detected", 0, tuple(issues))
        samples, issues = data, []
        line_nos = [None] * len(samples)

    # invariant guard: sample_index must stay < total_samples. A trailing
    # broken jsonl line would otherwise carry sample_index == len(samples);
    # line_no remains the primary locator for line-level issues.
    if samples:
        from dataclasses import replace as _replace
        issues = [
            _replace(i, sample_index=min(i.sample_index, len(samples) - 1))
            for i in issues
        ]
    detected = _detect_dialect(samples)
    resolved = dialect if dialect != "auto" else detected
    if resolved == "unknown":
        issues.append(_issue(
            "R009", SEVERITY_WARN, 0, line_nos[0] if line_nos else None, "<root>",
            "无法从样本识别方言（未见 instruction/conversations/messages 特征键）；"
            "请用 dialect= 显式指定，否则只做了 JSON 层检查"))
        return Report(str(p), "unknown", "detected" if dialect == "auto" else "explicit",
                      len(samples), tuple(issues))

    checker = _CHECKERS[resolved]
    if resolved == "alpaca":
        issues += checker(samples, line_nos, strict)
    else:
        issues += checker(samples, line_nos, strict)
    issues += _check_preference_hints(samples, line_nos)
    issues += _check_duplicates(samples, line_nos)
    issues.sort(key=lambda i: (i.sample_index, i.rule))

    return Report(
        path=str(p),
        dialect=resolved,
        dialect_confidence="explicit" if dialect != "auto" else "detected",
        total_samples=len(samples),
        issues=tuple(issues),
        spec_version=SPEC_VERSION,
    )


def inspect_path(path: str | Path, **kwargs) -> Iterator[Report]:
    """Stream-audit a file or every supported file under a directory."""
    p = Path(path)
    if p.is_file():
        yield inspect_file(p, **kwargs)
        return
    for child in sorted(p.rglob("*")):
        if child.is_file() and child.suffix.lower() in (".json", ".jsonl"):
            yield inspect_file(child, **kwargs)
