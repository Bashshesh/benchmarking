"""Refresh current technical reports from independently validated retained evidence."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,json,sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from upgrade.java.reproduce import write

def relative(path):return path.relative_to(ROOT).as_posix()
def newest(prefix,required=None):return sorted(p for p in (ROOT/'results').glob(prefix+'*') if required is None or (p/required).exists())[-1]
def prepend(path,heading,text):
    old=path.read_text(encoding='utf-8')
    marker='<!-- preserved-before-resume-20261105 -->'
    if marker in old:old=old.split(marker,1)[1].lstrip()
    historical='## Preserved earlier checkpoint (historical status)\n\n'
    while old.startswith(historical):old=old[len(historical):]
    path.write_text(heading+'\n\n'+text+'\n\n'+marker+'\n\n## Preserved earlier checkpoint (historical status)\n\n'+old,encoding='utf-8')

def main():
 p=argparse.ArgumentParser();p.add_argument('validation',type=Path);a=p.parse_args()
 folder=a.validation.resolve();v=json.loads((folder/'verification.json').read_text())
 cases={Path(c['case']).name:c for c in v['cases']}
 assert len(cases)==9 and v['observations']==156
 def effect(name):
    c=cases[name]['comparison'];lo,hi=c['ci95_percent']
    return f"{c['change_percent']:+.2f}% [95% CI {lo:+.2f}%, {hi:+.2f}%], **{c['decision']}**"
 corpus=newest('resume-corpus-','dataset.json');intervention=newest('resume-interventions-');compat=newest('resume-compatibility-')
 assert json.loads((compat/'status.json').read_text())['total_pinned_revisions']==4
 linux=ROOT/'results/resume-linux-after-fix-20261105T004355Z'
 assert json.loads((linux/'validation-status.json').read_text())['status']=='passed'
 for name in ['original-tests.json','extension-tests.json']:
    assert json.loads((linux/name).read_text())['returncode']==0
 native=json.loads((folder/'native-tests.json').read_text())
 assert [x['returncode'] for x in native]==[0,0]
 preserved=json.loads((folder/'preservation/verification.json').read_text())
 assert preserved['archived_original_entries_verified']==1116 and len(preserved['intentional_versioned_changes'])==3
 data=json.loads((corpus/'dataset.json').read_text())
 noise=cases['mitigation'];cv=noise['exploratory_cv_ratio_ci95']
 evidence=dict(primary='results/upgrade-java-20261104T233351Z',diagnostic='results/resume-diagnostics-20261104T234629Z',
   upstream_tests='results/resume-clone-tests-20261104T233916Z',corpus=relative(corpus),interventions=relative(intervention),
   ablation=str(Path(cases['guard-ablation']['case']).parent).replace('\\','/'),compatibility=relative(compat),
   linux_before='results/resume-linux-before-fix-20261105T004146Z',linux_after=relative(linux),validation=relative(folder),
   partial_ablation='results/resume-ablation-20261105T004520Z',failed_source_extraction='results/upgrade-java-20261104T233328Z',
   native_previous='results/upgrade-native-20261104T203656Z',synthetic_previous='results/upgrade-synthetic-20261104T215548Z')
 evidence['contention']=cases['contention']['case'].replace('\\','/')
 evidence['partial_mitigation']='results/resume-interventions-20261105T005600Z/mitigation'
 evidence['corpus_correctness']=relative(newest('resume-corpus-correctness-','status.json'))
 evidence['runtime_diagnostic']=relative(newest('resume-runtime-diagnostic-','plan.json'))
 answers=json.loads((ROOT/evidence['corpus_correctness']/'status.json').read_text())['answers']
 assert answers[0]==answers[1] and answers[0]['valid'] is True
 index_path=ROOT/'docs/UPGRADE_EVIDENCE_INDEX.json';index=json.loads(index_path.read_text());index['resume_20261105']=evidence;write(index_path,index)
 text='''Current branch: `upgrade/full-research-20261104`. All source/history/archives/attribution and earlier home/native-office measurements are preserved. Part 2 paper/presentation remains out of scope. This is Codex-assisted technical research, not independent human peer review.

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
'''
 for name in ['rank-65535','rank-65534','fullContainerRange-65535','guard-ablation','corpus-boundary','corpus-near-boundary','contention','mitigation','runtime']:
    c=cases[name];old,new=[c['summaries'][arm]['mean_seconds']*1e9 for arm in c['arms']]
    text+=f"|{name}|{c['pairs']}|{old:.2f} → {new:.2f}|{effect(name)}|\n"
 text+='''
There are **9 completed comparisons / 156 fresh JMH-fork observations**, with 3 iterations retained inside each fork. The original pair has 10 rounds/case; extensions have 8. Original rules use paired 5000-resample percentile bootstrap, fixed ±5% practical thresholds and fixed seeds. The small samples, possible serial dependence and no familywise correction limit certainty. Reanalysis reports order-group means, half-run drift, lag-one descriptions and exploratory circular length-2 block-bootstrap sensitivity without changing decisions.

## Mechanism and source hypothesis tested

Before, `BitmapContainer.rank(MAX)` scans all 1024 words using bit counts. After, it returns cached cardinality; an invalid lazy cardinality still needs repair. MAX-1 retains scanning. Public `rangeCardinality` with a container-boundary end exercises MAX internally. The frozen real-library harness consumes returned results and uses different containers. The upstream lazy-cardinality test passed; **first-lazy-call performance was not measured**.

The private ablation removes only the MAX guard from the after-revision BitmapContainer, recompiles that class inside Docker and passes the same independent oracle. The comparison in the table is intact optimized after / guard-removed after. Returning the large cost when the guard is removed, together with boundary controls, bytecode and JFR evidence, supports a bounded code-mechanism explanation. It does not identify every hardware/JIT contributor or estimate application-wide benefit. JFR sample counts depend on inlining, operation counts and duration; raw sample-count ratios are not speedups. There is no claimed native machine-code disassembly.

The PR claims a cached-cardinality shortcut, not a fixed numerical speedup. These data agree with that mechanism for the tested cached dense case and public range caller. No claim of O(1) lazy repair or universal acceleration of all container/query types follows. See [PR845](https://github.com/RoaringBitmap/RoaringBitmap/pull/845) and `docs/research/ROARING845_VERIFIED.json`.

## Application-derived input and permission outcome

'''
 text+=f"Frozen input: {data['byte_count']} bytes, SHA-256 `{data['sha256']}`. It concatenates sorted main Java sources from the **before** revision, indexes unsigned bytes >32, and uses identical bytes in both arms. Per-file hashes and Apache-2.0 license are retained in `{relative(corpus)}`. Full-block correctness was checked in trial setup; the supplemental full/near-boundary oracle checked {answers[0]['cases']} cases on both revisions with checksum {answers[0]['checksum']}. This is a real source-text indexing proxy, not a production bitmap query trace.\n\n"
 text+='''`real-roaring-datasets` was investigated again: GitHub license metadata is null, LICENSE returns404, README credits third-party inputs without a clear grant. Earlier documentation's statement that this dataset repository has an Apache license was incorrect and is explicitly corrected in `docs/research/DATASET_PERMISSION_CHECK_20261105.md`. The library's Apache license does not license that separate corpus. No such dataset was downloaded/used. Real-source input supports only limited input generalization; query boundaries were deliberately selected, not sampled from a real workload distribution.

## Noise, runtime and detector interpretation

'''
 text+=f"Contention: {effect('contention')}. Moving the same busy loop to another allowed virtual CPU: {effect('mitigation')}. Mitigation CV ratio's exploratory 95% interval is [{cv[0]:.3f}, {cv[1]:.3f}]; interpret this separately from the mean-time result. Cgroup v1 CPU/quota counters for the completed mitigation and within-fork variation are in verification.json. The earlier contention run has valid timings but the v2 counter path was unavailable. No physical-core class, frequency/thermal or cache mechanism is isolated by virtual CPU placement. Native hybrid-core evidence remains in the prior dataset.\n\n"
 text+=f"Actual library runtime setting: candidate tier1 / default is {effect('runtime')}. A separate matched rank(65534) tier1 diagnostic recorded level1 via PrintCompilation, while the default diagnostic reached level4. The profiler event threshold can omit short compilation events; the text log confirms the tier independently. No native assembly was captured, so the slowdown cannot be assigned to a specific instruction or compiler pass. This is a fixed exploratory configuration comparison, not a held-out tuning recommendation. The earlier native selection/confirmation retained default after tier1 slowed it; it is not replaced or pooled. JIT configuration changes code generation, but automatic source rewriting/PGO/Graal/native compiler optimization remains future work.\n\n"
 text+='Separate JFR records (not clean timing replicates):\n\n|Run|Execution samples|Rank stack frames|Rank compilation tiers/counts|GC events|\n|---|---:|---:|---|---:|\n'
 for name,d in sorted({**v['diagnostics'],**v['runtime_diagnostics']}.items()):
    text+=f"|{name.removesuffix('-events')}|{d['event_counts'].get('jdk.ExecutionSample',0)}|{sum(d['rank_stack_source_lines'].values())}|{d['rank_compilation_levels']}|{d['event_counts'].get('jdk.GarbageCollection',0)}|\n"
 text+='\nCounts reflect the instrumented workload and inlining; do not compare them as elapsed-time effects.\n\n'
 text+='''Detector: existing synthetic truth-model sensitivity, finite-cell coverage83.3–100% with30 datasets/cell and inconclusive counts remain unchanged and separately labeled. Existing real extra-work fractions are not guaranteed timing-effect labels. The original JMH near-MAX control stays within threshold. A 5-pair **identical-code** Java Linux functional smoke initially flagged improvement, while the after-fix smoke was inconclusive. This is a preserved false directional outcome under a tiny/noisy batch, not a useful optimization or evidence of high classifier accuracy. Python constant-time payloads are protocol fixtures, not measurements. No threshold was tuned to hide these outcomes.

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
'''
 prepend(ROOT/'docs/UPGRADE_RESULTS.md','# PerfLens research continuation — verified 5 November 2026',text)
 short=f"Branch `upgrade/full-research-20261104`. Completed bounded Docker/WSL continuation: {v['case_count']} JMH comparisons/{v['observations']} fresh forks; upstream Gradle193/195 tests; five JFR traces (four mechanism, one tier1); guard-ablation mechanism test; real-source input; virtual-CPU contention/mitigation/runtime comparisons; four-revision pilots. Native and Linux29 tests pass. POSIX successful-parent descendant leak reproduced then fixed. Raw summaries independently verified. See docs/UPGRADE_RESULTS.md and docs/UPGRADE_EVIDENCE_INDEX.json. Existing native/home results and all18 skills preserved; no pooling or Part2. Limitations: small samples, virtualized interactive environment, source-text proxy only, public corpus permissions unresolved, no universal accuracy/production claims. Earlier checkpoint text below retains its historical blocked status."
 prepend(ROOT/'CURRENT_STATUS.md','# PerfLens current status — 5 November 2026',short)
 selection=f"5 November follow-up: actual isolated PR845 pair builds/oracles/JMH pilots passed; upstream Gradle TestRank193/195 tests passed. {v['case_count']} comparisons/{v['observations']} fresh forks include measured primary and follow-ups; exact results in UPGRADE_RESULTS. Four nearby pinned revisions passed the same external pilot (see {relative(compat)}), satisfying a narrow source-compatibility gate, not release/JDK generality. RoaringBitmap is now the accepted bounded primary; no second repository needed. Measured artifact is direct base Java8 source build on Temurin21.0.7, separately distinguished from successful normal Gradle tests. Correct the older dataset-license claim: real-roaring-datasets metadata license=null, LICENSE404; no dataset used under that assumption. Detailed permission audit: research/DATASET_PERMISSION_CHECK_20261105.md. Historical screening below predates restored isolation."
 for name in ['JAVA_REPOSITORY_SELECTION.md','JAVA_COMMIT_SELECTION.md']:
    prepend(ROOT/'docs'/name,'# Java selection follow-up — 5 November 2026',selection)
 noise_text=f"""# Noise investigation follow-up — 5 November 2026

