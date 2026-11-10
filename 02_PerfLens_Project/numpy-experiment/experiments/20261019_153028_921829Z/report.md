# NumPy argsort benchmark report

| NumPy version | N | Mean (ms) | Median (ms) | SD (ms) | CV (%) |
|---|---:|---:|---:|---:|---:|
| numpy-1.26.4 | 5 | 1.2069 | 1.1215 | 0.2147 | 17.79 |
| numpy-2.0.0 | 5 | 3.5653 | 3.7641 | 0.5685 | 15.95 |

Relative mean change: +195.40%
95% confidence interval of change: [+155.34%, +245.15%]
Statistical direction (CI vs zero): slower
Practical threshold: 5%
Decision: **regression**

Positive changes mean slower execution. Regression requires the entire CI above the threshold.
Within-threshold describes this interval, not proof of equal performance.
The percentile bootstrap is approximate. Rounds may remain correlated; no correction for multiple experiments.
Confirm flagged changes in a separate preplanned run on a quiet machine.
One observation is a batch average from one fresh process, not independent loop timings.
CV is SD / mean; it describes variation, not statistical significance.
Configuration: repeats=5, loops=100, warmups=5, sorted array size=100000
Measured Python: 3.12.15
Platform: Windows-11-10.0.26200-SP0

Small sample: fewer than 20 pairs. Treat the interval as a smoke-test estimate.
