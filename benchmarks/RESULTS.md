# sftcheck 基准结果（真实运行，非虚构）

- 日期：2026-10-08（D-S4-1）
- 命令：`cd /e/n_projects/sftcheck && PYTHONPATH=src python benchmarks/run_bench.py`
- 环境：Python 3.13.2 (64bit) / Windows-11-10.0.26200-SP0 / Intel64 Family 6 Model 183（13 代酷睿桌面级，型号未单独核验）
- 方法：**合成 jsonl**（`random.Random(20261008)`，中英文混合池，按比例植入 R010 坏样本与 sharegpt 样本）；每格 5 次取 best/median（`time.perf_counter`）；数字仅同机同版本可比。

## 原始输出（逐字粘贴，2026-10-08 实跑，clamp 修复后最终版）

```text
== sftcheck benchmark ==
python     : 3.13.2 (64bit)
platform   : Windows-11-10.0.26200-SP0
processor  : Intel64 Family 6 Model 183 Stepping 1, GenuineIntel
method     : best/median of 5 runs per cell, time.perf_counter, seeded synthetic jsonl (seed=20261008)

sample           lines   best(ms)  median(ms)  best samples/s   issues
1000 lines        1000        5.5         5.7         182,532       28
10000 lines      10000       55.6        57.2         179,950       28
50000 lines      50000      275.3       283.2         181,599       28

(all cells include full rule set R001-R060 except R050/--strict)
```

## 观察与诚实结论

1. **吞吐约 18 万样本/秒，线性扩展**（1k→10k→50k 每样本耗时稳定在 ~5.5µs）；50,000 行全规则审计 0.28 秒——千万级数据集约 1 小时内可完成预检。
2. 内存为 O(n)：R040 精确去重需要全样本哈希集合，json 数组本身也整体加载——**超大文件建议用 jsonl 分片**；该限制记录于 DESIGN §5（诚实边界）。
3. issues=28 恒定：种子固定的坏样本植入比例所致（bad_every = size//20），符合预期，不是性能异常。
4. 中间版本测量（clamp 修复前 5.4ms/52.4ms/277.5ms）与最终版差异在噪声内——不变量修复无性能代价。
5. 不同机器/Python 版本数字会不同；禁止脱离环境引用本页数字。
