# NetworkX benchmark report

| Commit | N | Mean (ms) | Median (ms) | SD (ms) | CV (%) |
|---|---:|---:|---:|---:|---:|
| 87b57851e9 | 20 | 0.4665 | 0.4603 | 0.0224 | 4.80 |
| 6da4704cbf | 20 | 0.4691 | 0.4605 | 0.0282 | 6.02 |

Relative mean change: +0.56%
95% confidence interval of change: [-2.71%, +4.25%]
Statistical direction (CI vs zero): uncertain
Practical threshold: 5%
Decision: **within_threshold**

Positive changes mean slower execution. Regression requires the entire CI above the threshold.
Within-threshold describes this interval, not proof of equal performance.
The percentile bootstrap is approximate. Rounds may remain correlated; no correction for multiple experiments.
Confirm flagged changes in a separate preplanned run on a quiet machine.
One observation is a batch average from one fresh process, not independent loop timings.
CV is SD / mean; it describes variation, not statistical significance.
Configuration: repeats=20, loops=200, warmups=3, grid=35 x 35
Python: 3.13.13 (tags/v3.13.13:01104ce, Apr  7 2026, 19:25:48) [MSC v.1944 64 bit (AMD64)]
Platform: Windows-11-10.0.26200-SP0
