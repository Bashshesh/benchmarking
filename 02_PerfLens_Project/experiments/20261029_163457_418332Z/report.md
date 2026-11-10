# NetworkX benchmark report

| Commit | N | Mean (ms) | Median (ms) | SD (ms) | CV (%) |
|---|---:|---:|---:|---:|---:|
| 87b57851e9 | 20 | 0.5432 | 0.5318 | 0.0239 | 4.39 |
| 6da4704cbf | 20 | 0.5398 | 0.5316 | 0.0244 | 4.52 |

Relative mean change: -0.64%
95% confidence interval of change: [-2.96%, +2.12%]
Statistical direction (CI vs zero): uncertain
Practical threshold: 5%
Decision: **within_threshold**

Positive changes mean slower execution. Regression requires the entire CI above the threshold.
Within-threshold describes this interval, not proof of equal performance.
The percentile bootstrap is approximate. Rounds may remain correlated; no correction for multiple experiments.
Confirm flagged changes in a separate preplanned run on a quiet machine.
One observation is a batch average from one fresh process, not independent loop timings.
CV is SD / mean; it describes variation, not statistical significance.
Configuration: repeats=20, loops=100, warmups=3, grid=35 x 35
Python: 3.12.14 (main, Aug 25 2026, 14:01:42) [MSC v.1944 64 bit (AMD64)]
Platform: Windows-11-10.0.26200-SP0
