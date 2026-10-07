"""S4 fuzz/boundary tests for sftcheck (seeded, deterministic)."""
from __future__ import annotations

import json
import random
import tempfile
import unittest
from pathlib import Path

from sftcheck import inspect_file

RULES_KNOWN = {"R001", "R009", "R010", "R011", "R020", "R021", "R022",
               "R023", "R030", "R040", "R050", "R060"}
SEVERITIES = {"ERROR", "WARN", "INFO"}

GOOD_ALPACA = {"instruction": "翻译这句话", "input": "你好世界", "output": "Hello world."}
GOOD_SHAREGPT = {"conversations": [{"from": "human", "value": "hi"},
                                   {"from": "gpt", "value": "hello"}]}
GOOD_OPENAI = {"messages": [{"role": "system", "content": "be nice"},
                            {"role": "user", "content": "hi"},
                            {"role": "assistant", "content": "hello"}]}
BAD_POOL = [
    {"instruction": "q"},                                   # R010 output missing
    {"output": "a"},                                        # R010 instruction missing
    {"instruction": 123, "output": "a"},                    # R011
    {"instruction": "", "output": ""},                      # R020
    {"conversations": [{"from": "gpt", "value": "x"}]},     # R021
    {"conversations": [{"from": "bot", "value": "x"}]},     # R060
    {"messages": [{"role": "bot", "content": "x"}]},        # R022
    {"messages": [{"role": "assistant", "content": "y"}]},  # R022 first-position WARN
    {"instruction": "q", "output": "a", "chosen": "a"},     # R030
    {"instruction": "你好　世界", "output": "o"},              # R050 (strict only)
]
GARBAGE_LINES = ["{oops", "[1,2", "not json at all", '{"truncated']


class TestFuzzInvariants(unittest.TestCase):
    def test_fuzz_jsonl_invariants(self):
        rng = random.Random(20261008)
        tmp = tempfile.TemporaryDirectory()
        try:
            for case in range(60):
                lines: list[str] = []
                garbage = 0
                pool = [GOOD_ALPACA, GOOD_SHAREGPT, GOOD_OPENAI,
                        *rng.sample(BAD_POOL, rng.randrange(1, len(BAD_POOL)))]
                for _ in range(rng.randrange(0, 30)):
                    if rng.random() < 0.12:
                        lines.append(rng.choice(GARBAGE_LINES))
                        garbage += 1
                    else:
                        lines.append(json.dumps(rng.choice(pool), ensure_ascii=False))
                p = Path(tmp.name) / f"case{case}.jsonl"
                p.write_text("\n".join(lines), encoding="utf-8")
                with self.subTest(case=case):
                    report = inspect_file(str(p))
                    for issue in report.issues:
                        self.assertIn(issue.rule, RULES_KNOWN)
                        self.assertIn(issue.severity, SEVERITIES)
                        self.assertLess(issue.sample_index, max(report.total_samples, 1))
                        self.assertGreaterEqual(issue.sample_index, 0)
                        self.assertLessEqual(len(issue.excerpt), 80)
                    r001 = report.stats().get("R001", 0)
                    self.assertEqual(r001, garbage)
                    if report.total_samples == 0:
                        self.assertEqual(report.dialect, "unknown")
        finally:
            tmp.cleanup()

    def test_rule_ids_stable_across_dialects(self):
        for dialect, sample in (("alpaca", GOOD_ALPACA),
                                ("sharegpt", GOOD_SHAREGPT),
                                ("openai", GOOD_OPENAI)):
            with self.subTest(dialect=dialect):
                tmp = tempfile.TemporaryDirectory()
                try:
                    p = Path(tmp.name) / "a.json"
                    p.write_text(json.dumps(
                        [sample, *BAD_POOL], ensure_ascii=False), encoding="utf-8")
                    report = inspect_file(str(p), dialect=dialect)
                    self.assertTrue(report.issues)
                    for issue in report.issues:
                        self.assertIn(issue.rule, RULES_KNOWN)
                finally:
                    tmp.cleanup()

    def test_100k_line_jsonl_boundary(self):
        tmp = tempfile.TemporaryDirectory()
        try:
            rng = random.Random(20261008)
            p = Path(tmp.name) / "big.jsonl"
            expected_bad = 0
            with p.open("w", encoding="utf-8") as fh:
                for i in range(100000):
                    if i % 10000 == 9999:
                        fh.write('{"instruction": "no output here"}\n')
                        expected_bad += 1
                    else:
                        fh.write(json.dumps(GOOD_ALPACA, ensure_ascii=False) + "\n")
            report = inspect_file(str(p))
            self.assertEqual(report.total_samples, 100000)
            self.assertEqual(report.stats().get("R010", 0), expected_bad)
        finally:
            tmp.cleanup()


if __name__ == "__main__":
    unittest.main()
