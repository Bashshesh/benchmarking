# NumPy argsort benchmark report

| NumPy version | N | Mean (ms) | Median (ms) | SD (ms) | CV (%) |
|---|---:|---:|---:|---:|---:|
| numpy-1.26.4-control-A | 20 | 0.6073 | 0.5994 | 0.0228 | 3.75 |
| numpy-1.26.4-control-B | 20 | 0.5958 | 0.5936 | 0.0104 | 1.75 |

Relative mean change: -1.88%
95% confidence interval of change: [-3.72%, -0.21%]
Statistical direction (CI vs zero): faster
Practical threshold: 5%
Decision: **within_threshold**

Positive changes mean slower execution. Regression requires the entire CI above the threshold.
Within-threshold describes this interval, not proof of equal performance.
The percentile bootstrap is approximate. Rounds may remain correlated; no correction for multiple experiments.
Confirm flagged changes in a separate preplanned run on a quiet machine.
One observation is a batch average from one fresh process, not independent loop timings.
CV is SD / mean; it describes variation, not statistical significance.
Configuration: repeats=20, loops=100, warmups=5, sorted array size=100000
Measured Python: 3.12.14
Platform: Windows-11-10.0.26200-SP0
