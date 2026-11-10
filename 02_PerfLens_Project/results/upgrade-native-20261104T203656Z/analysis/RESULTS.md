# Native upgrade measurements

Fresh-process paired observations on the office Windows host. Original 5000-draw classifier, fixed5% threshold. Exploratory selection, confirmation, measured work interventions and separate diagnostics are labeled. No real upstream Java library was executed.

| Comparison | Stage | Change % | 95% interval % | Decision |
|---|---|---:|---|---|
| runtime_training_tier1 | exploratory | +13.58 | [+8.92, +19.62] | regression |
| runtime_training_interpreter | exploratory | +503.58 | [+480.08, +525.52] | regression |
| runtime_confirmation | confirmatory | +10.18 | [+6.46, +14.69] | regression |
| algorithm_resource_tradeoff | confirmatory | -97.48 | [-97.63, -97.27] | improvement |
| same_class_contention_mitigation | confirmatory | -59.06 | [-62.02, -56.43] | improvement |
| heterogeneous_core_policy | confirmatory | +12.62 | [+0.82, +35.14] | inconclusive |
| measured_extra_0_441 | measured calibration intervention; effect truth unknown | -6.17 | [-10.56, -1.34] | inconclusive |
| measured_extra_0p01_441 | measured calibration intervention; effect truth unknown | -3.41 | [-9.48, +2.09] | inconclusive |
| measured_extra_0p05_441 | measured calibration intervention; effect truth unknown | -2.47 | [-14.02, +5.06] | inconclusive |
| measured_extra_0p15_441 | measured calibration intervention; effect truth unknown | +2.11 | [-18.66, +17.97] | inconclusive |
| measured_extra_0p5_441 | measured calibration intervention; effect truth unknown | +45.86 | [+30.23, +62.02] | regression |
| measured_extra_0_442 | measured calibration intervention; effect truth unknown | -2.49 | [-8.78, +3.85] | inconclusive |
| measured_extra_0p01_442 | measured calibration intervention; effect truth unknown | -7.20 | [-40.72, +40.01] | inconclusive |
| measured_extra_0p05_442 | measured calibration intervention; effect truth unknown | -8.90 | [-17.16, +0.89] | inconclusive |
| measured_extra_0p15_442 | measured calibration intervention; effect truth unknown | +20.41 | [+9.57, +32.07] | regression |
| measured_extra_0p5_442 | measured calibration intervention; effect truth unknown | +53.85 | [+41.81, +63.50] | regression |
| measured_extra_0_443 | measured calibration intervention; effect truth unknown | -3.49 | [-16.41, +5.62] | inconclusive |
| measured_extra_0p01_443 | measured calibration intervention; effect truth unknown | +3.91 | [-1.14, +9.36] | inconclusive |
| measured_extra_0p05_443 | measured calibration intervention; effect truth unknown | -24.89 | [-46.92, +2.62] | inconclusive |
| measured_extra_0p15_443 | measured calibration intervention; effect truth unknown | -2.97 | [-31.51, +27.57] | inconclusive |
| measured_extra_0p5_443 | measured calibration intervention; effect truth unknown | +49.41 | [+38.59, +57.58] | regression |
| measured_improvement | confirmatory | -33.83 | [-37.43, -29.95] | improvement |

## Secondary resources and limits

secondary_metrics in reanalyzed.json retains per-arm CPU-time, allocated-byte and throughput means/min/max. CPU-time granularity can create zero/small samples. Per-thread allocation is not peak working set or total JVM allocation; management calls have observer cost. Throughput is the reciprocal time for this batch operation, not an independent application-level benefit. No customer SLA is available: the runtime decision uses a prespecified relative >5% improvement goal and observed CPU mean <=+10%.

Order-group changes, half-run drift and lag-one correlations are descriptive diagnostics, not proof of independent sampling or causal order effects. No multiple-comparison correction or general detector accuracy claim is made. Nominal extra-work fractions do not establish true timing effects. Inconclusive measured outcomes remain inconclusive.
