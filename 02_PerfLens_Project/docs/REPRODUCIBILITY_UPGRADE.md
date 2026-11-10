# Reproduce the resumed research — 5 November 2026

## Final PR845 experiments · 6 November 2026

Use the same verified source cache and Docker image recorded by the prior PR845 work.
The final runner checks the cached source file hashes, pinned image ID and regenerated
BitmapContainer class hashes. The archived Java source ZIPs and the original preparation
commands below provide the source provenance. The timing runner expects the recorded
image ID. Archived-data verification works on a fresh host without that image.

Run from the PerfLens directory with the project virtual environment and a Windows JDK 21.
The commands run sequentially. Docker pipe access may require approval for preparation,
lazy timing and guard compilation. Run native timing in a workspace shell that permits
local fork IPC. The initial default-sandbox attempt denied the loopback connect. The
reviewed-loopback run used an explicitly approved execution boundary and kept the
Docker-built Java guard, exclusive code-source policy, Windows job and minimal environment.
Trusted harness and JMH code can use the IPv4 loopback fork channel. The library domain
remains ungranted. Use the default-sandbox label if your shell supports this channel there.

```powershell
$run = 'results/final-roaring-' + [DateTime]::UtcNow.ToString('yyyyMMddTHHmmssZ')
.\.venv\Scripts\python.exe -B upgrade/java/final/study.py prepare $run
if ($LASTEXITCODE -ne 0) { throw 'Docker build or correctness gate failed' }
.\.venv\Scripts\python.exe -B upgrade/java/final/study.py lazy $run
if ($LASTEXITCODE -ne 0) { throw 'Docker lazy study failed' }
.\.venv\Scripts\python.exe -B upgrade/java/final/study.py native-guard $run
if ($LASTEXITCODE -ne 0) { throw 'Docker guard compilation failed' }
.\.venv\Scripts\python.exe -B upgrade/java/final/native.py $run --java 'C:\Program Files\Java\jdk-21\bin\java.exe' --ipc reviewed-loopback
if ($LASTEXITCODE -ne 0) { throw 'Native study failed. Retain the attempted run and inspect its receipts.' }
.\.venv\Scripts\python.exe -B upgrade/java/final/study.py verify $run
if ($LASTEXITCODE -ne 0) { throw 'Raw-data verification failed' }
```

The preparation runs the original correctness oracle and the new lazy-state and batch
oracles inside Docker. Windows execution stops on an artifact hash mismatch, missing
permission denial, incorrect checksum or failed JVM fork. The guard check also verifies
that trusted code is denied a non-loopback connection permission. The retained policy file and
JMH raw metadata record the runtime restrictions. The native Java executable and
environment settings are recorded separately from Docker. Treat their effects as two
estimates on one physical host and retain their raw files separately.

For archived results, run only the `verify` command with the retained timestamped folder.
It checks the randomized schedule and rebuilds the fork scores, intervals and raw hashes
in memory before comparing them with the saved CSV and JSON. This step needs neither
Docker nor rebuilt classes. The preliminary shot-only pilot is preserved for inspection
and has no complete paired summary.

---

Current evidence and limitations: UPGRADE_RESULTS and UPGRADE_EVIDENCE_INDEX.json, resume_20261105. Keep native Windows, Docker/WSL and home observations separate. Never run two timed suites at once. The completed initial pair was not repeated after interruption.

On a fresh computer use Python3.12/full JDK21 for trusted project tests, locked dependencies, preserved archives/sources and the existing branch. Recreate local environments. Source archives are transport-hashed; the isolated clone verifies Git objects. Do not execute upstream Java/Gradle natively.

