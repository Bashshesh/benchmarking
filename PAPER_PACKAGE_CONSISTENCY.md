# Paper ↔ package consistency check

Paper: `01_Paper/PerfLens_Integrated_LNCS_official_v2.pdf` (11 pages; SHA-256 `d9b50caa44719dcb343a8bea14e3af850dcfbb4791847e9ff92768d5a027b30e`). **The paper was not modified.** Status codes: ✔ confirmed against package data · ◐ confirmed only in part · ✖ problem · ○ not checkable offline.

## A. Archive identification

| Paper statement (ref. [17]) | Result |
|---|---|
| `PerfLens-review-20261105.zip`, SHA-256 `7612d2e1…b965` | ✔ identical to the uploaded file |
| `PerfLens-final-review.zip`, SHA-256 `28af5db3…3804b00` | ✔ identical content hash (the upload carried the prefix `b3b85298-`; rename is only a transfer artifact) |
| RoaringBitmap commits `2dfd0fb9…` / `684531c1…` | ✔ both appear in `docs/UPGRADE_RESULTS.md`, build records and source ZIPs |
| `docs/HANDOFF.md` is the handoff record | ✔ present |
| "Saved results can be re-checked without Docker via `upgrade/java/final/study.py verify <run>`" | ◐ true **only after** restoring the unchanged `analyze.py` next to the project root. `study.py` does `from analyze import compare`, but `analyze.py` is not at the root of either ZIP; it exists, byte-identical in all 81 copies, under `results/**/source/analyze.py`. With it restored (scratch copy), `verify` exits 0 and modifies nothing. |
| "a full re-run needs Docker and JDK 21 (`docs/REPRODUCIBILITY_UPGRADE.md`)" | ✔ consistent with that document (it also needs Windows PowerShell commands as written) — **not re-run here** |

## B. Numbers

| Paper item | Source checked | Result |
|---|---|---|
| Table 2 (all 16 cells, session 1) | `20261029T163706Z_evaluation/*/summary.json` (home), `office-20261103/20261103T152546Z_evaluation/*/summary.json` (office), `HOME_OFFICE_COMPARISON.md` | ✔ exact to 2 decimals; session-2 values quoted in text (−0.21, −0.94) also ✔ |
| "decisions agreed for 15 of 17" | `HOME_OFFICE_COMPARISON.md` ("differ for 2/17") | ✔ |
| "also in the later office rerun" (controls inconclusive) | `upgrade-office-20261104T201220Z/baseline/{1,2}_control` = −4.61 [−15.24, +8.48], −8.22 [−19.46, +5.39], both inconclusive | ✔ |
| CPU-class results −59.06 [−62.02, −56.43]; +12.62 [+0.82, +35.14]; Tier-1 +10.18 [+6.46, +14.69] | `docs/UPGRADE_RESULTS.md` | ✔ (quoted from the report; underlying summaries not re-derived) |
| Synthetic: 30/30, 23/30, 7/30; coverage 83.3–100 % | `docs/UPGRADE_RESULTS.md` | ✔ quoted; not re-derived |
| Extra-work: 50 % 3/3 detected, 15 % 1/3, zero-extra CI [−10.56, −1.34] inconclusive | `upgrade-native-…/measured_extra_*/summary.json` (0p5: 3 regressions; 0p15: 1 regression, 2 inconclusive; others inconclusive); −10.56 found in `measured_extra_0_441` | ✔ |
| Table 3 core block (rank-65535 342.61→1.75 etc.) | `upgrade-java-20261104T233351Z/*/summary.json`, `docs/UPGRADE_RESULTS.md` | ✔ rows rank-65535, rank-65534, full-container range matched to the saved `summary.json` files (changes and CIs); remaining rows (ablation, source input, contention/mitigation/runtime) compared only with the numbers quoted in `docs/UPGRADE_RESULTS.md` |
| Table 3 native block and cache-state block | recomputed from `windows-native/forks.csv`, `docker-lazy/forks.csv` | ✔ means and point estimates match to 2 decimals (see below) |
| 193 / 195 upstream tests; 44 boundary cases; 1 428 579 B input | `docs/UPGRADE_RESULTS.md` | ✔ |
| Table 1 counts: 17/680 per host; 9/156 forks; 3/60 forks each | 17 comparisons × 20 pairs; 3×10 + 6×8 pairs ×2 arms = 156; 3 × 10 pairs × 2 = 60 | ✔ arithmetic; "22 / 278" native studies **not recounted** (○) |
| Docker: `--network none`, 2 CPUs | `upgrade/java/reproduce.py` (`--network none --cpus 2 --memory 2g`) | ✔ |

