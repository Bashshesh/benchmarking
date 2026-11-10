# PerfLens — Software Performance Measurement and Optimization

PerfLens is a small research project for Advanced Software Engineering, Topic 9. It extends the previous group's NetworkX/NumPy prototype instead of replacing it.

**Research question:** How can software performance be measured reliably, and which optimization techniques provide reproducible improvements?

The project follows this process:

**Measure → check reliability → classify change → assess targets → diagnose → optimize → verify.**

No regression does not automatically mean acceptable performance. PerfLens also checks an absolute operation-time budget and investigates unnecessary work even when code has not changed.

## What is included

- The original Python benchmark runner, graph workload and paired statistical classifier.
- A configurable external-command runner for Python, Java or another executable that follows a small JSON output contract.
- Controlled CPU-contention and JVM-warmup investigations, including mitigation comparisons.
- An unchanged-code control and deliberate redundant-computation slowdown.
- A correctness-checked NetworkX optimization: reuse one breadth-first search for multiple targets from the same source.
- A Java optimization: binary search instead of repeated linear membership scans on already sorted data.
- A Java runtime comparison: interpreter mode (`-Xint`) versus the default JVM.
- Raw data, exact commands, configuration, runtime information, source snapshots, analysis, charts and tests.
- Unchanged original materials, hashes and attribution.

This is a focused research demonstrator, not an automatic optimizer for arbitrary programs. It measures the configured workload; it does not claim to characterize an entire library or application.

## Start with the evidence

Read `docs/HANDOFF.md` for the achieved results, limitations and remaining work. Read `docs/EXPERIMENT_PLAN.md` for the fixed evaluation design and `docs/LITERATURE.md` for the scientific rationale. The current measured evaluation has its own `analysis/RESULTS.md`, comparison CSV/JSON and charts beneath `results/`.

The earlier group's archived paper and slides are background material. No updated paper or presentation is produced in this stage.

The completed main evaluation is [here](results/20261029T163706Z_evaluation/analysis/RESULTS.md). It contains 17 comparisons and 680 fresh-process observations. The technical hand-off also covers the fresh original NetworkX and NumPy reproductions and the fixed-dtype diagnostic.

## Folder guide

| Path | Purpose |
|---|---|
| `archive/` | Byte-for-byte copies of supplied files and `SHA256.json` |
| `original/misc/` | Unchanged extracted original project, including Git history and all original results |
| `run.py`, `benchmark.py`, `analyze.py` | Original NetworkX comparison workflow; analyzer reused by the extension |
| `test_analysis.py` | Original statistical tests, including all four decisions |
| `numpy-experiment/` | Preserved NumPy runner, workload, analyzer and original results; new reruns get new timestamps |
| `experiments/` | Original NetworkX results plus new timestamped reproduction |
| `perflens.py` | New command runner, provenance, correctness protocol and paired analysis |
| `workloads/` | NetworkX graph-query workload and Java search demonstration |
| `configs/` | Explicit, inspectable configurations for the 17-comparison evaluation |
| `tests/` | New runner contract and workload correctness tests |
| `results/` | New suite data, test logs, original-data audit and diagnosis outputs |
| `summarize.py` | Reanalyze an explicit completed suite and produce tables/charts |
| `docs/` | Experiment plan, literature, attribution, course alignment and hand-off |

`original/`, `networkx_repo/` and local environments are excluded from new Git commits to avoid duplicating large dependencies. The unchanged ZIP remains in the deliverable package. The working directory keeps the recovered original Git history. Read `docs/ATTRIBUTION.md` before using the material in an assessment.

## Requirements and setup

Validated environment: Windows 11, Python 3.12 and a portable OpenJDK 21. Python 3.12 is recommended because the historical NumPy 1.26.4 case needs a compatible wheel. Use a full **JDK**, not only a JRE, for Java compilation.

