# Measured evaluation results

The primary table comes from completed fresh measurements in this suite. The later recovered-data comparison is explicitly historical. No simulated timings are mixed into these results. Internal operation times exclude setup/startup and are not full-application latency.

| Comparison | Reference ms | Candidate ms | Change % | 95% CI % | Classification |
|---|---:|---:|---:|---|---|
| 1_control | 8.2878 | 8.2815 | -0.08 | [-1.14, +1.05] | within_threshold |
| 1_cpu_contention | 8.1577 | 16.1524 | +98.00 | [+85.11, +114.06] | regression |
| 1_cpu_mitigation | 17.0062 | 8.3598 | -50.84 | [-55.17, -45.72] | improvement |
| 1_injection | 8.3977 | 16.9624 | +101.99 | [+94.12, +112.05] | regression |
| 1_java_optimization | 7.6674 | 0.1839 | -97.60 | [-97.63, -97.56] | improvement |
| 1_java_runtime | 0.9699 | 0.1709 | -82.38 | [-82.72, -82.00] | improvement |
| 1_java_warmup | 0.2840 | 0.1738 | -38.79 | [-41.43, -36.23] | improvement |
| 1_python_optimization | 8.4440 | 0.5377 | -93.63 | [-94.00, -93.06] | improvement |
| 1_python_scaling | 24.7553 | 1.5789 | -93.62 | [-93.78, -93.45] | improvement |
| 2_control | 8.2587 | 8.2416 | -0.21 | [-1.55, +1.15] | within_threshold |
| 2_cpu_contention | 8.2607 | 16.0395 | +94.17 | [+78.98, +111.56] | regression |
| 2_cpu_mitigation | 15.7050 | 8.1895 | -47.85 | [-51.16, -44.62] | improvement |
| 2_injection | 8.1838 | 16.2246 | +98.25 | [+96.89, +99.62] | regression |
| 2_java_optimization | 7.6840 | 0.1837 | -97.61 | [-97.63, -97.58] | improvement |
| 2_java_runtime | 0.9523 | 0.1702 | -82.13 | [-82.52, -81.73] | improvement |
| 2_java_warmup | 0.2760 | 0.1697 | -38.50 | [-39.23, -37.76] | improvement |
| 2_python_optimization | 8.1881 | 0.5233 | -93.61 | [-93.71, -93.52] | improvement |

## Classifier validation

Trials here are whole 20-pair comparisons, not inner timing loops. Exact binomial intervals below are descriptive and assume independent comparable trials; the two sessions share a host, so independence/generalization is limited. Two trials cannot establish a reliable general false-positive or detection rate.

- False regression flags: 0/2; exact 95% binomial interval [0.0%, 84.2%]. Outcomes: within_threshold, within_threshold.

- Detected injected slowdowns: 2/2; exact 95% binomial interval [15.8%, 100.0%]. Outcomes: regression, regression.

## Noise and mitigation

CV is sample SD / mean. Lower CV is not automatically less bias or a better estimator. CV-ratio intervals use 2000 paired bootstrap draws and are exploratory. A mitigation may change average duration without reducing variation.

- 1_cpu_contention: CV 0.66% → 17.50%; candidate/reference CV ratio 95% interval [18.26, 33.63]. See per-pair plot and Java warmup traces where applicable.

- 1_cpu_mitigation: CV 20.69% → 6.39%; candidate/reference CV ratio 95% interval [0.06, 0.54]. See per-pair plot and Java warmup traces where applicable.

- 1_java_warmup: CV 6.84% → 5.86%; candidate/reference CV ratio 95% interval [0.39, 2.84]. See per-pair plot and Java warmup traces where applicable.

- 2_cpu_contention: CV 5.59% → 18.28%; candidate/reference CV ratio 95% interval [1.51, 21.77]. See per-pair plot and Java warmup traces where applicable.

- 2_cpu_mitigation: CV 15.42% → 2.45%; candidate/reference CV ratio 95% interval [0.06, 1.28]. See per-pair plot and Java warmup traces where applicable.

- 2_java_warmup: CV 2.55% → 1.42%; candidate/reference CV ratio 95% interval [0.26, 1.08]. See per-pair plot and Java warmup traces where applicable.

## No regression and absolute targets

The graph target is a preselected illustrative mean-operation budget of 3 ms, not a real application SLA. Assessment uses the observed mean; it makes no tail-latency or confidence guarantee.
- 1_control: {'reference': False, 'unchanged': False}.
- 1_python_optimization: {'repeated_BFS': False, 'reuse_BFS': True}.
- 1_python_scaling: {'repeated_BFS': False, 'reuse_BFS': True}.
- 2_control: {'reference': False, 'unchanged': False}.
- 2_python_optimization: {'repeated_BFS': False, 'reuse_BFS': True}.

## Comparative methodology evaluation

Paired interval classification quantifies uncertainty and can remain inconclusive. A point-estimate-only ±5% rule cannot express uncertainty. The minimum-time ratio is recorded in comparisons.csv; it describes best observed timings and is not the mean-change estimand. No significance test is performed on minima.

Point-only versus interval classification differs for 0 of 17 comparisons: none.

The deliberately large effects in this suite are easy cases; agreement does not establish that point-only classification is generally adequate.

Warmup traces allow inspection but no changepoint analysis or steady-state proof is implemented. Process-wall means in comparisons.json include startup/setup; never substitute them for internal times when interpreting the optimization magnitude.

## Repeatability and limitations

Session 2 is a preplanned held-out confirmation with fresh processes and a different order seed. It is same-host repeatability, not reproduction on another machine. The suite provides limited workloads, one host and JVM, no power calculation, approximate bootstrap coverage, no multiple-testing adjustment, and no measurements of energy, memory or end-to-end user impact. Source/runtime effects are conditional on these exact workloads. Large improvements from deliberately redundant BFS or linear search do not establish improvements across all of NetworkX or Java.

All original project results remain separate. Five supplied NetworkX/NumPy datasets were recovered and their stored analyses exactly recomputed in results/original-audit.json.

![Effect intervals](effects.png)

## Recovered original data: uncertainty changes the decision

This table reuses the previous group’s raw data, whose analysis was checked exactly. These are not new timings or additional validation trials.

| Historical dataset | Pairs | Mean change % | Point-only ±5% | Paired-CI decision |
|---|---:|---:|---|---|
| original\misc\experiments\20261018_175350_179456Z | 20 | +0.56 | within_threshold | within_threshold |
| original\misc\experiments\20261018_180546_746006Z | 30 | +1.49 | within_threshold | inconclusive |
| original\misc\numpy-experiment\experiments\20261019_153028_921829Z | 5 | +195.40 | regression | regression |
| original\misc\numpy-experiment\experiments\20261019_153158_134656Z | 20 | +236.08 | regression | regression |
| original\misc\numpy-experiment\experiments\20261019_154453_136230Z | 20 | +9.93 | regression | inconclusive |

In the original NumPy unchanged-version control, +9.93% would trigger a point-only regression alarm, while the interval [-1.77%, +26.22%] yields inconclusive. In the 30-pair original NetworkX case, +1.49% is inside the point tolerance, but its interval extends to +7.03%, so the interval rule remains inconclusive. These examples show the role of uncertainty; they do not estimate general classifier accuracy.