The previous native Windows evidence is retained, not pooled: results/upgrade-native-20261104T203656Z and results/upgrade-diagnostics-20261104T215420Z. New evidence: {relative(intervention)}, {relative(folder)}/verification.json and results/resume-diagnostics-20261104T234629Z. All below are exploratory bounded investigations, not independent-machine replication.

|Factor/hypothesis|Control and intervention|Evidence/observed outcome|Confounders and mitigation limits|
|---|---|---|---|
|CPU scheduling contention divides runnable time|Same real-library rank path/heap/JMH; clean vs busy loop on same allowed virtual CPU; then move identical loop to a second virtual CPU|Contention {effect('contention')}; mitigation {effect('mitigation')}; before/after cgroup v1 counters captured in mitigation retry. Earlier v2 path missing is recorded.|Virtual CPU does not prove physical core class; quota, SMT, cache, frequency/JIT remain. Pinning both JVM launcher and fork uses inherited affinity.|
|Variation may decrease after separating load|Compare fork-level CVs independently of mean|Mitigation candidate/reference CV interval [{cv[0]:.3f},{cv[1]:.3f}], exploratory paired resampling|8pairs only; CV estimates and confidence coverage unstable. Do not infer variance reduction from faster means alone.|
|JVM compilation changes observed hot path|Actual before/after MAX vs near-MAX diagnostics; fixed wall-budget loops; default vs tier1 JMH|JFR execution stacks/compilation tiers, bytecode and separate runtime effect {effect('runtime')}|Instrumentation, JIT inlining and unequal operation counts preclude raw sample-count speedups; fixed warmup does not prove steady state.|
|GC might perturb timing|Record separate JFR GC events and JVM gc/safepoint logs|Exact event counts in verification.json, original .jfr/.log retained|A short run with few/no captured GC events does not establish general GC irrelevance. No induced-GC mitigation study is claimed.|
|Frequency/thermal/core class might explain affinity effects|Prior native topology/probes kept; new container CPU information recorded|Container /proc/cpuinfo and cgroup limits captured, native same-class and heterogeneous effects already reported|No trustworthy thermal/frequency control or virtual-to-physical class mapping; no frequency/cache causal claim.|
|Order/drift/autocorrelation distort pair inference|Randomized whole-arm order; independent JVM forks; equal inputs and JMH settings|Order-group means, half-run drift, lag-one description and length2 block-bootstrap sensitivity retained|Descriptive diagnostics cannot prove independence; small8/10pair samples, shared host and multiple comparisons remain.|

