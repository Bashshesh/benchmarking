# PerfLens research continuation — verified 5 November 2026

## Final PR845 experiments · 6 November 2026

The two final experiments extend the verified `c776a52` checkpoint. Both compare
`2dfd0fb994468c8d416dea3d217dc40ca7d6d145` with
`684531c13877fbdacccf02262b32e6faf889d76f`. The results and inputs from earlier
work are referenced through the existing evidence index. New evidence is in
[`results/final-roaring-20261105T225902Z`](../results/final-roaring-20261105T225902Z/).

### First-call lazy cardinality in Docker/WSL

| State | Before → after (mean ns/rank) | Paired change [95% CI] | ±5% decision |
|---|---:|---:|---|
| Precomputed | 964.04 → 8.74 | -99.09% [-99.43%, -98.43%] | improvement |
| First invalid (-1) | 857.01 → 714.60 | -16.62% [-38.14%, +8.92%] | inconclusive |
| Next call after priming | 660.44 → 8.42 | -98.73% [-98.99%, -98.37%] | improvement |

| Within-revision contrast | Reference → candidate (ns/rank) | Paired change [95% CI] |
|---|---:|---:|
| Before, first / precomputed | 964.04 → 857.01 | -11.10% [-32.61%, +12.99%] |
| Before, next / first | 857.01 → 660.44 | -22.94% [-45.25%, +2.16%] |
| Before, next / precomputed | 964.04 → 660.44 | -31.49% [-52.23%, +1.50%] |
| After, first / precomputed | 8.74 → 714.60 | +8074.23% [+5437.53%, +10990.31%] |
| After, next / first | 714.60 → 8.42 | -98.82% [-99.13%, -98.43%] |
| After, next / precomputed | 8.74 → 8.42 | -3.70% [-40.44%, +57.85%] |

The before revision scans and returns the independent membership count on both calls, leaving
cardinality at -1. The after revision repairs the field on the first call and reads the
stored value on the next call. Each of the 16 bitmaps passed an independent count oracle,
and all three 256-operation batches produced checksum 8396800 on both revisions. Iteration
setup and teardown checked field state. The measured call sequence traversed a fresh batch
once. An untimed priming call per object established the repeat condition.

JMH 1.37 SingleShotTime uses one timed batch per shot and normalizes by 256 operations.
Every shot constructs distinct BitmapContainer objects outside timing. The 16 backing arrays
are reused, so the test measures logical invalidation with reused input data. It does not
measure cold memory or a cold JVM. The matching precomputed scenario controls for driver
and batch timing costs. Its absolute time is specific to this design and differs from the
original continuous AverageTime harness. Each fork had 16,000 untimed batch preheat calls,
30 warmup shots and 20 measured shots. No timer estimate was subtracted.

The pilot in `results/final-roaring-20261105T225535Z` stopped before the planned pairs were complete. The short
shot-only warmup invoked the batch driver only 50 times and cached shots were unstable.
The main design adds the same fixed driver preheat to all arms. Pilot measurements and
source are retained separately and excluded from the paired estimates.

Each experiment uses ten randomized blocks. For every workload, each block contributes
one independent JVM fork per revision. Bootstrap intervals use 5,000 resamples of whole
pairs, preserving within-fork dependence. The intervals are marginal and conditional on
this machine and run. Short shots, warmup, JVM compilation, shared-host activity and
cache locality can still affect estimates. The within-revision contrasts are descriptive
and unadjusted for multiple comparisons.

### Native Windows reproduction

| Core workload | Native before → after (mean ns/op) | Windows paired change [95% CI] | Earlier Docker/WSL paired change [95% CI] |
|---|---:|---:|---:|
| rank(65535) | 607.19 → 2.78 | -99.54% [-99.56%, -99.52%] | -99.49% [-99.50%, -99.48%] |
| rank(65534) | 614.71 → 648.20 | +5.45% [+0.13%, +12.69%] | +0.70% [-0.93%, +2.58%] |
| fullContainerRange | 615.03 → 12.47 | -97.97% [-98.02%, -97.92%] | -97.85% [-97.90%, -97.81%] |

