# Fixed evaluation plan

Recorded before running the new evaluation suite on 29 October 2026. This is an engineering protocol, not a formal preregistration. The recovered original NetworkX run was already reproduced; its results do not determine acceptance of new outcomes.

## Scope and acceptance

The official research question is: How can software performance be measured reliably, and which optimization techniques provide reproducible improvements?

Preserve the original code and statistics. Extend its process rather than replacing it. Working experiments and a reproducible reviewer package come first. No new seminar paper or presentation in this stage. Local files are the task tracker. The user's deadline is next week; an exact calendar submission date has not been supplied.

The public interfaces tested are the existing compare/analyze functions, the new external-command runner and its output protocol, and workload correctness. These checks implement the correctness and fixture requirements already authorized by the user. Test results and source snapshots belong in the package.

## Design

Each named experiment has exactly two arms, 20 paired rounds, random within-round order, and one fresh process per observation. Session 1 seed is 1730, session 2 seed is 1731. All nine comparisons run in session 1; all except scaling run again in session 2. These are same-host repeatability sessions, not independent-machine reproducibility. No adaptive stopping or rerunning to obtain significance. Failed runs are retained and diagnosed.

Twenty pairs are a modest fixed budget inherited from the prototype, not a power calculation. Intervals may be too wide. Inconclusive results remain inconclusive. The first session is the initial evaluation; the second is a held-out confirmation using a different execution-order seed and fresh processes. The second is run regardless of the first session's outcome. Nothing is tuned between sessions.

Primary method is the original 5000-resample paired percentile bootstrap of relative mean change. The entire interval must exceed +5% for regression or fall below -5% for improvement. An interval entirely inside [-5%,5%] is within_threshold; other intervals are inconclusive. The 5% practical threshold is selected in advance, not estimated from observations. Minimum/point-only comparisons will be shown descriptively, not adopted as inference.

One reported observation is the average of timed calls inside one process; loops are not independent samples. Imports, workload preparation, warmups and correctness checks are outside the internal timer. Also retain whole-process wall time, which includes runtime startup, wrappers and setup. Never equate it with kernel time. CPU-affinity wrappers add process overhead outside the internal timer.

## Workloads and interventions

| Comparison | Reference -> candidate | Interpretation |
|---|---|---|
| control | Repeated NetworkX BFS -> identical workload | Unchanged-code negative control |
| injection | One BFS per query -> two BFS calls per query | Deliberate redundant computation; known slowdown, not a historical bug |
| python_optimization | One BFS per same-source target -> one BFS reused across targets | Remove redundant work; validate every requested grid distance against x+y |
| python_scaling | Same optimization on a 60x60 rather than 35x35 grid | One extra input size; not broad application generalization |
| cpu_contention | Quiet pinned workload -> load on same logical CPU | Controlled scheduling contention, fixed affinity in both arms |
| cpu_mitigation | Load on same CPU -> workload on another CPU with original load retained | CPU placement mitigation; physical-core/SMT topology not proven |
| java_optimization | Linear membership search -> binary search | Algorithmic optimization on already sorted data; preparation excluded |
| java_warmup | No untimed calls -> 20 untimed calls | Initialization/JIT warmup policy sensitivity; retain all warmup traces, do not assume steady state |
| java_runtime | -Xint -> default JVM | Runtime mode sensitivity for the identical binary-search workload |

Python defaults: 16 same-source queries, 5 timed batches, 3 warmups. Graph is immutable during each operation; no cache persists between operations. Baseline and optimized implementations return the same list, not only a scalar checksum. New NetworkX experiments use the recovered checked-out source revision after the original runner restores its HEAD.

Java defaults: 20,000 sorted even integers, 2,000 deterministic mixed present/absent membership queries, 5 timed loops. Independent arithmetic membership oracle checks the result. A volatile sink consumes results. Search preparation is excluded; binary search is justified only where data are already sorted or sorting is amortized. Baseline linear search has 5 warmups; the warmup/runtime studies use binary search with 0 or 20 as specified. This small standalone harness is not JMH and does not establish steady-state JVM performance.

CPU intervention uses one bounded-lifetime busy worker on logical CPU 2, with a readiness handshake. Pin the measured process to 2 (contention) or 4 (mitigation). Verify these CPUs are permitted before starting. Do not disable user services, change power plans or alter system settings. Measurements on a shared interactive desktop retain uncontrolled noise.

## No-regression decision

A 3 ms mean-per-operation demonstration target is specified for graph comparisons before timing. It is a project-selected illustrative budget, not a user/application SLA. Even an unchanged-code control can miss it. If so, profile and investigate the redundant BFS work, then test reuse. Target status is descriptive observed mean, separate from uncertainty-aware relative classification and not a tail-latency guarantee. Retain baseline if no worthwhile improvement is established.

## Reporting and limits

Save all raw data, exact commands, configuration, stdout payloads, JVM warmup traces, versions, timestamps, hashes and source snapshots. Compare means, uncertainty and CV; measure both bias/duration and variability rather than promising noise always increases variance. Report whether each mitigation worked for this case. Summarize two control/injection outcomes with exact binomial uncertainty, while emphasizing two runs are far too few to establish general detector sensitivity/specificity. Four-outcome deterministic fixtures are labeled synthetic tests, never measured performance.

Do not pool warmup iterations as fresh-process observations. No multiple-comparison correction; findings are workload-specific exploratory comparisons with a preplanned confirmation. Bootstrap assumes adequately independent rounds; autocorrelation and drift remain possible. No thermal/frequency counters, allocation profiling or memory equivalence proof. No universal optimization ranking.
