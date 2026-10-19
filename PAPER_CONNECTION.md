# How this implementation relates to our paper

Source: `ASE_project (1).pdf`, Preliminary Research Direction, 5 October 2026,
8 PDF pages. The document describes research ideas, not executable Python code.
The implementation was written for this prototype; do not describe it as code copied
from the paper. Disclose development assistance according to the course rules.

| Paper concept | Location | Implementation |
|---|---|---|
| Same workload across software versions | Section 2.1, page 2; section 4, page 6 | One NetworkX graph and algorithm, two Git commits |
| Repeated measurements | Sections 2.1-2.2, pages 2-3 | Configurable paired rounds in run.py |
| Warmup, caching and measurement settings | Section 2.2, page 3 | Untimed warmups, fixed batch size, fresh processes |
| Mean performance | Section 2.3, equation (5), page 4 | statistics.mean in analyze.py |
| Median, standard deviation, variance | Section 2.3, page 4 | Descriptive summaries in analyze.py |
| Relative change of means | Section 2.3, equation (6), page 4 | (new_mean / old_mean - 1) x 100 |
| Confidence intervals and bootstrap as possible approaches | Section 2.3, page 4 | Approximate 95% paired percentile bootstrap CI |
| Statistical and practical significance are different | Section 2.3, pages 4-5 | CI versus zero separately from CI versus practical threshold |
| Git history to benchmark to analysis | Section 2.4, page 5; section 4, page 6 | run.py -> benchmark.py -> analyze.py |

## Choices made by us, not prescribed by the paper

- NetworkX: supported by the comparison in Selections.pdf, pages 1-2.
- A square grid and single-source shortest paths: our concrete workload.
- The default two SHAs: a technical pilot pair, not a known performance bug.
- Defaults of 20 rounds, 100 calls, three warmups and a 35 x 35 grid.
- A practical threshold of 5%; this is configurable and must be chosen in advance.
- Random ordering within paired rounds and a fresh process for each observation.
- Paired percentile bootstrap of the ratio of means, 5000 resamples, 95% confidence.
  The paper mentions bootstrap, but does not specify these details or prove coverage.
- CV, CSV/JSON/Markdown output, unique experiment folders and source snapshots.
- Python's argparse, subprocess, time, csv, random and statistics modules.

NetworkX supplies the graph algorithm; we supply measurement and comparison code.
We use confidence intervals as the inferential method. We do not also implement
t-tests or Mann-Whitney tests merely because the paper lists them as alternatives.
No p-value is computed. There is no claim of multiple-testing control.

## Why paired rounds?

Each round observes both versions close in time. The random order avoids always
giving one version the earlier slot. Resampling whole rounds retains this pairing.
Our effect remains the relative change of means, matching the paper's equation.
This design does not establish independent rounds or remove all machine noise.

## What is still needed for the full research question?

ASE Lab3.pdf, page 4, asks how reliably regressions can be detected. An implementation
and one real-history run do not answer that fully. Evaluate known unchanged cases,
known injected slowdowns and independent confirmation runs; report false positives,
detection rates, inconclusive results and experiment cost. Test more workloads.

ASE Lab3.pdf, page 14, discusses allocating repetitions using observed variability.
The configurable repetition count is a starting point, not an adaptive procedure.
Use a separate pilot to choose a fixed evaluation budget. Avoid repeated peeking
and stopping as soon as the desired result appears.

## Technical references

- Python timer documentation: https://docs.python.org/3/library/time.html#time.perf_counter
- Bootstrap concepts, pairing and percentile method: https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.bootstrap.html

The SciPy page is a methodological reference, not a dependency. Our small standard-library
implementation uses a percentile interval; it does not implement SciPy's default BCa method.