```powershell
.\.venv\Scripts\python.exe -B upgrade/java/reproduce.py --prepare
.\.venv\Scripts\python.exe -B upgrade/java/reproduce.py --pilot
.\.venv\Scripts\python.exe -B upgrade/java/reproduce.py --measure
.\.venv\Scripts\python.exe -B upgrade/java/extend.py clone-tests
.\.venv\Scripts\python.exe -B upgrade/java/extend.py diagnostics
.\.venv\Scripts\python.exe -B upgrade/java/extend.py ablation
.\.venv\Scripts\python.exe -B upgrade/java/extend.py corpus
.\.venv\Scripts\python.exe -B upgrade/java/extend.py interventions
.\.venv\Scripts\python.exe -B upgrade/java/extend.py runtime-diagnostic
.\.venv\Scripts\python.exe -B upgrade/java/compatibility.py
docker build -f upgrade/Linux.Dockerfile -t perflens-linux:resume .
.\.venv\Scripts\python.exe -B upgrade/linux_host.py --label validation
.\.venv\Scripts\python.exe -B upgrade/java/corpus_validate.py
.\.venv\Scripts\python.exe -B upgrade/resume_analyze.py
```

Commands are **sequential**, each gated by successful process exit and correctness; retain failed receipts. Paths/timestamps in the retained data are provenance, not portable executable paths. `resume_analyze.py` defaults to the retained office primary/diagnostics/clone folders; for a fresh measurement pass `--primary`, `--diagnostics`, `--runtime-diagnostics`, `--clone-tests`, and one `--extension` argument per selected extension folder. It validates ZIP member hashes directly so the old absolute source-cache paths are unnecessary. It refuses duplicate cases and incomplete pair rows. No raw observations from different hosts/environments may be combined.

The short `.tmp/j845` cache avoids Windows long paths; `--prepare` deliberately refuses an existing source cache. On this office computer do not rerun preparation over the completed cache. A fresh extracted project/new empty cache is the supported full reproduction route. Extend scripts reuse existing successful artifacts, never silently rebuild the initial pair. Original measurement harness bytes are frozen in the built image, and preparation records them. Later source additions and logging-only UTF-8 capture fixes are separately versioned. A changed orchestration script must not be mistaken for changed benchmark code.

The original primary image ID and dependency hashes are in preparation.json; extension plans reuse the same image ID. The resolved Maven base was `maven:3.9.9-eclipse-temurin-21@sha256:3a4ab3276a087bf276f79cae96b1af04f53731bec53fb2e651aca79e4b10211e`; the Linux Python base was `python:3.12.12-slim-bookworm@sha256:593bd06efe90efa80dc4eee3948be7c0fde4134606dd40d8dd8dbcade98e669c`. These digests are captured in the actual BuildKit logs. Docker builds need public dependency network access without secrets; clean/diagnostic execution uses network none, read-only root/source, non-root user, dropped capabilities and dedicated output mounts. Linux validation mounts only a copied reviewed-code subset. `linux_host.py` receipts show its image and source hashes. Disposable Linux project copies are scratch workspaces, not required transfer sources; the Git source and mount hash record are authoritative.

Public real-roaring-datasets permission remains unresolved; do not add it implicitly. The executed input is pinned Apache-licensed library source bytes, a limited text-index proxy. Corpus full-block oracle executes during JMH setup; `corpus_validate.py` additionally verifies full/near-block results independently on both versions before final interpretation. For interpretation use the retained dataset metadata/checksums and paired summaries, not raw console point estimates.

The previous 4 November finalize_upgrade.py describes that historical checkpoint and must not be run as a current status generator. It assumes two changed checkpoint files; current preservation permits three explicitly documented files. `upgrade/preserve.py` verifies all unchanged originals and stores exact pre-upgrade bytes from the earlier supplied transfer ZIP. Preserve that ZIP or the new preservation snapshot; a Git clone alone omits ignored archives/NetworkX inputs.


<!-- preserved-before-resume-20261105 -->

## Preserved earlier checkpoint (historical status)

# Reproduce the research upgrade

Start with UPGRADE_RESULTS for actual completed/blocked gates, UPGRADE_FEASIBILITY for scope, and UPGRADE_CHANGELOG for source changes. The branch is `upgrade/full-research-20261104`; starting checkpoint111accf and all historical data/attribution remain intact. Part2 paper/presentation is not authorized.

## Trusted project setup and tests

