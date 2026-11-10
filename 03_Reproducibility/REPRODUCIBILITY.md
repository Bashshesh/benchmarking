# Reproducibility guide

**Honesty note.** Commands below are taken from the project's own documents (`02_PerfLens_Project/docs/REPRODUCIBILITY_UPGRADE.md`, 6 Nov version; its 5 Nov text is preserved inside it). Only the items in the table "What was actually executed during assembly" were run by the package assembler. Everything else is **documented but not verified here** (Windows + Docker + JDK 21 environment of the authors was not available).

## 1. Environments the data came from

| Component | Recorded value | Source |
|---|---|---|
| Office host | Intel Core Ultra 7 155H, 16 physical / 22 logical CPUs, 15.37 GiB usable RAM, Windows 11 10.0.26200 (SP0), Balanced power scheme | `results/final-roaring-20261105T225902Z/windows-native/environment.json` |
| Home host | AMD Ryzen 5 5500 | `results/hardware.json`, `docs/HANDOFF.md` |
| Python | 3.12 (office run 3.12.14, pip wheels; original prototype environment 3.12.15 / conda — "not exactly reconstructed") | `office-20261103/HOME_OFFICE_COMPARISON.md`, `docs/HANDOFF.md` |
| Java, native Windows | Oracle HotSpot JDK 21.0.8 (`C:\Program Files\Java\jdk-21`), executable SHA-256 `f3d26e4f…28ba` | `windows-native/environment.json`, `jvm.json` |
| Java, Docker/WSL2 | Temurin 21.0.7; base image `maven:3.9.9-eclipse-temurin-21@sha256:3a4ab327…0211e`; Linux Python base `python:3.12.12-slim-bookworm@sha256:593bd06e…e669c`; run flags `--network none --cpus 2 --memory 2g --read-only --cap-drop ALL --pids-limit 256` | `docs/REPRODUCIBILITY_UPGRADE.md`, `upgrade/java/reproduce.py` |
| JMH | 1.37; 512 MiB fixed heap, one thread, one fork per observation; AverageTime 3×200 ms warmup + 3×300 ms measurement; cache-state study: SingleShotTime, 16 000 untimed preheat batch calls, 30 warmup + 20 measured shots, 256 ops per shot | `docs/UPGRADE_RESULTS.md`, `final-roaring-…/plan.json` |
| Target library | RoaringBitmap, before `2dfd0fb994468c8d416dea3d217dc40ca7d6d145`, after `684531c13877fbdacccf02262b32e6faf889d76f`; measured artifact = `javac --release 8` build of base sources, not a published JAR | `results/upgrade-java-20261104T233351Z/inputs/*.zip` |
| Python dependencies | `requirements-lock.txt` is referenced by the docs but **not included** in either archive *(v2: now included at `02_PerfLens_Project/requirements-lock.txt`; it is the lock of the 2026-10-29 Codex environment, not of the 2026-10-18 prototype environment)* | — |

## 2. Commands (from the project documents; PowerShell, project root)

Setup (trusted project tests): create `.venv`, `pip install -r requirements-lock.txt`, set `TEMP`/`TMP` to a writable `.tmp`, set `PERFLENS_JAVA` to the JDK 21 `java.exe`, run `prepare_sources.py`, then `python -m unittest discover -s tests -v`.

Python/Java native studies (run sequentially; never two timed suites at once):
```
.\.venv\Scripts\python.exe -B upgrade/baseline.py
.\.venv\Scripts\python.exe -B upgrade/study.py --java $env:PERFLENS_JAVA
.\.venv\Scripts\python.exe -B upgrade/diagnose.py --java $env:PERFLENS_JAVA
.\.venv\Scripts\python.exe -B upgrade/calibrate.py --runs 30
```
Reanalysis: `summarize.py results/<baseline folder>`, `upgrade/analyze_evidence.py results/<native|synthetic folder> --kind native|synthetic`.

RoaringBitmap primary pair and extensions: `upgrade/java/reproduce.py --prepare | --pilot | --measure`, `upgrade/java/extend.py clone-tests | diagnostics | ablation | corpus | interventions | runtime-diagnostic`, `upgrade/java/compatibility.py`, `docker build -f upgrade/Linux.Dockerfile -t perflens-linux:resume .`, `upgrade/linux_host.py --label validation`, `upgrade/java/corpus_validate.py`, `upgrade/resume_analyze.py` (full list and caveats in `docs/REPRODUCIBILITY_UPGRADE.md`).

