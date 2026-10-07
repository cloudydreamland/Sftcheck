"""Known vectors + invariant tests for the alpaca dialect (S3-1 scope)."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from sftcheck import Issue, inspect_file
from sftcheck.model import SPEC_VERSION


def write(tmp: Path, name: str, payload) -> str:
    p = tmp / name
    if name.endswith(".jsonl"):
        p.write_text("\n".join(json.dumps(x, ensure_ascii=False) for x in payload), encoding="utf-8")
    else:
        p.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return str(p)


GOOD = {
    "instruction": "把下面的话翻译成英文",
    "input": "今天天气不错",
    "output": "The weather is nice today.",
}


class TestAlpacaBasics(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_good_sample_clean(self):
        report = inspect_file(write(self.tmp_path, "a.json", [GOOD]))
        self.assertEqual(report.dialect, "alpaca")
        self.assertEqual(report.dialect_confidence, "detected")
        self.assertEqual(report.issues, ())
        self.assertEqual(report.total_samples, 1)
        self.assertEqual(report.spec_version, SPEC_VERSION)

    def test_explicit_dialect(self):
        report = inspect_file(write(self.tmp_path, "a.json", [GOOD]), dialect="alpaca")
        self.assertEqual(report.dialect_confidence, "explicit")

    def test_issue_7577_keyerror_instruction_vector(self):
        # LlamaFactory #7577: a sharegpt-styled file fed to an alpaca loader
        # crashes with KeyError: 'instruction'. sftcheck reports it pre-flight.
        sharegpt_styled = {"conversations": [{"from": "human", "value": "hi"},
                                             {"from": "gpt", "value": "hello"}]}
        report = inspect_file(write(self.tmp_path, "a.json", [sharegpt_styled]),
                              dialect="alpaca")
        rules = {i.rule for i in report.issues}
        self.assertIn("R010", rules)
        fields = {i.field for i in report.issues if i.rule == "R010"}
        self.assertEqual(fields, {"instruction", "output"})
        self.assertTrue(all(i.severity == "ERROR" for i in report.issues))

    def test_r010_missing_output(self):
        sample = {"instruction": "q"}
        report = inspect_file(write(self.tmp_path, "a.json", [sample]))
        self.assertIn("R010", report.stats())
        self.assertIn("output", {i.field for i in report.issues if i.rule == "R010"})

    def test_r011_type_errors(self):
        report = inspect_file(write(self.tmp_path, "a.json", [
            {"instruction": 123, "output": None, "input": ["x"], "system": 5}]))
        self.assertEqual({i.rule for i in report.issues}, {"R011"})
        self.assertEqual({i.field for i in report.issues},
                         {"instruction", "output", "input", "system"})

    def test_r020_empty_strings_are_warns(self):
        report = inspect_file(write(self.tmp_path, "a.json", [
            {"instruction": "   ", "output": ""}]))
        self.assertEqual({i.rule for i in report.issues}, {"R020"})
        self.assertTrue(all(i.severity == "WARN" for i in report.issues))
        self.assertEqual({i.field for i in report.issues}, {"instruction", "output"})

    def test_r023_history_shapes(self):
        report = inspect_file(write(self.tmp_path, "a.json", [
            {**GOOD, "history": ["not", "a", "pair"]},
            {**GOOD, "history": [[1, 2]]},
            {**GOOD, "history": [["u", "m"]]},
        ]))
        r023 = [i for i in report.issues if i.rule == "R023"]
        # per-item granularity: the 3 bad strings + the 1 bad pair
        self.assertEqual(len(r023), 4)
        self.assertTrue(all(i.severity == "WARN" for i in r023))
        self.assertEqual({i.sample_index for i in r023}, {0, 1})


class TestLoadingAndInvariants(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_r001_jsonl_broken_line_is_isolated(self):
        p = self.tmp_path / "a.jsonl"
        good = json.dumps(GOOD, ensure_ascii=False)
        p.write_text(good + "\n{broken json\n" + good, encoding="utf-8")
        report = inspect_file(str(p))
        self.assertEqual(report.total_samples, 2)
        r001 = [i for i in report.issues if i.rule == "R001"]
        self.assertEqual(len(r001), 1)
        self.assertEqual(r001[0].line_no, 2)
        self.assertEqual(r001[0].sample_index, 1)

    def test_r001_json_top_level_not_list(self):
        p = self.tmp_path / "a.json"
        p.write_text(json.dumps(GOOD, ensure_ascii=False), encoding="utf-8")
        report = inspect_file(str(p))
        self.assertEqual([i.rule for i in report.issues], ["R001"])

    def test_r001_json_parse_error(self):
        p = self.tmp_path / "a.json"
        p.write_text("{not json", encoding="utf-8")
        report = inspect_file(str(p))
        self.assertEqual([i.rule for i in report.issues], ["R001"])

    def test_sample_index_invariant_and_excerpt_prefix(self):
        value = "长" * 200
        report = inspect_file(write(self.tmp_path, "a.json", [
            {**GOOD, "instruction": 42}, ]))
        issue = report.issues[0]
        self.assertEqual(issue.sample_index, 0)
        self.assertLessEqual(len(issue.excerpt), 80)
        # excerpt is a prefix of the JSON rendering of the offending value
        self.assertTrue(json.dumps(42, ensure_ascii=False).startswith(issue.excerpt[:10]))

    def test_summary_mentions_counts(self):
        report = inspect_file(write(self.tmp_path, "a.json", [
            {"instruction": "", "output": ""}]))
        text = report.summary()
        self.assertIn("alpaca", text)
        self.assertIn("WARN 2", text)

    def test_unknown_dialect_warns(self):
        report = inspect_file(write(self.tmp_path, "a.json", [{"foo": "bar"}]))
        self.assertEqual(report.dialect, "unknown")
        self.assertTrue(any("无法" in i.message for i in report.issues))

    def test_unsupported_extension_raises_valueerror(self):
        p = self.tmp_path / "a.csv"
        p.write_text("a,b\n1,2", encoding="utf-8")
        with self.assertRaises(ValueError):
            inspect_file(str(p))

    def test_issue_is_frozen_dataclass(self):
        issue = Issue("R010", "ERROR", 0, None, "instruction", "msg")
        with self.assertRaises(Exception):
            issue.rule = "R011"  # type: ignore[misc]


if __name__ == "__main__":
    unittest.main()
