# PerfLens — Final Seminar Submission Package

HAW Kiel · Advanced Software Engineering seminar · Topic 9 ("How can software performance be measured reliably, and which optimization techniques provide reproducible improvements?")
Authors of the paper: Ansar Bashayev, Thanh Tra Nguyen, Dasol Jung.
Package assembled 9 November 2026 from two project snapshots and the final paper PDF.
> **v2 (2026-11-09):** this package was extended with the 252 files that exist only in `PerfLens-complete-transfer-20261103T160906Z.zip` (root files, `experiments/`, `numpy-experiment/`, `archive/`, `configs/`, `workloads/`, `images/`, `history.bundle`, `requirements-lock.txt`, `package-manifest.json`; 129 under `02_PerfLens_Project/`, 123 transfer/office/skill files under `05_Historical_Records/Transfer_Packages/`). Statements below that say these items are absent describe package **v1** and are corrected in `CHANGELOG_INTEGRATION_v2.md` and `CONFLICTS_AND_DECISIONS_v2_ADDENDUM.md`.

This package **merges two archives without discarding anything**. Nothing in the research data, code or documents was edited; the only changes are (a) the union of both archives, (b) three documents where the later archive is a strict superset of the earlier one, and (c) new navigation/verification documents listed in `CHANGELOG_INTEGRATION.md`.

## 1. Project and research purpose

PerfLens extends a small NetworkX performance-regression prototype (paired repetitions, paired bootstrap interval, ±5 % practical threshold) with Java support, correctness oracles, environment/hash receipts, and a diagnostic path (JFR, JIT logs, ablation) that is kept apart from clean timing. The paper asks three questions:

| RQ | Question (paper wording, abridged) |
|---|---|
| RQ1 | Can paired repeated benchmarking with an uncertainty estimate separate meaningful changes between two versions from measurement variability, in Python and Java? |
| RQ2 | How large is the variability, and how do interference, warmup, runtime configuration and environment change measured performance and its interpretation? |
| RQ3 | Can a real library optimization be reproduced and its source-level mechanism isolated, and in which states and environments does its benefit hold? |

How this matches the four goals in the submission brief (and where it does not go further than the evidence):

