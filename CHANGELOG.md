# Changelog

All notable changes are documented here. Versions follow SemVer; pre-release
versions (a/b/rc) must never be presented as stable.

## 0.1.0a1 (unreleased)

- Initial release: pre-flight structural auditing for SFT fine-tuning datasets
  in three dialects — alpaca, sharegpt, OpenAI (spec anchored to LlamaFactory
  `data/README.md`, blob `e43e0eed…`, embedded as `spec_version` in every
  report).
- Rule set R001–R060: JSON parsing with per-line isolation for broken jsonl
  (R001), undetectable dialect (R009), missing required fields (R010), type
  errors (R011), empty messages (R020), sharegpt role-parity violations (R021),
  OpenAI role validity and first-message position (R022), history shape (R023),
  preference fields inside SFT data (R030, cf. LlamaFactory #3793),
  exact-duplicate groups (R040), Chinese-quality signals — fullwidth spaces /
  U+FFFD / traditional-simplified mixing heuristic (R050, INFO, `--strict`
  only), non-standard roles (R060).
- Dialect auto-detection with explicit override; every report embeds
  `spec_version`.
- CLI training gate `python -m sftcheck`: exit 0 = no ERROR, 1 = ERROR found,
  2 = file unreadable; `--min-severity` display threshold.
- Evidence model: frozen `Issue` / `Report` dataclasses; `sample_index` is
  invariant (< total_samples, fuzz-guarded — a trailing broken jsonl line was
  found by fuzz and clamped); `excerpt` is a bounded prefix of the offending
  value.
- Boundary fuzz suite (60 seeded cases, 100k-line file) and reproducible
  benchmarks: ~180k samples/second, linear (benchmarks/RESULTS.md).
- Known limitations: exact-hash dedup only (no semantic near-duplicates);
  O(n) memory (jsonl sharding recommended for very large files); .json/.jsonl
  only (csv/parquet/arrow get explicit downgrade messages); spec follows
  LlamaFactory — other frameworks not promised.
- 34 tests.
