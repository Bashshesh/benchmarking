# NetworkX benchmark report

| Commit | N | Mean (ms) | Median (ms) | SD (ms) | CV (%) |
|---|---:|---:|---:|---:|---:|
| 87b57851e9 | 30 | 0.5158 | 0.4995 | 0.0400 | 7.75 |
| 6da4704cbf | 30 | 0.5235 | 0.4998 | 0.0651 | 12.43 |

Relative mean change: +1.49%
95% confidence interval of change: [-3.40%, +7.03%]
Statistical direction (CI vs zero): uncertain
Practical threshold: 5%
Decision: **inconclusive**

Positive changes mean slower execution. Regression requires the entire CI above the threshold.
Within-threshold describes this interval, not proof of equal performance.
The percentile bootstrap is approximate. Rounds may remain correlated; no correction for multiple experiments.
Confirm flagged changes in a separate preplanned run on a quiet machine.
One observation is a batch average from one fresh process, not independent loop timings.
CV is SD / mean; it describes variation, not statistical significance.
Configuration: repeats=30, loops=200, warmups=5, grid=35 x 35
Python: 3.13.13 (tags/v3.13.13:01104ce, Apr  7 2026, 19:25:48) [MSC v.1944 64 bit (AMD64)]
Platform: Windows-11-10.0.26200-SP0