* *Real optimization effect vs. chance/variation* — covered: fresh-process paired observations, 5 000-resample paired percentile bootstrap, four-way decision (regression / improvement / within threshold / inconclusive). Limits: 8–20 pairs per comparison, no multiple-comparison correction, possible serial dependence.
* *Python and Java* — covered: Python (NetworkX BFS workloads, NumPy argsort prototype cases) and Java (linear vs. binary search, warmup, `-Xint`, RoaringBitmap PR #845 via JMH 1.37). The two languages are not compared head-to-head on one workload; they are separate studies under one method.
* *Explaining a gain* — covered for one case only: RoaringBitmap `BitmapContainer.rank(65535)` (control query, private guard-ablation, bytecode inspection, separate JFR runs). The paper itself states this is a *bounded* explanation, not a proof of every JIT/hardware contributor. Statistical significance is never treated as proof of cause.
* *Evidence beyond the timed interval* — JFR samples, PrintCompilation logs, bytecode, upstream test runs, independent correctness oracles, and a synthetic calibration study (540 generated datasets). JFR sample counts are explicitly *not* speed estimates.

Not claimed: a generally accurate detector, production speedups, end-to-end application benefit, native-compiler/PGO optimization, replication on an independent machine, or the planned analysis of regressions across NetworkX history (listed as future work in the paper).

## 2. Main results (all numbers are taken from archived summaries; see `04_Navigation_and_Traceability/EVIDENCE_TRACEABILITY.md`)

* **Controlled suite** (17 comparisons × 20 pairs = 680 fresh-process observations per host; home Ryzen 5 5500 and office Core Ultra 7 155H): known effects were classified as expected on both hosts; decisions agreed in 15 of 17 comparisons. The two unchanged-code controls were *within threshold* on the home PC (−0.08 %, −0.21 %) but *inconclusive* on the noisier office PC (−7.60 % [−21.84, +15.36], −0.94 % [−14.65, +15.50]).
* **Noise**: same-CPU contention changed mean time by +52 % to +98 %; moving the load lowered mean time (−38 % to −51 %) but reduced variability was not established (CV-ratio intervals include 1 in several cases). Virtual-CPU placement does not identify the physical core/cache effect.
* **Detector limits** (synthetic study, 540 datasets): a +10 % slowdown was flagged in 30/30, 23/30, 7/30 datasets at CV 1 %, 5 %, 20 %; empirical coverage of the nominal 95 % interval ranged 83.3–100 %.
* **RoaringBitmap PR #845** (before `2dfd0fb9…`, after `684531c1…`; Docker/WSL2, JMH AverageTime): `rank(65535)` 342.61 → 1.75 ns/op (−99.49 % [−99.50, −99.48]); control `rank(65534)` +0.70 % (within threshold); public full-container range query −97.85 %; removing the guard restores the cost (−99.44 % intact vs. ablated).
* **Final experiments (6 Nov, later archive)**: *cache state* (JMH SingleShotTime, Docker/WSL2): precomputed −99.09 %, next call after priming −98.73 %, but the **first call on an invalid cache is −16.62 % [−38.14, +8.92] — inconclusive**. *Native Windows 11 replication* (same physical PC, Oracle HotSpot 21.0.8): MAX rank −99.54 %, range −97.97 %; near-boundary control +5.45 % [+0.13, +12.69] — inconclusive at the ±5 % threshold. Docker/WSL2 and native results are **never pooled**; OS, JDK build, scheduling and isolation changed together.

## 3. Where the evidence lives

| Need | Location |
|---|---|
| Paper | `01_Paper/PerfLens_Integrated_LNCS_official_v2.pdf` |
| Merged project tree (original relative layout preserved) | `02_PerfLens_Project/{docs,results,tests,upgrade}` |
| Latest results narrative | `02_PerfLens_Project/docs/UPGRADE_RESULTS.md` (6 Nov version, contains the 5 Nov text unchanged below the new section) |
| Machine-readable evidence index | `02_PerfLens_Project/docs/UPGRADE_EVIDENCE_INDEX.json` |
| Result → experiment → code → raw data → analysis chain | `04_Navigation_and_Traceability/EVIDENCE_TRACEABILITY.md` |
| Per-file origin (archive, SHA-256, category) of all 3 135 project files | `04_Navigation_and_Traceability/FILE_PROVENANCE.csv` |
| Reproduction guide | `03_Reproducibility/REPRODUCIBILITY.md` |
| Decisions on overlapping files | `CONFLICTS_AND_DECISIONS.md` |
| Paper ↔ package check | `PAPER_PACKAGE_CONSISTENCY.md` |
| Earlier versions and original archive listings/hashes | `05_Historical_Records/` |
| Integrity hashes of every file in this package | `MANIFEST_SHA256.txt` |

## 4. Directory structure and why it differs from the suggested template

```
PerfLens-Seminar-Submission/
├── README.md, MANIFEST_SHA256.txt, CHANGELOG_INTEGRATION.md,
│   CONFLICTS_AND_DECISIONS.md, PAPER_PACKAGE_CONSISTENCY.md
├── 01_Paper/
├── 02_PerfLens_Project/          docs/  results/  tests/  upgrade/   (original relative paths)
├── 03_Reproducibility/
├── 04_Navigation_and_Traceability/
└── 05_Historical_Records/        Previous_Versions/  Original_Archive_Manifests/
```

The project's own documents, `UPGRADE_EVIDENCE_INDEX.json`, run metadata and scripts refer to each other by project-relative paths (`results/…`, `upgrade/…`, `docs/…`). Splitting `results/` into separate "raw data / analysis / experiments" folders would break those references and the verification script, so the original layout is kept intact and the numbered folders add navigation on top of it. (Result folders are timestamped and self-contained: raw JMH JSON, CSV/JSONL observations, configs, source snapshots, summaries, plots.)

## 5. Environments (never pooled)

| Label | Host / runtime | Where |
|---|---|---|
| Home | AMD Ryzen 5 5500, recorded home OpenJDK | `results/20261029T163706Z_evaluation`, `results/hardware.json` |
| Office native | Intel Core Ultra 7 155H (16 physical / 22 logical), 15.4 GiB, Windows 11 10.0.26200, Python 3.12.14, Oracle JDK 21.0.8, Balanced power scheme | `results/office-20261103`, `results/upgrade-native-*`, `…/windows-native` |
| Office Docker/WSL2 | same physical office PC, Temurin 21.0.7, `--network none`, `--cpus 2`, `--memory 2g` | `results/upgrade-java-*`, `results/resume-*`, `…/docker-lazy` |
| Synthetic | generated data, no hardware | `results/upgrade-synthetic-*` |

## 6. Known limits of this package (read before judging completeness)

1. **The two archives are not the whole project.** There is no project-root `README.md`, `.git` history, `requirements-lock.txt`, `package-manifest.json`, `archive/`, `experiments/`, `numpy-experiment/` (preliminary NetworkX/NumPy prototype raw data). The project-root Python/Java sources (`analyze.py`, `perflens.py`, `run.py`, `benchmark.py`, `summarize.py`, `process_control.py`, `audit_original.py`, workloads, …) are **not at the root**; they exist only as frozen per-run snapshots under `results/**/source/` (some in several versions). Details in `03_Reproducibility/REPRODUCIBILITY.md`.
2. The Java-side `study.py verify` for the final run **does** work from the archived data once the unchanged `analyze.py` is restored from a run snapshot (checked during assembly; see REPRODUCIBILITY.md). Full re-measurement needs Docker, JDK 21 and Windows and was **not** re-run.
3. Many retained metadata files contain the original author's absolute Windows paths; they are provenance, not portable paths.

## 7. Suggested reading order

1. `01_Paper/…pdf` (≈11 pages) → 2. this README → 3. `02_PerfLens_Project/docs/UPGRADE_RESULTS.md` → 4. `04_…/EVIDENCE_TRACEABILITY.md` → 5. `docs/RESEARCH_METHODS_AND_EVIDENCE.md`, `docs/LITERATURE.md`, `docs/EXPERIMENT_PLAN.md` → 6. `docs/HANDOFF.md` (29 Oct state) → 7. `03_Reproducibility/REPRODUCIBILITY.md` → 8. `CONFLICTS_AND_DECISIONS.md`, `PAPER_PACKAGE_CONSISTENCY.md`.

## 8. Attribution

The preliminary report, presentation and prototype are by the seminar team; the extension was developed with OpenAI Codex assistance; ChatGPT and Anthropic Claude assisted with drafting/consistency checks (see the paper's provenance paragraph and `docs/ATTRIBUTION.md`). The package assembly and consistency checks in this directory were done with Claude. AI tools are not authors or independent validators. 
