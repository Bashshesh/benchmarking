# NumPy argsort benchmark report

| NumPy version | N | Mean (ms) | Median (ms) | SD (ms) | CV (%) |
|---|---:|---:|---:|---:|---:|
| numpy-1.26.4 | 20 | 1.1254 | 1.1642 | 0.1492 | 13.25 |
| numpy-2.0.0 | 20 | 3.7824 | 3.9283 | 0.6158 | 16.28 |

Relative mean change: +236.08%
95% confidence interval of change: [+225.44%, +247.75%]
Statistical direction (CI vs zero): slower
Practical threshold: 5%
Decision: **regression**

Positive changes mean slower execution. Regression requires the entire CI above the threshold.
Within-threshold describes this interval, not proof of equal performance.
The percentile bootstrap is approximate. Rounds may remain correlated; no correction for multiple experiments.
Confirm flagged changes in a separate preplanned run on a quiet machine.
One observation is a batch average from one fresh process, not independent loop timings.
CV is SD / mean; it describes variation, not statistical significance.
Configuration: repeats=20, loops=100, warmups=5, sorted array size=100000
Measured Python: 3.12.15
Platform: Windows-11-10.0.26200-SP0