Final experiments (6 Nov), from `docs/REPRODUCIBILITY_UPGRADE.md`:
```
$run = 'results/final-roaring-' + [DateTime]::UtcNow.ToString('yyyyMMddTHHmmssZ')
.\.venv\Scripts\python.exe -B upgrade/java/final/study.py prepare $run
.\.venv\Scripts\python.exe -B upgrade/java/final/study.py lazy $run
.\.venv\Scripts\python.exe -B upgrade/java/final/study.py native-guard $run
.\.venv\Scripts\python.exe -B upgrade/java/final/native.py $run --java 'C:\Program Files\Java\jdk-21\bin\java.exe' --ipc reviewed-loopback
.\.venv\Scripts\python.exe -B upgrade/java/final/study.py verify $run
```
Check of archived results only: run just `verify` on the retained folder (needs neither Docker nor rebuilt classes). Native timing needs a shell that permits the loopback fork channel; the first attempt without it is kept in `windows-native-ipc-denied`.

Result locations: every run writes a new timestamped folder under `results/` (`raw.csv`/`observations.jsonl`/`summary.json` per case, JMH JSON for Java, `analysis/RESULTS.md` + plots for suites). Existing output folders must never be reused.

## 3. What was actually executed during assembly (Linux sandbox, Python 3.13.18, no Docker/JDK-21 Windows)

| Check | Outcome |
|---|---|
| `unzip -t` on both archives and the 6 nested ZIPs | no errors |
| SHA-256 of 333 files listed in `final-roaring-20261105T225902Z/evidence-sha256.json` | 333/333 match |
| `study.py verify` for the final run, in a scratch directory with `upgrade/` from the package and `analyze.py`/`perflens.py`/`process_control.py` copied from `results/upgrade-native-20261104T203656Z/measured_extra_0_441/source/` | exit 0; printed the same two summary paths as the retained `verification.txt`; input folder unchanged afterwards (`diff -r`) |
| Independent bootstrap recomputation of cache-state and native estimates | point estimates equal; CI ends within ≈1 pp (see `PAPER_PACKAGE_CONSISTENCY.md`) |
| `tests/test_upgrade.py` in the same scratch layout | 5 tests OK |
| `tests/test_statistics.py`, `test_archive.py`, `test_metrics_java.py`, `test_workloads.py` | **failed to run** in that scratch layout because only a few snapshot files were copied to the root (`summarize`, `audit_original`, `workloads/graph_queries.py`, `workloads/SearchBench.java` were not at the root; copies exist as run snapshots). Not a defect finding; a faithful rerun needs the full project root reassembled from the snapshots of one chosen run. |
| Any timing experiment, Docker build, JMH run, Windows-only test | **not run** |

The project's own test status (from its documents, not re-run): 29 native + 29 Linux tests, upstream RoaringBitmap `TestRank*` 193 (before) / 195 (after) with zero failures; twelve selected analysis/capture/cleanup tests for the final run (`results/final-roaring-20261105T225902Z/tests.txt`).

## 4. What is missing for a from-scratch rerun

* **[v2: this section describes package v1.]** Absent everywhere in the two original archives: root `README.md`, `requirements-lock.txt`, `package-manifest.json` — all three are now present (recovered from the complete-transfer ZIP).
* Present only as frozen per-run snapshots in `results/**/source/` (not at the root): `prepare_sources.py`, `run.py`, `benchmark.py`, `analyze.py` (one hash in all 81 copies), `summarize.py` (3 versions), `perflens.py` (3 versions), `process_control.py` (2 versions), `audit_original.py`, `test_analysis.py`, `workloads/graph_queries.py`, `SearchBench.java`. Use the snapshot belonging to the run you reproduce.
* *[v2: `archive/`, `experiments/`, `numpy-experiment/` are now present; Git history only up to 2026-10-29, see `05_Historical_Records/Git_History/GIT_HISTORY_NOTE.md`.]* `archive/` (originals of the preliminary NetworkX/NumPy prototype), `experiments/`, `numpy-experiment/` (raw prototype data), `.git` history (the docs name branch `upgrade/full-research-20261104` and checkpoint `c776a52`, but no repository data is present).
* Windows-style absolute paths inside `command.json`, `environment.json`, `verification.txt` are provenance only.

## 5. Where results will legitimately differ

Absolute times depend on CPU model, power plan, background load, JDK distribution (Temurin vs. Oracle), OS scheduler, Docker/WSL2 CPU allocation and JIT state; the authors' own data show control queries moving from +0.70 % to +5.45 % between Docker and native. Expect the *direction and decision class* of large effects (≈ −98…−99 %) to reproduce, not the third digit, and expect near-threshold/inconclusive cases to flip. Bootstrap intervals depend on the seed; with 8–10 pairs the ends move by ≈1 pp. Do not pool results across environments; do not interpret first-call numbers as cold-JVM or cold-memory behaviour.