Native Windows ran on Intel(R) Core(TM) Ultra 7 155H with 16 physical cores and
22 logical processors, 15.37 GiB
usable memory and Windows-11-10.0.26200-SP0. Native JVM details and executable hash are in
`windows-native/jvm.json` and `windows-native/environment.json`. Docker/WSL used
Temurin 21.0.7 while Windows used Oracle HotSpot 21.0.8. Both used the frozen workload,
JMH 1.37, a 512 MiB fixed heap, one thread and one fork per invocation, 3 × 200 ms warmup
and 3 × 300 ms measurement. CPU allocation, OS scheduling, JDK distribution and the
security policy differ across environments.

The Docker builds revalidated the pinned sources and the archived target class hashes.
The native launcher verified all artifact hashes before and after execution. Native
correctness checks returned checksum 458211 on both revisions. The Java 21 code-source
policy denied all eight permission probes in the ungranted code domain. The first attempt
passed the checks but the host sandbox refused the JMH fork's loopback connect before timing.
The receipt is in `windows-native-ipc-denied`. The retry used a scoped approval for native
execution with a Docker-built guard that restricts Java socket permissions to IPv4 loopback,
the exclusive code-source policy, a minimal environment and a Windows job for cleanup.
Both permission gates passed before timing. The JMH build and harness stayed the same.
The restriction design is specific to the reviewed, pinned artifacts and this JDK 21 setup.

The large improvements have the same direction in both environments. The Windows
estimates are about 0.05 and 0.12 percentage points larger for MAX rank and the range
query, respectively. The Windows near-MAX control is inconclusive at the 5% practical
threshold. Its interval spans effects from +0.13% to +12.69%, while the prior Docker
interval falls inside ±5%. Both estimates are from the same physical machine, and
Windows, JDK, scheduling and isolation effects are confounded.

The final verification recalculated all 120 fork scores and paired estimates directly
from the raw JMH JSON and matched the saved CSVs and summaries. Twelve selected
analysis, capture and process-cleanup tests passed. The evidence manifest covers the
completed runs, partial pilot and initial IPC denial.

---

Current branch: `upgrade/full-research-20261104`. All source/history/archives/attribution and earlier home/native-office measurements are preserved. Part 2 paper/presentation remains out of scope. This is Codex-assisted technical research, not independent human peer review.

The previously blocked **bounded five-priority research continuation is now executed**, subject to the limitations below. This does not claim production representativeness, universal detector calibration or complete generalization of the original broad research agenda. Docker/WSL2 is a separate execution environment on the same physical office machine; none of its observations are pooled with native Windows/home data.

## Updated six-priority status

| Priority | Implemented and tested | Actual result | Evidence and remaining limitation |
|---|---|---|---|
|Real optimization/root cause|Both actual library sources compiled; independent oracle, upstream Gradle tests, frozen JMH, JFR, bytecode and private guard ablation executed|MAX rank and public boundary query improve; near-MAX control and ablation localize the mechanism|Java dossier below; base Java8 source artifact, small fork counts, not end-to-end application performance|
|Noise diagnosis/mitigation|Native same-class study retained; new virtual-CPU shared contention/moved-load comparisons with cgroup counters|Report all mean/CV outcomes below, including uncertainty|Virtual affinity does not identify physical hybrid core class; quota/cache/JIT/scheduling remain confounders|
|System-aware optimization|Native default/tier1/interpreter selection retained; actual-library default/tier1 comparison executed|No setting is automatically preferred; decisions below|JIT runtime configuration and bytecode evidence, not native O2/O3/PGO or source generation|
|Detector evaluation|Original classifier/rules unchanged; previous 540 synthetic datasets/3-seed measured work studies retained; real negative control and small Linux controls inspected|Coverage and inconclusive/false directional outcomes retained|No broad real-world accuracy percentage; tiny integration timings unsuitable for confirmatory inference|
|Cross-language/portability|Linux success-parent descendant leak reproduced and fixed; timeout/pipe/failure/build/config/result/analysis checks executed|29 native tests and 29 Linux tests; upstream 193/195 tests|POSIX groups can be escaped by deliberate new sessions; init reaps orphans, containment is not a sandbox|
|Targets/additional metrics|Prior CPU/allocation/throughput study and fixed >5% target preserved; real JMH time plus derived rate|Resource and performance trade-offs remain workload-specific|No production SLA/peak-memory/energy claim; reciprocal mean-time rate is not independently measured throughput|

## Real Java case and completed execution

RoaringBitmap PR #845 / Daniel Lemire: before `2dfd0fb994468c8d416dea3d217dc40ca7d6d145`; after `684531c13877fbdacccf02262b32e6faf889d76f`. GitHub PR/sole-parent metadata were reverified and a secrets-free container clone independently checked the object relationship. No upstream changes or external publication occurred.

