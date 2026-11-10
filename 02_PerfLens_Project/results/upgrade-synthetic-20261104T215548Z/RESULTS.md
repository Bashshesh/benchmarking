# Synthetic classifier operating characteristics

Generated distributions, not benchmark observations. The original 5000-resample classifier and5% rule are unchanged. Every cell contains independent generated20-pair datasets with separate generation and bootstrap random streams. Boundary+5% cases are not binary ground truth. Inconclusive decisions are reported separately from decisive false negatives.

| True mean effect | Residual CV | Runs | Regression | Improvement | Within | Inconclusive | Empirical interval coverage |
|---|---|---:|---:|---:|---:|---:|---:|
| +0% | 1% | 30 | 0 | 0 | 30 | 0 | 90.0% |
| +0% | 5% | 30 | 0 | 0 | 20 | 10 | 90.0% |
| +0% | 20% | 30 | 0 | 1 | 0 | 29 | 90.0% |
| +2% | 1% | 30 | 0 | 0 | 30 | 0 | 93.3% |
| +2% | 5% | 30 | 0 | 0 | 15 | 15 | 86.7% |
| +2% | 20% | 30 | 0 | 0 | 0 | 30 | 93.3% |
| +5% | 1% | 30 | 1 | 0 | 1 | 28 | 93.3% |
| +5% | 5% | 30 | 1 | 0 | 2 | 27 | 90.0% |
| +5% | 20% | 30 | 0 | 0 | 0 | 30 | 93.3% |
| +10% | 1% | 30 | 30 | 0 | 0 | 0 | 83.3% |
| +10% | 5% | 30 | 23 | 0 | 0 | 7 | 90.0% |
| +10% | 20% | 30 | 7 | 0 | 0 | 23 | 90.0% |
| +30% | 1% | 30 | 30 | 0 | 0 | 0 | 86.7% |
| +30% | 5% | 30 | 30 | 0 | 0 | 0 | 90.0% |
| +30% | 20% | 30 | 30 | 0 | 0 | 0 | 100.0% |
| -15% | 1% | 30 | 0 | 30 | 0 | 0 | 83.3% |
| -15% | 5% | 30 | 0 | 30 | 0 | 0 | 96.7% |
| -15% | 20% | 30 | 0 | 10 | 0 | 20 | 93.3% |

Each flag-rate exact binomial interval and confusion counts are retained in summary.json. Empirical coverage here is conditional on this simulation model and modest repetitions, not proof of nominal coverage or independence for real timing runs. No measured nominal work fraction is used as a guaranteed timing-effect label.
