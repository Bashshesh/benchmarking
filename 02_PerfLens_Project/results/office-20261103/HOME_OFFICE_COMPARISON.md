# Office reproduction: host-separated comparison

Measured on 3 November 2026 with the fixed office protocol. All 17 comparisons completed, 20 pairs each, 680 fresh-process observations. All CSV/JSONL values, snapshot hashes, frozen configurations, raw hashes and saved summary reanalysis passed checks.

Home: AMD Ryzen 5 5500 and the recorded home OpenJDK. Office: Intel Core Ultra 7 155H, Windows 11, Python 3.12.14, Oracle JDK 21.0.8, Balanced power scheme. Different host and runtime settings are not a single-factor hardware experiment. Raw observations are never pooled. Effects below are separately estimated within each host.

| Comparison | Home change % [95% CI] | Home decision | Office change % [95% CI] | Office decision |
|---|---|---|---|---|
| 1_control | -0.08 [-1.14, +1.05] | within_threshold | -7.60 [-21.84, +15.36] | inconclusive |
| 1_cpu_contention | +98.00 [+85.11, +114.06] | regression | +52.30 [+20.90, +87.00] | regression |
| 1_cpu_mitigation | -50.84 [-55.17, -45.72] | improvement | -38.13 [-44.70, -30.38] | improvement |
| 1_injection | +101.99 [+94.12, +112.05] | regression | +121.47 [+88.85, +157.11] | regression |
| 1_java_optimization | -97.60 [-97.63, -97.56] | improvement | -97.10 [-97.44, -96.70] | improvement |
| 1_java_runtime | -82.38 [-82.72, -82.00] | improvement | -75.84 [-84.25, -65.82] | improvement |
| 1_java_warmup | -38.79 [-41.43, -36.23] | improvement | -49.85 [-56.26, -42.26] | improvement |
| 1_python_optimization | -93.63 [-94.00, -93.06] | improvement | -94.32 [-94.99, -93.60] | improvement |
| 1_python_scaling | -93.62 [-93.78, -93.45] | improvement | -94.43 [-94.94, -93.87] | improvement |
| 2_control | -0.21 [-1.55, +1.15] | within_threshold | -0.94 [-14.65, +15.50] | inconclusive |
| 2_cpu_contention | +94.17 [+78.98, +111.56] | regression | +71.85 [+39.79, +114.27] | regression |
| 2_cpu_mitigation | -47.85 [-51.16, -44.62] | improvement | -45.07 [-50.29, -38.90] | improvement |
| 2_injection | +98.25 [+96.89, +99.62] | regression | +115.39 [+87.42, +144.14] | regression |
| 2_java_optimization | -97.61 [-97.63, -97.58] | improvement | -97.37 [-97.62, -97.08] | improvement |
| 2_java_runtime | -82.13 [-82.52, -81.73] | improvement | -66.68 [-73.77, -57.80] | improvement |
| 2_java_warmup | -38.50 [-39.23, -37.76] | improvement | -45.96 [-52.87, -37.86] | improvement |
| 2_python_optimization | -93.61 [-93.71, -93.52] | improvement | -93.48 [-94.57, -92.19] | improvement |

Decisions differ for 2/17 comparisons: 1_control, 2_control.

Classification agreement is descriptive; it does not establish equal effect sizes or statistical equivalence across machines. Inconclusive results are retained and not rerun to obtain agreement. The two sessions inside each host assess repeatability; agreement between hosts is a bounded reproduction result for these workloads. See the complete office report for CV intervals, absolute target assessments and warmup traces.

CPU placement on a hybrid processor may change performance class/cache as well as contention. Fixed warmup does not establish steady state. Twenty paired rounds do not prove independence or bootstrap coverage. No memory, energy, sorting preparation, or application-level benefit was measured.

The original NetworkX historical-commit and NumPy pinned-release workflows were restored and their supplied saved data audited, but were not freshly timed on this office host in this run. This statement distinguishes them from the new graph/Java 17-case evaluation.

Previous group authors: Ansar Bashayev, Thanh Tra Nguyen and Dasol Jung. The office helpers, audit adaptation and technical notes were produced with OpenAI Codex assistance. Original attribution and unchanged home data remain in the package. This is a technical results note; the updated seminar paper and presentation remain deferred.

Office suite: `results/office-20261103/20261103T152546Z_evaluation`.
