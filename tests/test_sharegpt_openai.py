"""Vectors + invariant tests for sharegpt / openai dialects and R021-R060."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from sftcheck import inspect_file

SHAREGPT_GOOD = {
    "conversations": [
        {"from": "human", "value": "hi"},
        {"from": "gpt", "value": "hello"},
    ],
    "system": "be nice",
}
OPENAI_GOOD = {
    "messages": [
        {"role": "system", "content": "be nice"},
        {"role": "user", "content": "hi"},
        {"role": "assistant", "content": "hello"},
    ],
}


class TestSharegpt(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def _write(self, payload, name="a.json"):
        p = self.tmp_path / name
        p.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        return str(p)

    def test_good_sharegpt_clean(self):
        report = inspect_file(self._write([SHAREGPT_GOOD]))
        self.assertEqual(report.dialect, "sharegpt")
        self.assertEqual(report.issues, ())

    def test_r021_parity_violations(self):
        report = inspect_file(self._write([
            {"conversations": [{"from": "gpt", "value": "hello first"}]},
            {"conversations": [{"from": "human", "value": "a"},
                                {"from": "human", "value": "b"}]},
        ]))
        r021 = [i for i in report.issues if i.rule == "R021"]
        self.assertEqual(len(r021), 2)
        self.assertEqual({i.sample_index for i in r021}, {0, 1})
        self.assertTrue(all(i.severity == "ERROR" for i in r021))

    def test_r010_missing_conversations(self):
        report = inspect_file(self._write([{"system": "x"}]), dialect="sharegpt")
        r010 = [i for i in report.issues if i.rule == "R010"]
        self.assertEqual(len(r010), 1)
        self.assertEqual(r010[0].field, "conversations")

    def test_r011_conversations_shapes(self):
        report = inspect_file(self._write([
            {"conversations": "not a list"},
            {"conversations": ["not a dict"]},
            {"conversations": [{"from": 1, "value": "x"}]},
            {"conversations": [{"from": "human", "value": 5}]},
        ]))
        self.assertEqual({i.rule for i in report.issues}, {"R011"})
        self.assertEqual(len(report.issues), 4)

    def test_r060_nonstandard_role(self):
        report = inspect_file(self._write([
            {"conversations": [{"from": "bot", "value": "hey"},
                                {"from": "gpt", "value": "o"}]},
        ]))
        r060 = [i for i in report.issues if i.rule == "R060"]
        self.assertEqual(len(r060), 1)
        self.assertIn("'bot'", r060[0].message)

    def test_r020_empty_conversations(self):
        report = inspect_file(self._write([{"conversations": []}]))
        self.assertIn("R020", report.stats())

    def test_openai_dialect_and_r022(self):
        report = inspect_file(self._write([OPENAI_GOOD]))
        self.assertEqual(report.dialect, "openai")
        self.assertEqual(report.issues, ())
        report = inspect_file(self._write([
            {"messages": [{"role": "bot", "content": "x"}]},
            {"messages": [{"role": "assistant", "content": "y"},
                          {"role": "user", "content": "z"}]},
        ]))
        r022 = [i for i in report.issues if i.rule == "R022"]
        self.assertEqual(len(r022), 2)
        self.assertEqual({i.severity for i in r022}, {"ERROR", "WARN"})


class TestCrossCuttingRules(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def _write(self, payload, name="a.json"):
        p = self.tmp_path / name
        p.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        return str(p)

    def test_r030_preference_fields(self):
        report = inspect_file(self._write([
            {"instruction": "q", "output": "a", "chosen": "a", "rejected": "b"}]))
        r030 = [i for i in report.issues if i.rule == "R030"]
        self.assertEqual(len(r030), 1)
        self.assertIn("#3793", r030[0].message)

    def test_r040_duplicate_group(self):
        dup = {"instruction": "q", "output": "a"}
        report = inspect_file(self._write([dup, dup,
                                           {"instruction": "q2", "output": "a2"}]))
        r040 = [i for i in report.issues if i.rule == "R040"]
        self.assertEqual(len(r040), 1)
        self.assertIn("[0, 1]", r040[0].message)

    def test_r050_strict_only(self):
        sample = {"instruction": "你好　世界",  # U+3000 ideographic space
                  "output": "ok"}
        strict = inspect_file(self._write([sample]), strict=True)
        loose = inspect_file(self._write([sample]))
        self.assertIn("R050", strict.stats())
        self.assertNotIn("R050", loose.stats())
        self.assertEqual(strict.issues[0].severity, "INFO")

    def test_r050_traditional_simplified_mix(self):
        sample = {"instruction": "這個时间很好用", "output": "ok"}  # 這個 trad + 软件 simp
        report = inspect_file(self._write([sample]), strict=True)
        r050 = [i for i in report.issues if i.rule == "R050"]
        self.assertTrue(any("繁简混杂" in i.message for i in r050))


class TestCli(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def _run(self, *args):
        import subprocess
        import sys
        import os
        env = dict(os.environ)
        env["PYTHONPATH"] = "src"
        env["PYTHONIOENCODING"] = "utf-8"
        return subprocess.run(
            [sys.executable, "-m", "sftcheck", *args],
            capture_output=True, env=env, cwd=Path(__file__).resolve().parent.parent,
        )

    def _write(self, payload, name="a.json"):
        p = self.tmp_path / name
        p.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        return str(p)

    def test_exit_0_on_clean(self):
        proc = self._run(self._write([{"instruction": "q", "output": "a"}]))
        self.assertEqual(proc.returncode, 0)

    def test_exit_1_on_error(self):
        proc = self._run(self._write([{"instruction": "q"}]))
        self.assertEqual(proc.returncode, 1)
        self.assertIn("R010", proc.stdout.decode("utf-8"))

    def test_exit_2_on_unreadable(self):
        proc = self._run(str(self.tmp_path / "missing.json"))
        self.assertEqual(proc.returncode, 2)

    def test_min_severity_filters_display(self):
        proc = self._run(self._write([{"instruction": "q", "output": "a", "chosen": "a"}]),
                         "--min-severity", "ERROR")
        out = proc.stdout.decode("utf-8")
        self.assertNotIn("[WARN] R030", out)
        self.assertEqual(proc.returncode, 0)  # WARN only, no ERROR

    def test_strict_flag_enables_r050(self):
        proc = self._run(self._write([{"instruction": "你好　世界", "output": "o"}]),
                         "--strict", "--min-severity", "INFO")
        self.assertIn("R050", proc.stdout.decode("utf-8"))


if __name__ == "__main__":
    unittest.main()
