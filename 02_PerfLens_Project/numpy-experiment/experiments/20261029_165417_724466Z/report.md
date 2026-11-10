# NumPy argsort benchmark report

| NumPy version | N | Mean (ms) | Median (ms) | SD (ms) | CV (%) |
|---|---:|---:|---:|---:|---:|
| numpy-1.26.4 | 20 | 0.6049 | 0.6002 | 0.0179 | 2.96 |
| numpy-2.0.0 | 20 | 2.0085 | 2.0174 | 0.0464 | 2.31 |

Relative mean change: +232.03%
95% confidence interval of change: [+227.35%, +236.25%]
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
Measured Python: 3.12.14
Platform: Windows-11-10.0.26200-SP0
