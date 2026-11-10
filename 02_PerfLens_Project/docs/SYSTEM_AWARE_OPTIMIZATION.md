# System-aware follow-up — 5 November 2026

5 November actual-library extension: tier1/default +880.92% [95% CI +853.77%, +919.10%], **regression**. Exact raw case: results\resume-interventions-20261105T191951Z\runtime. This is an exploratory same-artifact/input JMH comparison, separate from the earlier native held-out evaluator; no favorable configuration is forced. JFR and JVM logs now also cover actual Roaring code. Bytecode was examined; native machine-code/PGO/source generation remains unexecuted. See UPGRADE_RESULTS and NOISE_INVESTIGATION for diagnostics, uncertainty and limitations.

<!-- preserved-before-resume-20261105 -->

## Preserved earlier checkpoint (historical status)

# Bounded system-aware optimization

This upgrade evaluates configuration selection for an existing correct project-owned Java workload. It does not generate arbitrary source optimizations. Exact implementation: `upgrade/metrics.py`, `upgrade/study.py`, `upgrade/workloads/MetricsBench.java`; execution status and actual results are in UPGRADE_RESULTS and the native dataset's recommendation/analysis files.

## Three distinct approaches

**A compiler/runtime configuration:** implemented as an allowlist of default HotSpot, `-XX:TieredStopAtLevel=1` and `-Xint`. `permitted_jvm` refuses arbitrary names/agent flags. All configurations run the same compiled binary, sorted data, query trace, correctness oracle, timed-loop policy and recorded JDK. Java JIT may generate different machine code from the same bytecode; choosing a runtime setting is not rewriting source. A fixed warmup policy cannot prove steady state. Resource metrics expose whether faster wall time trades CPU/allocation for it.

**B system/workload-dependent generated code:** HotSpot compilation is an existing runtime code-generation mechanism observed through JFR compilation tiers and PrintCompilation. This upgrade records compilation diagnostics where executed, not disassembly. `hsdis`, native compilers, PGO, target-ISA generation and GraalVM have not been provisioned or evaluated. A bounded future specialization template could generate fixed-domain kernels but needs separate semantic equivalence and out-of-sample workload/hardware validation.

**C automatic source transformation:** not implemented. Previous BFS reuse and search algorithm replacement are manual, attributed source changes with known domain assumptions. They do not imply an unrestricted AI optimizer. Search over generated algorithms, safety proofs and application-wide transformation remain future research. Compiler flags, JIT-emitted code and source rewriting must never be conflated.

## Selection interface and fixed objective

Run `python -B upgrade/study.py --java PATH_TO_JDK21_JAVA`. The interface evaluates the permitted settings on MetricsBench and writes all configurations/raw observations/snapshots. It is a small workload-specific evaluator, not a universal autotuner. Existing PerfLens command configs remain the integration interface for other languages/workloads without changing the analyzer.

Training compares default against tier1 and interpreter, eight fresh-process pairs each, fixed seeds410/411. Select one candidate from exploratory effect estimates, then confirm once against default using10 new pairs/seed420. Fixed objective: confirmed internal-time interval entirely below-5%, correctness established, and observed mean process CPU no more than10% above reference. The CPU resource allowance is descriptive, not a confidence/SLA guarantee. Missing resource evidence must not pass the guard. If the criterion fails, retain default rather than forcing a new setting or repeatedly measuring until significance. No more aggressive setting is presumed better.

The same trusted source binary is hashed. Per-operation process CPU time includes JVM compiler/GC threads in the surrounding measurement window; per-thread allocated bytes do not measure whole-JVM allocation/peak memory. Throughput is the reciprocal timed operation rate, not an application saturation metric. An independent arithmetic membership oracle checks both algorithms before timing and the final timed checksum afterward.

Each timed invocation deterministically changes one query to a different known-present even value. Both settings/algorithms see the same trace and the expected membership count remains unchanged. This avoids making every operation invariant; the small trace-update cost is included consistently. This is still a custom demonstrator, not a substitute for the separately prepared JMH real-library study.

One MetricsBench operation is a batch of2000 membership queries over20000 sorted integers, plus the trace update. Reported operations/second refers to these batches, not individual membership queries. The5% goal retains the project's existing practical tolerance; the10% CPU allowance is an analyst-selected lab resource ceiling fixed before measurement, not an externally supplied application requirement.

## Hardware/system awareness

Read-only GetSystemCpuSetInformation records logical/group/core/cache/efficiency-class relationships. On heterogeneous Windows CPUs, higher efficiency-class values describe faster but less efficient processors; that is not a frequency measurement. The same-class placement intervention avoids changing the reported class while moving the workload away from a loaded core. A separate cross-class policy comparison makes that changed factor explicit. Frequency/context-switch probes are coarse/system-wide supporting records and do not establish causality or temperature. No power plan or services are modified.

Primary API reference: [Windows CPU-set information](https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-system_cpu_set_information). Source-pinned methodological literature is in RESEARCH_METHODS_AND_EVIDENCE.

## Diagnostic boundaries and portability

`python -B upgrade/diagnose.py --java PATH` runs separate instrumented Java invocations with JFR, JIT compilation output, GC/safepoint logs and a latency trace. The recording profile disables environment-variable/system-property/system-process events to avoid collecting unrelated sensitive settings. Compilation threshold is lowered for visibility; this changes diagnostic overhead. Do not mix those durations with clean timing or infer speedups from unequal-duration raw event counts. Retained raw latency nanoseconds allow quantile reanalysis but remain correlated inner-process observations.

Native execution needs full JDK21, including `javac` and `jfr`, plus the locked Python environment. Windows CPU classes are supported only by the native API; other platforms explicitly report unsupported. Linux cleanup execution is pending a working isolated environment. The real Roaring/JMH case is independently blocked by Docker and is not substituted by this trusted synthetic search experiment.
