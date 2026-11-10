# Measured evaluation results

The primary table comes from completed fresh measurements in this suite. The later recovered-data comparison is explicitly historical. No simulated timings are mixed into these results. Internal operation times exclude setup/startup and are not full-application latency.

| Comparison | Reference ms | Candidate ms | Change % | 95% CI % | Classification |
|---|---:|---:|---:|---|---|
| 1_control | 17.3430 | 16.5443 | -4.61 | [-15.24, +8.48] | inconclusive |
| 1_cpu_contention | 13.0576 | 24.1374 | +84.85 | [+64.50, +105.16] | regression |
| 1_cpu_mitigation | 27.0764 | 14.8602 | -45.12 | [-55.01, -32.99] | improvement |
| 1_injection | 9.2994 | 18.3611 | +97.44 | [+78.31, +117.74] | regression |
| 1_java_optimization | 12.1432 | 0.3394 | -97.20 | [-97.47, -96.86] | improvement |
| 1_java_runtime | 1.0883 | 0.3287 | -69.80 | [-71.52, -67.73] | improvement |
| 1_java_warmup | 0.7089 | 0.3399 | -52.06 | [-62.78, -39.61] | improvement |
| 1_python_optimization | 9.0831 | 0.5264 | -94.21 | [-94.69, -93.59] | improvement |
| 1_python_scaling | 44.3779 | 2.8400 | -93.60 | [-94.14, -92.99] | improvement |
| 2_control | 16.7352 | 15.3592 | -8.22 | [-19.46, +5.39] | inconclusive |
| 2_cpu_contention | 12.7998 | 24.1898 | +88.99 | [+60.78, +117.40] | regression |
| 2_cpu_mitigation | 22.8375 | 12.0466 | -47.25 | [-54.60, -38.31] | improvement |
| 2_injection | 21.9057 | 39.2859 | +79.34 | [+64.45, +95.78] | regression |
| 2_java_optimization | 21.7657 | 0.5326 | -97.55 | [-97.84, -97.19] | improvement |
| 2_java_runtime | 2.5771 | 0.5744 | -77.71 | [-82.04, -71.60] | improvement |
| 2_java_warmup | 0.8392 | 0.5416 | -35.46 | [-43.88, -26.27] | improvement |
| 2_python_optimization | 19.6900 | 1.2974 | -93.41 | [-94.07, -92.76] | improvement |

## Classifier validation

Trials here are whole 20-pair comparisons, not inner timing loops. Exact binomial intervals below are descriptive and assume independent comparable trials; the two sessions share a host, so independence/generalization is limited. Two trials cannot establish a reliable general false-positive or detection rate.

- False regression flags: 0/2; exact 95% binomial interval [0.0%, 84.2%]. Outcomes: inconclusive, inconclusive.

- Detected injected slowdowns: 2/2; exact 95% binomial interval [15.8%, 100.0%]. Outcomes: regression, regression.

## Noise and mitigation

CV is sample SD / mean. Lower CV is not automatically less bias or a better estimator. CV-ratio intervals use 2000 paired bootstrap draws and are exploratory. A mitigation may change average duration without reducing variation.

- 1_cpu_contention: CV 11.99% → 27.30%; candidate/reference CV ratio 95% interval [1.59, 4.56]. See per-pair plot and Java warmup traces where applicable.

- 1_cpu_mitigation: CV 59.97% → 35.79%; candidate/reference CV ratio 95% interval [0.42, 0.77]. See per-pair plot and Java warmup traces where applicable.

- 1_java_warmup: CV 49.03% → 21.08%; candidate/reference CV ratio 95% interval [0.18, 1.94]. See per-pair plot and Java warmup traces where applicable.

- 2_cpu_contention: CV 8.39% → 33.61%; candidate/reference CV ratio 95% interval [2.63, 7.09]. See per-pair plot and Java warmup traces where applicable.

- 2_cpu_mitigation: CV 35.38% → 8.75%; candidate/reference CV ratio 95% interval [0.16, 0.37]. See per-pair plot and Java warmup traces where applicable.

- 2_java_warmup: CV 25.59% → 35.47%; candidate/reference CV ratio 95% interval [0.91, 1.98]. See per-pair plot and Java warmup traces where applicable.

## No regression and absolute targets

The graph target is a preselected illustrative mean-operation budget of 3 ms, not a real application SLA. Assessment uses the observed mean; it makes no tail-latency or confidence guarantee.
- 1_control: {'reference': False, 'unchanged': False}.
- 1_python_optimization: {'repeated_BFS': False, 'reuse_BFS': True}.
- 1_python_scaling: {'repeated_BFS': False, 'reuse_BFS': True}.
- 2_control: {'reference': False, 'unchanged': False}.
- 2_python_optimization: {'repeated_BFS': False, 'reuse_BFS': True}.

## Comparative methodology evaluation

Paired interval classification quantifies uncertainty and can remain inconclusive. A point-estimate-only ±5% rule cannot express uncertainty. The minimum-time ratio is recorded in comparisons.csv; it describes best observed timings and is not the mean-change estimand. No significance test is performed on minima.

Point-only versus interval classification differs for 2 of 17 comparisons: 1_control, 2_control.

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