Main repeated-fork measurement and profiler runs were executed sequentially. Diagnostic measurements and Docker/WSL observations stay separate from clean timing/native data. The ablation infrastructure timeout is retained; incomplete samples were not used as a favorable run-selection mechanism. No cache-state or steady-state proof is claimed. The Linux tiny functional control's false improvement is preserved as a warning about untrustworthy short batches.
"""
 (ROOT/'docs/NOISE_INVESTIGATION.md').write_text(noise_text,encoding='utf-8')
 runtime=f"5 November actual-library extension: tier1/default {effect('runtime')}. Exact raw case: {cases['runtime']['case']}. This is an exploratory same-artifact/input JMH comparison, separate from the earlier native held-out evaluator; no favorable configuration is forced. JFR and JVM logs now also cover actual Roaring code. Bytecode was examined; native machine-code/PGO/source generation remains unexecuted. See UPGRADE_RESULTS and NOISE_INVESTIGATION for diagnostics, uncertainty and limitations."
 prepend(ROOT/'docs/SYSTEM_AWARE_OPTIMIZATION.md','# System-aware follow-up — 5 November 2026',runtime)
 prepend(ROOT/'docs/MEASUREMENT_METHODOLOGY_COMPARISON.md','# Executed methodology follow-up — 5 November 2026',
    'Actual-library JMH and JFR are now executed, not blocked. Each independent fork supplies one observation; three correlated iterations remain nested. Paired bootstrap is unchanged, with additional order/drift/CV and circular block-bootstrap sensitivity. JFR, GC/JIT logs and javap bytecode support diagnosis; throughput from JMH avgt is explicitly a derived reciprocal rate. Linux timeout/descendant/cross-language tests passed after a verified POSIX fix. See UPGRADE_RESULTS, NOISE_INVESTIGATION and resume_20261105 evidence index. Rows below retain the original methodology inventory, not current execution gates.')
 reproduce='''Current evidence and limitations: UPGRADE_RESULTS and UPGRADE_EVIDENCE_INDEX.json, resume_20261105. Keep native Windows, Docker/WSL and home observations separate. Never run two timed suites at once. The completed initial pair was not repeated after interruption.

On a fresh computer use Python3.12/full JDK21 for trusted project tests, locked dependencies, preserved archives/sources and the existing branch. Recreate local environments. Source archives are transport-hashed; the isolated clone verifies Git objects. Do not execute upstream Java/Gradle natively.

```powershell
.\\.venv\\Scripts\\python.exe -B upgrade/java/reproduce.py --prepare
.\\.venv\\Scripts\\python.exe -B upgrade/java/reproduce.py --pilot
.\\.venv\\Scripts\\python.exe -B upgrade/java/reproduce.py --measure
.\\.venv\\Scripts\\python.exe -B upgrade/java/extend.py clone-tests
.\\.venv\\Scripts\\python.exe -B upgrade/java/extend.py diagnostics
.\\.venv\\Scripts\\python.exe -B upgrade/java/extend.py ablation
.\\.venv\\Scripts\\python.exe -B upgrade/java/extend.py corpus
.\\.venv\\Scripts\\python.exe -B upgrade/java/extend.py interventions
.\\.venv\\Scripts\\python.exe -B upgrade/java/extend.py runtime-diagnostic
.\\.venv\\Scripts\\python.exe -B upgrade/java/compatibility.py
docker build -f upgrade/Linux.Dockerfile -t perflens-linux:resume .
.\\.venv\\Scripts\\python.exe -B upgrade/linux_host.py --label validation
.\\.venv\\Scripts\\python.exe -B upgrade/java/corpus_validate.py
.\\.venv\\Scripts\\python.exe -B upgrade/resume_analyze.py
```

Commands are **sequential**, each gated by successful process exit and correctness; retain failed receipts. Paths/timestamps in the retained data are provenance, not portable executable paths. `resume_analyze.py` defaults to the retained office primary/diagnostics/clone folders; for a fresh measurement pass `--primary`, `--diagnostics`, `--runtime-diagnostics`, `--clone-tests`, and one `--extension` argument per selected extension folder. It validates ZIP member hashes directly so the old absolute source-cache paths are unnecessary. It refuses duplicate cases and incomplete pair rows. No raw observations from different hosts/environments may be combined.

The short `.tmp/j845` cache avoids Windows long paths; `--prepare` deliberately refuses an existing source cache. On this office computer do not rerun preparation over the completed cache. A fresh extracted project/new empty cache is the supported full reproduction route. Extend scripts reuse existing successful artifacts, never silently rebuild the initial pair. Original measurement harness bytes are frozen in the built image, and preparation records them. Later source additions and logging-only UTF-8 capture fixes are separately versioned. A changed orchestration script must not be mistaken for changed benchmark code.

The original primary image ID and dependency hashes are in preparation.json; extension plans reuse the same image ID. The resolved Maven base was `maven:3.9.9-eclipse-temurin-21@sha256:3a4ab3276a087bf276f79cae96b1af04f53731bec53fb2e651aca79e4b10211e`; the Linux Python base was `python:3.12.12-slim-bookworm@sha256:593bd06efe90efa80dc4eee3948be7c0fde4134606dd40d8dd8dbcade98e669c`. These digests are captured in the actual BuildKit logs. Docker builds need public dependency network access without secrets; clean/diagnostic execution uses network none, read-only root/source, non-root user, dropped capabilities and dedicated output mounts. Linux validation mounts only a copied reviewed-code subset. `linux_host.py` receipts show its image and source hashes. Disposable Linux project copies are scratch workspaces, not required transfer sources; the Git source and mount hash record are authoritative.

Public real-roaring-datasets permission remains unresolved; do not add it implicitly. The executed input is pinned Apache-licensed library source bytes, a limited text-index proxy. Corpus full-block oracle executes during JMH setup; `corpus_validate.py` additionally verifies full/near-block results independently on both versions before final interpretation. For interpretation use the retained dataset metadata/checksums and paired summaries, not raw console point estimates.

The previous 4 November finalize_upgrade.py describes that historical checkpoint and must not be run as a current status generator. It assumes two changed checkpoint files; current preservation permits three explicitly documented files. `upgrade/preserve.py` verifies all unchanged originals and stores exact pre-upgrade bytes from the earlier supplied transfer ZIP. Preserve that ZIP or the new preservation snapshot; a Git clone alone omits ignored archives/NetworkX inputs.
'''
 prepend(ROOT/'docs/REPRODUCIBILITY_UPGRADE.md','# Reproduce the resumed research — 5 November 2026',reproduce)
 java_doc=ROOT/'upgrade/java/REPRODUCE.md'
 prepend(java_doc,'# Verified isolated Java case — 5 November 2026',
    'Primary builds/oracles/JMH pilots, upstream Gradle193/195 rank tests, 10-pair original measurements, four JFR diagnostics, 8-pair guard ablation, source-input and noise/runtime extensions now executed. See docs/UPGRADE_RESULTS and the resume_20261105 evidence index for exact outcomes and limitations. Default/lazy-first-call and published corpus generalization must not be inferred. The setup instructions below were originally prepared while Docker was unavailable; their NOT EXECUTED text is historical, superseded only for the explicitly evidenced gates above.')
 changelog=ROOT/'docs/UPGRADE_CHANGELOG.md'
 heading='## 5 November resumed checkpoint'
 prior=changelog.read_text(encoding='utf-8').split(heading,1)[0].rstrip()
 changelog.write_text(prior+'\n\n'+heading+'\n\nRestored Docker; preserved completed initial pair after usage interruption; verified original Gradle193/195 tests and JFR outputs. Added private guard ablation, real-source byte-index input, virtual-affinity noise/JVM experiments, four-revision compatibility and independent raw validation. Reproduced then fixed POSIX success-parent descendant cleanup in perflens.py; unchanged analyzer. Added UTF-8 command capture regression test and propagated Linux wrapper test failures. Corrected unsupported dataset-license claim; no restricted corpus used. Partial watchdog failures retained, complete retries not selected by significance. Exact numbers/paths are in UPGRADE_RESULTS and UPGRADE_EVIDENCE_INDEX. All29 native/Linux tests pass; original bytes and contributors preserved; no Part2.\n',encoding='utf-8')
 print('Updated current status, results, evidence index, selection, noise/method/runtime and reproducibility documents.')
if __name__=='__main__':main()