The original paired JMH run was **not repeated after the usage interruption**. Both original builds/oracles/pilots remain authoritative. New work: four JFR diagnostic records, private ablation, real-source input, virtual-affinity/noise/runtime interventions, Linux validation and two additional compatibility pilots. A successful original Gradle `TestRank*` run executed 193 tests before and 195 after, zero failures/errors/skips. JMH uses declared direct `javac --release 8` base sources, whereas upstream Gradle checks its normal modular build; do not call the measured artifact a published multi-release JAR.

| Comparison | Pairs | Reference → candidate mean ns/op | Candidate/reference mean time change |
|---|---:|---:|---|
|rank-65535|10|342.61 → 1.75|-99.49% [95% CI -99.50%, -99.48%], **improvement**|
|rank-65534|10|348.63 → 351.07|+0.70% [95% CI -0.93%, +2.58%], **within_threshold**|
|fullContainerRange-65535|10|366.36 → 7.86|-97.85% [95% CI -97.90%, -97.81%], **improvement**|
|guard-ablation|8|651.10 → 3.64|-99.44% [95% CI -99.52%, -99.35%], **improvement**|
|corpus-boundary|8|524.76 → 11.20|-97.87% [95% CI -98.02%, -97.68%], **improvement**|
|corpus-near-boundary|8|422.70 → 407.75|-3.54% [95% CI -7.18%, +0.12%], **inconclusive**|
|contention|8|439.72 → 826.45|+87.95% [95% CI +66.76%, +113.19%], **regression**|
|mitigation|8|750.78 → 385.79|-48.61% [95% CI -50.98%, -46.03%], **improvement**|
|runtime|8|353.70 → 3469.50|+880.92% [95% CI +853.77%, +919.10%], **regression**|

There are **9 completed comparisons / 156 fresh JMH-fork observations**, with 3 iterations retained inside each fork. The original pair has 10 rounds/case; extensions have 8. Original rules use paired 5000-resample percentile bootstrap, fixed ±5% practical thresholds and fixed seeds. The small samples, possible serial dependence and no familywise correction limit certainty. Reanalysis reports order-group means, half-run drift, lag-one descriptions and exploratory circular length-2 block-bootstrap sensitivity without changing decisions.

## Mechanism and source hypothesis tested

Before, `BitmapContainer.rank(MAX)` scans all 1024 words using bit counts. After, it returns cached cardinality; an invalid lazy cardinality still needs repair. MAX-1 retains scanning. Public `rangeCardinality` with a container-boundary end exercises MAX internally. The frozen real-library harness consumes returned results and uses different containers. The upstream lazy-cardinality test passed; **first-lazy-call performance was not measured**.

The private ablation removes only the MAX guard from the after-revision BitmapContainer, recompiles that class inside Docker and passes the same independent oracle. The comparison in the table is intact optimized after / guard-removed after. Returning the large cost when the guard is removed, together with boundary controls, bytecode and JFR evidence, supports a bounded code-mechanism explanation. It does not identify every hardware/JIT contributor or estimate application-wide benefit. JFR sample counts depend on inlining, operation counts and duration; raw sample-count ratios are not speedups. There is no claimed native machine-code disassembly.