Use Python3.12 and full JDK21. Create a local virtual environment and install requirements-lock.txt. Set TEMP/TMP to a writable project .tmp directory and PERFLENS_JAVA to the actual java executable. Follow README for offline restoration from unchanged archive/misc.zip. Never copy historical home/office executable paths blindly.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
New-Item -ItemType Directory -Force .tmp | Out-Null
$env:TEMP=(Resolve-Path .tmp).Path
$env:TMP=$env:TEMP
$env:PERFLENS_JAVA='C:\Path\To\jdk-21\bin\java.exe'
.\.venv\Scripts\python.exe -B prepare_sources.py
.\.venv\Scripts\python.exe -B -m unittest -v test_analysis.py
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -v
```

The original package-manifest.json describes the pre-upgrade checkpoint. Two intentional versioned files (process_control.py and tests/test_runner.py) differ, so do not overwrite its inventory or claim the current code is byte-identical to it. `upgrade/preserve.py` verifies all other listed files, archive bytes and recovered originals, and can retain exact previous versions from the original supplied transfer. That optional archival helper expects the source transfer ZIP in Downloads; on another machine use the retained pre-upgrade source snapshot/new preservation report instead. Historical archive SHA records remain authoritative for original inputs.

## Execute sequentially

Run one command to completion before starting the next timed or diagnostic command. Never run tests/builds/profilers or another suite during a timing suite. Do not repair/start Docker during native timings. Every new run gets a new timestamped folder; never reuse an existing output target. Inspect affinity/topology/JDK and record host identity before adapting settings.

```powershell
.\.venv\Scripts\python.exe -B upgrade/baseline.py
.\.venv\Scripts\python.exe -B upgrade/study.py --java $env:PERFLENS_JAVA
.\.venv\Scripts\python.exe -B upgrade/diagnose.py --java $env:PERFLENS_JAVA
.\.venv\Scripts\python.exe -B upgrade/calibrate.py --runs 30
```

The baseline preserves all17 original configurations/20pairs/seeds. The native study has exploratory/confirmatory JVM settings, additional resources, topology-aware interventions and measured redundant-work controls. The synthetic calibration contains18 cells x30 independent generated20-pair datasets, separate generation/bootstrap seeds, no benchmark timings. Diagnostics are instrumented and kept separate. No cross-machine observations are pooled.

## Reanalyze and validate

Replace ACTUAL paths with completed folders; latest absolute paths in old metadata are provenance, not portable references.

```powershell
.\.venv\Scripts\python.exe -B summarize.py results/ACTUAL_UPGRADE_OFFICE_FOLDER/baseline
.\.venv\Scripts\python.exe -B upgrade/analyze_evidence.py results/ACTUAL_NATIVE_FOLDER --kind native
.\.venv\Scripts\python.exe -B upgrade/analyze_evidence.py results/ACTUAL_SYNTHETIC_FOLDER --kind synthetic
```

Native reanalysis verifies status, CSV and JSONL hashes, every pair/order/checksum, source snapshots and exact original-classifier summary equality. It also reports secondary CPU uncertainty where all samples are positive, exploratory CV ratios and descriptive order/drift/autocorrelation. Synthetic reanalysis independently parses all stored pairs and repeats every5000-draw classification, then checks counts. Figures are generated with Matplotlib; dependency versions are pinned. Diagnostic raw latency quantiles and JFR JSON are separately inspectable.

## Real Java repository experiment

On this office Windows host Docker is unavailable. Do not run downloaded repository code here. All Roaring/Caffeine/Fory build and compatibility pilots, real-repository timings/profiling, and Linux-container execution are explicitly unexecuted. The prepared exact primary-pair commands, pinned SHAs, JMH source, boolean correctness oracle, Maven dependency POM, restricted Dockerfile and fail-closed runner are under `upgrade/java/`. Follow its REPRODUCE.md only on a working isolated environment. Both source builds and matching correctness/pilots must pass before measurement. Preserve raw JMH iterations nested inside single-fork observations.

No real published dataset was used: dataset-specific third-party permissions for real-roaring-datasets remain unresolved. All upgrade workload fixtures are labeled generated. An upstream README/PR number is not a measured local result.

## Cleanup portability

Windows uses bounded job termination/accounting and the launch handshake. POSIX uses process groups; a zombie is terminated but still needs its parent/init to reap it. The revised tests distinguish liveness from PID enumeration. Use Docker `--init` for container reaping. Linux execution and adversarial descendant behavior escaping a process group are not claimed tested on this Windows host; OS process containment is not a security sandbox. Apply the isolated third-party setup separately.
