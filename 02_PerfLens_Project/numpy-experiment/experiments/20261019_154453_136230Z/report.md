# NumPy argsort benchmark report

| NumPy version | N | Mean (ms) | Median (ms) | SD (ms) | CV (%) |
|---|---:|---:|---:|---:|---:|
| numpy-1.26.4-control-A | 20 | 1.2084 | 1.2011 | 0.0618 | 5.12 |
| numpy-1.26.4-control-B | 20 | 1.3285 | 1.2094 | 0.4085 | 30.75 |

Relative mean change: +9.93%
95% confidence interval of change: [-1.77%, +26.22%]
Statistical direction (CI vs zero): uncertain
Practical threshold: 5%
Decision: **inconclusive**

Positive changes mean slower execution. Regression requires the entire CI above the threshold.
Within-threshold describes this interval, not proof of equal performance.
The percentile bootstrap is approximate. Rounds may remain correlated; no correction for multiple experiments.
Confirm flagged changes in a separate preplanned run on a quiet machine.
One observation is a batch average from one fresh process, not independent loop timings.
CV is SD / mean; it describes variation, not statistical significance.
Configuration: repeats=20, loops=100, warmups=5, sorted array size=100000
Measured Python: 3.12.15
Platform: Windows-11-10.0.26200-SP0