### Independent recomputation of the final-run estimates

My own code (paired percentile bootstrap, 5 000 resamples of whole pairs, seed 12345; not the project's seed) on the raw `forks.csv` files:

| Case | n pairs | mean ref → cand (ns) | change | my 95 % CI | paper |
|---|---:|---|---:|---|---|
| cached | 10 | 964.04 → 8.74 | −99.09 % | [−99.43, −98.40] | −99.09 [−99.43, −98.43] |
| first (invalid) | 10 | 857.01 → 714.60 | −16.62 % | [−37.52, +9.89] | −16.62 [−38.14, +8.92] |
| repeat | 10 | 660.44 → 8.42 | −98.73 % | [−98.99, −98.36] | −98.73 [−98.99, −98.37] |
| native rank-max | 10 | 607.19 → 2.78 | −99.54 % | [−99.56, −99.52] | same |
| native rank-near | 10 | 614.71 → 648.20 | +5.45 % | [+0.24, +12.90] | +5.45 [+0.13, +12.69] |
| native range | 10 | 615.03 → 12.47 | −97.97 % | [−98.02, −97.92] | same |

Point estimates and means are reproduced exactly; interval ends move by up to ≈1 pp with the bootstrap seed. Interpretation is unchanged (first call: crosses zero; native near-boundary: excludes zero but crosses +5 %). Worth one sentence in the paper: bootstrap intervals with 10 pairs are seed-sensitive (the paper already says this for the source-input near-boundary case only).

## C. Problems and recommendations

| # | Sev. | Finding | Recommendation (paper not edited) |
|---|---|---|---|
| 1 | medium | Artifact-availability text implies `study.py verify` is self-contained; it needs `analyze.py`, which is present only as a per-run snapshot (A). | Add: "restore `analyze.py` from `results/*/source/`" or ship the project root. |
| 2 | medium | Section 3.1 says the prototype's "code, data and attribution are preserved unchanged [17]". The prototype's analyzer survives as snapshots, but the supplied ZIPs contain no `archive/` folder, no prototype raw observations and no Git history (`HANDOFF.md` describes `archive/`, `experiments/`, `numpy-experiment/`, root `README.md`). The paper elsewhere correctly says the raw prototype observations are "not in the examined package". | Either include those items in the submission or reword to "preserved in the authors' original project folder". | **[v2 update]** `archive/`, `experiments/`, `numpy-experiment/` and the prototype raw observations are now included (complete-transfer ZIP); the recommendation "include those items" is therefore satisfied by package v2. The paper's own sentence that the raw observations are "not in the examined package" remains true of the two archives it examined; if the v2 package is what is submitted, that sentence should be re-checked by the authors (the paper was not edited). Git history is still incomplete (ends 2026-10-29).
| 3 | low | Reference [17] cites the archive names and hashes but not that two folders (`results/final-roaring-20261105T225535Z` = pilot, `…T225902Z` = main) exist; reviewers may open the wrong one. | Optionally name the main folder in Sect. 4.3. |
| 4 | low | Header of `docs/UPGRADE_RESULTS.md` still says "verified 5 November 2026". | Documentation only; not changed. |

No contradiction was found between the paper's claims and the data for any quantity that could be checked; the statistical language of the paper (inconclusive first call; control within/inconclusive; "bounded explanation"; no pooling across environments) matches what the data support.