The PR claims a cached-cardinality shortcut, not a fixed numerical speedup. These data agree with that mechanism for the tested cached dense case and public range caller. No claim of O(1) lazy repair or universal acceleration of all container/query types follows. See [PR845](https://github.com/RoaringBitmap/RoaringBitmap/pull/845) and `docs/research/ROARING845_VERIFIED.json`.

## Application-derived input and permission outcome

Frozen input: 1428579 bytes, SHA-256 `8d3135f4ecab2eab64021b2c5aee31abdedd345a02653076ccac440619a014cf`. It concatenates sorted main Java sources from the **before** revision, indexes unsigned bytes >32, and uses identical bytes in both arms. Per-file hashes and Apache-2.0 license are retained in `results/resume-corpus-20261105T005256Z`. Full-block correctness was checked in trial setup; the supplemental full/near-boundary oracle checked 44 cases on both revisions with checksum 2112424. This is a real source-text indexing proxy, not a production bitmap query trace.

`real-roaring-datasets` was investigated again: GitHub license metadata is null, LICENSE returns404, README credits third-party inputs without a clear grant. Earlier documentation's statement that this dataset repository has an Apache license was incorrect and is explicitly corrected in `docs/research/DATASET_PERMISSION_CHECK_20261105.md`. The library's Apache license does not license that separate corpus. No such dataset was downloaded/used. Real-source input supports only limited input generalization; query boundaries were deliberately selected, not sampled from a real workload distribution.

## Noise, runtime and detector interpretation

Contention: +87.95% [95% CI +66.76%, +113.19%], **regression**. Moving the same busy loop to another allowed virtual CPU: -48.61% [95% CI -50.98%, -46.03%], **improvement**. Mitigation CV ratio's exploratory 95% interval is [0.693, 1.886]; interpret this separately from the mean-time result. Cgroup v1 CPU/quota counters for the completed mitigation and within-fork variation are in verification.json. The earlier contention run has valid timings but the v2 counter path was unavailable. No physical-core class, frequency/thermal or cache mechanism is isolated by virtual CPU placement. Native hybrid-core evidence remains in the prior dataset.

Actual library runtime setting: candidate tier1 / default is +880.92% [95% CI +853.77%, +919.10%], **regression**. A separate matched rank(65534) tier1 diagnostic recorded level1 via PrintCompilation, while the default diagnostic reached level4. The profiler event threshold can omit short compilation events; the text log confirms the tier independently. No native assembly was captured, so the slowdown cannot be assigned to a specific instruction or compiler pass. This is a fixed exploratory configuration comparison, not a held-out tuning recommendation. The earlier native selection/confirmation retained default after tier1 slowed it; it is not replaced or pooled. JIT configuration changes code generation, but automatic source rewriting/PGO/Graal/native compiler optimization remains future work.

Separate JFR records (not clean timing replicates):

|Run|Execution samples|Rank stack frames|Rank compilation tiers/counts|GC events|
|---|---:|---:|---|---:|
|rank-2dfd0fb99446-65534|288|283|{}|1|
|rank-2dfd0fb99446-65534-tier1|114|112|{}|1|
|rank-2dfd0fb99446-65535|282|276|{}|1|
|rank-684531c13877-65534|283|282|{}|1|
|rank-684531c13877-65535|107|72|{}|1|

Counts reflect the instrumented workload and inlining; do not compare them as elapsed-time effects.

Detector: existing synthetic truth-model sensitivity, finite-cell coverage83.3–100% with30 datasets/cell and inconclusive counts remain unchanged and separately labeled. Existing real extra-work fractions are not guaranteed timing-effect labels. The original JMH near-MAX control stays within threshold. A 5-pair **identical-code** Java Linux functional smoke initially flagged improvement, while the after-fix smoke was inconclusive. This is a preserved false directional outcome under a tiny/noisy batch, not a useful optimization or evidence of high classifier accuracy. Python constant-time payloads are protocol fixtures, not measurements. No threshold was tuned to hide these outcomes.

## Failure and interruption audit

- The usage interruption did not cancel the completed primary benchmarks. The last inspection exit1 came from querying a then-absent diagnostic log, not Java failure. Upstream Gradle and JFR commands subsequently completed successfully.
- First source extraction failed Windows path length; a shorter cache preserved all failed inputs and enabled the independent builds.
- Initial JMH console capture used Windows cp949 and lost some text fields on Unicode, despite returncode0 and valid retained JMH JSON. Exact affected receipt counts are in validation; future capture explicitly uses UTF-8 with a regression test. The original JSON data and summaries passed reanalysis.
- First ablation stopped at a Docker CLI watchdog after JMH emitted results but successful container exit was not established. Its partial observations/logs are preserved and excluded from confirmatory summaries. A fresh complete ablation used identical measurement settings and a longer command watchdog; this was an infrastructure retry, not significance-driven sampling.
- First mitigation stopped at a similar CLI watchdog after an extended host time gap. Its incomplete pairs remain excluded; the earlier complete contention case was not repeated. The retry used the same timing design, added cgroup v1 path detection and waited for the load worker to exit. This is separately timestamped; the exact reason the CLI ceased responding is not established. The failed invocation's console output is retained, but its unconfirmed scratch JMH JSON was not archived before reuse of that cache filename. The successful pair JSON files are intact. Future invocations use run-specific scratch names and save any unconfirmed JSON separately.
- Linux before-fix unittest actually failed on a live descendant after a successful parent. POSIX normal completion now kills the owned process group, just as failure already did. The same strengthened test passes. The old validation wrapper returned0 despite a failed unittest receipt; it now propagates failed test status. Old logs are unchanged.

## Preservation, reproduction and remaining limitations

All previous historical/native-office evidence remains separate. The unchanged statistical analyzer is reused. Three deliberately versioned original-checkpoint files now differ: process_control.py, tests/test_runner.py (prior bounded Windows fix) and perflens.py (new POSIX success cleanup). The preservation report verifies all other541 checkpoint entries, all1116 archived originals and exact original bytes for these three files. All18 installed skills and sanitized/original skill snapshots are unchanged. No paper, slides or new transfer ZIP was made.

Four nearby pinned source revisions pass the same external correctness/JMH pilot. This is not broad release/JDK compatibility. Current constraints include Docker/WSL virtualization and 2CPU quota; a shared interactive host; no physical CPU frequency/thermal/PMU control; short fixed warmup with no steady-state proof; limited dataset representativeness; base-source measured artifacts; small fork counts and incomplete independent-host replication; no universal detector accuracy or production SLA. Native compiler/PGO/C++ support is optional future work, not claimed executed.

Use `docs/REPRODUCIBILITY_UPGRADE.md` and `upgrade/java/REPRODUCE.md`. Current raw/graph/test/diagnostic paths are in `docs/UPGRADE_EVIDENCE_INDEX.json` under resume_20261105. Reanalysis entry: `upgrade/resume_analyze.py`. Original source commits, raw iteration hierarchy, image IDs, commands, source/input hashes and failure receipts are preserved. Recreate environments rather than moving virtual environments or pretending the old Downloads ZIP contains this continuation.


<!-- preserved-before-resume-20261105 -->

## Preserved earlier checkpoint (historical status)

# PerfLens upgrade results and remaining gates

**The complete requested upgrade is not claimed finished.** The permitted native engineering/experiments and stored-data validation are complete. Docker is unavailable, confirmed by the user; actual third-party Java builds, compatibility pilots, real-repository optimization/JFR and Linux-container tests remain unexecuted. No untrusted repository code ran on the Windows host. No updated seminar paper or presentation was created.

Branch `upgrade/full-research-20261104`; preserved starting checkpoint `111accf`. Original analyzer, historical measurements, archives and contributor attribution remain intact. Two original-checkpoint source/test files were intentionally versioned for cleanup reliability; their exact pre-upgrade bytes are retained in the preservation ZIP. This is a technical Codex-assisted research/engineering record, not student-authored peer feedback.

## Six improvement priorities

| Priority | Implemented | Tested/executed | Actual result and evidence | Remaining limitation |
|---|---|---|---|---|
|1 Real regression root cause|Prepared external actual-library JMH harness and independent oracle; source investigation complete|Real builds/pilots/timing/profiling NOT EXECUTED|Provisional Roaring845 exact pair and cached-rank hypothesis; docs/JAVA_COMMIT_SELECTION.md and upgrade/java/|Isolation unavailable; no experimentally validated primary or real-case reproduction claim|
|2 Noise diagnosis/mitigation|CPU-class/core/cache topology, same-class load placement, system probes, separate JFR/JIT/GC and latency traces|Native and original baseline executed|-59.06% [95% CI -62.02%, -56.43%], `improvement`; results/upgrade-native-20261104T203656Z/analysis/ and results/upgrade-diagnostics-20261104T215420Z/|Shared interactive host, correlated rounds, coarse frequency/context observations; no thermal/PMU or proven steady state|
|3 Compiler/code generation|A: allowlisted runtime evaluator with separate selection/confirmation; B: JIT diagnostics only; C: no automatic rewriting|3 runtime settings and held-out confirmation executed|Default retained; tier1 confirmation +10.18% [95% CI +6.46%, +14.69%], `regression`; recommendation.json|No native O2/O3/PGO/GraalVM/disassembly or automatic source generator; workload-specific only|
|4 Detector calibration|Unchanged original classifier; synthetic operating characteristics and measured work interventions|540 generated 20-pair datasets, 30/cell,18cells; 16 measured intervention comparisons|results/upgrade-synthetic-20261104T215548Z/RESULTS.md, summary.json and raw data; every classification independently reproduced|Synthetic lognormal model only; real work fractions are not guaranteed timing labels, small measured runs not general accuracy|
|5 Cross-language/portability|Python/Java command protocol, declarative build receipts, timeout/failure tests, bounded Windows jobs, single-fork JMH adapter|28 tests pass; Java build/run adapter smoke 10 processes; native Python/Java studies|tests/ and results/upgrade-adapter-20261104T204540Z/; failed cleanup/guard tests retained before fixes|Linux/zombie reaping not executed; process groups/jobs are not a security sandbox; no C++ compiler experiment|
|6 Targets/additional metrics|Prespecified relative improvement goal and CPU ceiling, CPU/allocation/throughput, diagnostic tails|Resource algorithm comparison and raw latency trace executed|Algorithm internal time -97.48% [95% CI -97.63%, -97.27%], `improvement`; CPU-time effect -97.24% [95% CI -97.43%, -97.01%]|No customer SLA, peak RSS/retained heap/energy or application impact; per-thread allocation scope and CPU granularity limits|

## Exact execution inventory

- Unchanged 17-case baseline: 680 fresh-process observations, original 20 pairs/seeds/configurations, results/upgrade-office-20261104T201220Z/baseline/. Correctness preflight passed after recorded cleanup-test repair.
- Native additions: 22 comparisons, 278 fresh-process observations: training/confirmation, algorithm resources, same-class mitigation, heterogeneous-class policy,15 extra-work cases over3 seeds and one removed-work improvement. All outcomes retained in results/upgrade-native-20261104T203656Z/.
- Declarative Java adapter: build receipts, source hashes and5paired smoke rounds (10 processes), results/upgrade-adapter-20261104T204540Z/. Functional integration evidence, not a separate confirmatory research finding.
- Instrumented diagnostics:3 project-owned Java/JFR runs plus one 2000-operation latency trace, results/upgrade-diagnostics-20261104T215420Z/. Durations are not pooled with clean timing. First JFR startup failed sandbox temporary-repository permission; unchanged workload retry succeeded with approved access and a new result directory.
- Synthetic model: 540 independent generated datasets, 10800 paired rows, separate generation/bootstrap seeds; results/upgrade-synthetic-20261104T215548Z/. These are NOT hardware measurements.
- Tests: 5 original + 23 extension = 28 pass; logs in results/upgrade-office-20261104T201220Z/final-*-tests.txt. First baseline preflight and missing-resource recommendation failure are retained, and occurred before their relevant timing studies.

## Repositories and datasets

Provisional primary RoaringBitmap PR845: before `2dfd0fb994468c8d416dea3d217dc40ca7d6d145`, after `684531c13877fbdacccf02262b32e6faf889d76f`. Exact parents, requested840/845/Caffeine1320, Fory and C1–C10 screening are documented. All build/pilot success rates and setup costs remain unmeasured; shared isolation failure is not a software build failure. No second Java repository is added before primary validation.

No real or published input dataset was used. Existing NetworkX grids, sorted membership queries, native redundant-work fixtures and the JMH prepared bitmaps are generated inputs. real-roaring-datasets provenance was inspected, but dataset-specific third-party license permissions remain unresolved. Published study results are separately labeled in RESEARCH_METHODS_AND_EVIDENCE and are not local observations.

## Root-cause evidence and uncertainty

For the local search example, source uses linear scanning versus binary search on already sorted data. Clean time and CPU evidence support this workload-specific reduction; JFR execution samples and compilation records provide independent diagnostic context. They do not measure sorting cost, memory-system causality or application impact. Native frequency/context-switch readings are supporting system-wide probes, not per-workload causal estimates.

Same-class mitigation improves measured time while keeping reported efficiency class fixed; core, cache, SMT/frequency and background OS activity can still differ. The separate heterogeneous policy result is +12.62% [95% CI +0.82%, +35.14%], `inconclusive`. Do not relabel its practical inconclusive outcome as a confirmed >5% slowdown. Order groups, half-run drift and lag-one correlations are descriptive, not independence proofs.

The real845 mechanism is a SOURCE HYPOTHESIS: cached cardinality at MAX avoids a1024-word scan, while first lazy-cardinality repair still scans. rank(MAX-1) and public range-cardinality controls are prepared. No local before/after library data or profiler evidence exists, so no reproduced speedup, root-cause isolation, agreement with the PR or causal claim is made.

## Resources and runtime result

MetricsBench operation means one batch of2000 membership queries over20000 sorted integers, with a deterministic known-present query update. Throughput uses these batches. Secondary summaries and CPU uncertainty are in native analysis/reanalyzed.json. Per-thread allocated bytes are not peak/retained memory; zero values cannot establish memory equivalence. CPU time includes JVM background/compiler threads and can be coarse.

The evaluator did not force an optimization: {"selected": "default", "reason": "no confirmed practically relevant improvement"}. The new goal (>5% confirmed elapsed improvement with observed CPU mean <=+10%) is an analyst-selected lab objective, not an externally supplied SLA. The old3ms graph target remains an illustrative historical target only.

## Independent validation and reproduction

Every baseline CSV/JSONL/source snapshot and summary passed cross-checks. Native primary/secondary/dependence summaries were independently re-read and reproduced; all540 synthetic classifications and counts/coverage matched reanalysis. Five historical saved analyses exactly reproduced in results/upgrade-validation-20261104T221156Z/original-audit.json. The preservation report verifies542 unchanged checkpoint files,2 declared versioned changes, and1116 original archive entries. All old raw evidence and attribution are preserved.

See docs/REPRODUCIBILITY_UPGRADE.md for sequential setup/test/run/reanalysis commands and upgrade/java/REPRODUCE.md for the BLOCKED isolated real-case route. Transfer the current working project and archive/misc.zip together (or seed with the old complete transfer and overlay the new branch); a Git clone alone may omit ignored archived inputs. Reinstall local environments/JDK. Keep each physical host/execution environment separate. Do not use the older transfer ZIP as if it contained this upgrade.

Reanalyzed figures: baseline/analysis/effects.png, native/analysis/effects.png, synthetic/synthetic-operating-characteristics.png. Raw paths and all status locations are indexed in docs/UPGRADE_EVIDENCE_INDEX.json. Validation source: office/finalize_upgrade.py and upgrade/analyze_evidence.py.


## Calibration and resource interpretation

For true +10% synthetic mean change, regression flags were 30/30, 23/30 and 7/30 at residual CV1%,5%,20%; the high-noise cell retained 23/30 inconclusive outcomes. True +30% changes flagged30/30 in each tested cell. These finite model results do not establish hardware/software detection accuracy.

Zero-effect cells produced no regression flags, but the20% noise cell had one false improvement and29/30 inconclusive outcomes. Thus zero regression flags is not perfect four-class accuracy. Empirical inclusion of the known population effect in nominal95% intervals ranged 83.3%–100.0% across cells (30 datasets/cell). This does not prove95% coverage; no threshold/rule was changed to hide it. Exact flag-rate intervals and decisive false-negative/true-negative counts remain in summary.json; inconclusive results are separate.

The same-class mitigation's exploratory candidate/reference CV-ratio interval was [0.0075, 0.0578], below one in this run, alongside its mean-time reduction. This conditional10-pair result does not make variance reduction universal or isolate frequency/cache effects.

The algorithm resource comparison observed mean per-thread allocation0.160 versus0.456 bytes/batch (linear versus binary). These tiny window readings include observer/runtime effects and are not evidence of a meaningful algorithmic memory regression or peak-memory equivalence. Observed mean CPU time was11.178ms versus0.309ms/batch; the paired CPU interval is reported above. Mean per-process batch throughput was80.5 versus3171.2 batches/s; do not interpret it as request-level service throughput.

JFR found SearchBench.search in512/515 linear execution samples and310/311 binary samples. Default runs recorded search compilation through tier4; the tier1-limited run recorded tier1 only. This verifies runtime/compiler behavior and hot-path involvement, not disassembly or isolation of every timing cause. No GC events were captured in these short configured records; absence of captured events does not establish general GC irrelevance.

All full-range and work-intervention-only effect figures were visually checked. The separate work-intervention view avoids compressing near-threshold cases beside the large interpreter slowdown. Both views retain their full selected-by-study-type data; no result was discarded.
## What remains

A working isolated execution environment is still required to accept the primary repository, build3–5 revisions, execute the real commit pair/JMH/JFR, and run Linux cleanup tests. Real corpus permissions/representative application evaluation, native compiler/PGO/code generation, trustworthy thermal/PMU/peak-memory/energy studies, full hierarchical/change-point analysis and independent human review remain incomplete. No calibrated real-world detector accuracy, universal optimization ranking or completed full project is claimed. Part2 remains out of scope.