The following PowerShell commands assume this project folder is the current directory and a working Python 3.12 command is available. Substitute its full executable path if needed.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
.\.venv\Scripts\python.exe verify_package.py
.\.venv\Scripts\python.exe prepare_sources.py
```

`prepare_sources.py` restores the original project and NetworkX from `archive/misc.zip` without overwriting existing files. It is useful after unpacking the portable package. No fresh NetworkX clone is needed. Never edit `original/` or `archive/`.

Install a JDK 21 from a trusted distributor and set `JAVA_HOME`, or pass the full path to `java.exe` when running the suite. The Java runtime used for the supplied measurements is recorded in every experiment's metadata. The local development JDK is outside the deliverable and is not silently required at its original path.

The portable ZIP omits local environments, unpacked originals, the active NetworkX checkout and `.git`. `archive/misc.zip` retains the complete original source/history; `prepare_sources.py` restores it. `history.bundle` additionally preserves the extended project history and can be inspected with `git bundle verify history.bundle` from a Git repository, or cloned into a separate folder with `git clone history.bundle perflens-history`. The ZIP supplies the archived inputs alongside that history; ignored archives are not embedded in new Git commits.

## Run the tests before measuring

```powershell
New-Item -ItemType Directory -Force .tmp | Out-Null
$env:TEMP = (Resolve-Path .tmp).Path
$env:TMP = $env:TEMP
$env:PERFLENS_JAVA = 'C:\Path\To\jdk-21\bin\java.exe'
.\.venv\Scripts\python.exe -B -m unittest -v test_analysis.py
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -v
.\.venv\Scripts\python.exe audit_original.py
```

Tests use constructed timing fixtures, subprocess fixtures and independent correctness oracles. Constructed timing values are **tests**, not experimental observations. No tests should run concurrently with a benchmark.

## Reproduce the original NetworkX comparison

```powershell
.\.venv\Scripts\python.exe run.py --commits 87b57851e9 6da4704cbf --repeats 20 --loops 200 --warmups 3 --size 35
```

The original runner uses its dedicated `networkx_repo`, refuses a dirty checkout, verifies the import location, and restores its original Git state. Do not run another benchmark or edit this repository while it is measuring. The selected pair is a real historical pair, not a known performance regression.

For original saved-data reanalysis without changing archived files, use `audit_original.py`. It checks that the reported original statistics exactly reproduce from all supplied raw NetworkX and NumPy data.

## Reproduce the original NumPy case

After setting up the main environment, run:

```powershell
.\reproduce_numpy.ps1 -Python 'C:\Path\To\Python312\python.exe'
```

This creates two isolated environments with NumPy 1.26.4 and 2.0.0, runs the unchanged original release comparison and unchanged-version control, records the environments, and runs a separate explicit-int64 diagnostic. All three comparisons use 20 pairs. See `docs/NUMPY_PLAN.md` and `docs/HANDOFF.md`. The Windows default input dtype differs between these historical releases, so the original source-level comparison and fixed-dtype diagnostic answer different questions. A package-setup failure from the development environment is retained in `results/numpy-setup-first-attempt.txt`; no benchmark result was discarded.

## Run the new evaluation

The supplied configurations already encode the preselected workloads, 20 pairs, 5% threshold and two session seeds. On this host logical CPUs 2 and 4 were allowed. On another host, inspect CPU affinity and choose valid CPUs first. `make_configs.py --cpu N --other-cpu M` regenerates configurations; record this change as a different setup rather than pretending it is the original experiment.

```powershell
.\.venv\Scripts\python.exe run_suite.py --java 'C:\Path\To\jdk-21\bin\java.exe'
```

This runs 17 comparisons sequentially: nine initial comparisons, then eight held-out confirmations. It creates a new timestamped results folder and never overwrites a previous run. Use `--session 1` or `--session 2` for a single session. Each comparison uses 40 fresh benchmark processes. Compilation, setup and source snapshots are outside the kernel timer.

The contention experiment starts a temporary busy worker on one logical CPU, waits for readiness, and terminates it after the observation. The same-CPU and separate-CPU arms deliberately change placement. It does not disable services or change power settings. The two selected logical CPUs are not a claim of independent physical cores.

For one comparison:

```powershell
.\.venv\Scripts\python.exe perflens.py configs\1_python_optimization.json
.\.venv\Scripts\python.exe perflens.py configs\1_java_runtime.json --java 'C:\Path\To\jdk-21\bin\java.exe'
```

## Read and regenerate results

Replace the example suite path below with the actual completed folder printed by `run_suite.py`:

```powershell
.\.venv\Scripts\python.exe summarize.py results\ACTUAL_SUITE_FOLDER
```

The analyzer verifies completion, the raw CSV hash, every pair and checksum, and recomputes the saved summary before making charts. The generated `analysis/` folder contains:

- `RESULTS.md`: measured findings and limitations.
- `comparisons.csv` and `comparisons.json`: effects, uncertainty, CV, target assessment, point-only/minimum summaries and process-wall means.
- `effects.png`: all effects and intervals.
- Per-comparison raw-order plots and box plots, plus JVM warmup traces.

Each experiment stores `raw.csv`, `observations.jsonl`, `config.json`, `metadata.json`, `summary.json`, and `source/`. The raw JSONL includes the actual argument-array command, result payload, warmup trace and any standard error. Paths in metadata describe the original measurement machine; use current configuration placeholders for reruns.

## Statistical interpretation

The existing analyzer reports relative mean time change:

`100 × (candidate mean / reference mean − 1)`

Positive means slower. It resamples complete pairs 5,000 times and reports an approximate 95% percentile bootstrap interval.

| Decision | Rule with the preselected 5% threshold |
|---|---|
| `regression` | Entire interval above +5% |
| `improvement` | Entire interval below −5% |
| `within_threshold` | Entire interval inside [−5%, +5%] |
| `inconclusive` | Anything else |

Statistical direction versus zero is reported separately. Within-threshold is not proof of identical performance. One fresh process supplies one batch-average observation; timed loops and warmup calls are not additional independent samples.

The illustrative graph budget is **3 ms per operation on average**, chosen before the new suite. It is not a real customer SLA. Both relative classification and observed-mean target assessment are reported. An unchanged program can miss this budget, motivating diagnosis and optimization.

## Add another language or workload

Create a JSON configuration with two named arms, `rounds >= 5`, a seed and a practical threshold. Commands are argument arrays, never shell expressions. Supported substitutions are `{python}`, `{root}` and `{java}`. Each invocation must output exactly one JSON object:

```json
{"seconds": 0.01, "checksum": [1, 2, 3], "valid": true}
```

`seconds` must be finite and positive. `valid` must reflect an independent correctness check implemented by the workload. Checksums must match across both arms and all rounds. Numeric result checking can use a stable canonical representation if floating-point differences are acceptable, but the current runner itself uses exact JSON checksum equality.

Failures retain metadata and, for attempted observations, `failures.jsonl` with command/output evidence. A Windows launch handshake assigns the command tree to a job before execution; timeouts/interruption terminate that job, including descendants whose original parent has exited. The POSIX implementation uses a new process group but has not been executed on this Windows host. The runner supports one sequential experiment at a time per project folder; do not launch competing runs. Timed benchmarks must be noninteractive and must not require stdin.

An arm can set `metric` to `internal` (default) or `process`. Whole-process timing includes startup/setup and affinity-wrapper overhead. Compare the same measurement boundary in both arms and state it explicitly. The runner trusts the benchmark's internal timer and correctness declaration; it cannot prove arbitrary third-party output truthful. Build external programs before running them; only the supplied Java demonstration is compiled automatically when a Java runtime is provided.

## Scientific and practical limits

These are controlled microbenchmark examples on one interactive machine. Two sessions demonstrate same-host repeatability, not reproduction on another machine. Twenty pairs are a modest fixed budget, not a demonstrated power optimum. Bootstrap coverage, independence of rounds and steady state are not proven. No multiple-comparison correction is implemented. No energy, allocation, memory, thermal or hardware-counter study is claimed.

BFS reuse helps repeated same-source queries on an unchanged graph; it does not improve every graph algorithm. Java binary search assumes sorted data; sorting cost and full application impact are not measured. Warmup may alter duration and variability without establishing steady state. Runtime flags have workload-specific effects.

All attempts and outcomes should remain visible. Do not delete inconclusive comparisons, tune thresholds after seeing results, or stop when a desired result appears. Check source attribution and development-assistance disclosure before submission. Peer reviews, examinations, paper, slides and colloquium remain separate course obligations.
