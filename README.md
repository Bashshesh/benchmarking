# NetworkX performance comparison

A small research prototype that compares the same graph algorithm at two Git commits.
Python 3.11+ and Git are required. No pip dependencies are required for this workload.

## Start here

Open this folder in VS Code, then open Terminal > New Terminal:

```powershell
python run.py --commits 87b57851e9 6da4704cbf --repeats 20
```

This is a real pair of adjacent NetworkX commits from our pilot, not a known regression.
Results can legitimately show no meaningful difference. Short SHAs, full SHAs and tags
are accepted. Pass exactly two distinct revisions, old first; the old revision must be
an ancestor of the new one. Git resolves and saves the full SHAs before measurement.

For a longer experiment:

```powershell
python run.py --commits 87b57851e9 6da4704cbf --repeats 30 --loops 200 --warmups 5 --threshold 5
```

Or simply `python run.py` to use the pilot pair and default settings.
Use `py` instead of `python` if that is how Python is installed on your machine.
First execution clones NetworkX; later executions reuse `networkx_repo`.
Never edit the downloaded repository during a run. The runner refuses a dirty checkout
and restores the original Git branch or detached HEAD when measurements finish or fail.
Do not run two experiments simultaneously in this folder.

To choose other commits, inspect the history:

```powershell
git -C networkx_repo log -15 --oneline --first-parent
```

Fetch newer history if necessary: `git -C networkx_repo fetch origin`.
Historical versions must support your Python version and the workload's API.

## Three main files

| File | Responsibility |
|---|---|
| **benchmark.py** | The actual benchmark: input graph, warmups, timed calls, result check |
| **run.py** | Command-line settings, Git checkout, randomized rounds, fresh processes, CSV and metadata |
| **analyze.py** | Descriptive statistics, bootstrap confidence interval, decision, Markdown report |

Read benchmark.py first. Its `measure()` function is the core of the experiment.
The main program runs it automatically; it is not necessary to launch it yourself.
`test_analysis.py` checks analysis behavior and rejects incomplete data.

## Settings

| Option | Default | Meaning |
|---|---:|---|
| `--commits OLD NEW` | Pilot pair | Two revisions to compare |
| `--repeats` | 20 | Number of paired rounds; at least 5 |
| `--loops` | 100 | Algorithm calls inside one timing observation |
| `--warmups` | 3 | Untimed calls before each observation |
| `--size` | 35 | Square grid side length (35 x 35 = 1225 nodes) |
| `--threshold` | 5 | Practical threshold in percent, chosen before measuring |
| `--seed` | 42 | Reproducible random order and bootstrap draws |

See all options: `python run.py --help`.
Five rounds are allowed for smoke testing, not recommended for research conclusions.
Twenty is a starting budget, not a proven optimal count. Inspect pilot variation and
choose the repetition budget before the main experiment. Do not stop when a desired result appears.

## Measurement, step by step

For every round, run both commits in a randomly shuffled order. Each observation
uses a new Python process, so the previous revision cannot remain imported in memory.

1. Check out the selected commit in our dedicated `networkx_repo` clone.
2. Import NetworkX from that checkout and verify the import path.
3. Create a deterministic square grid with `nx.grid_2d_graph`.
4. Warm up `nx.single_source_shortest_path_length` from node `(0, 0)`.
5. Read `perf_counter()`, call the algorithm `loops` times, read the timer again.
6. Divide elapsed time by `loops` and save one observation.
7. Verify the number of reachable nodes and the distance to the opposite corner.

Imports, Git, graph creation, warmups, validation and file output are outside the timer.
The loop and result assignment are inside it. GC stays enabled. PYTHONHASHSEED is 0.
With 20 repeats, two commits produce 40 observations, NOT 4000 independent observations.
Each observation is a batch average. Timings are stored in seconds and displayed in ms.

## Analysis: more than a threshold

For each commit, calculate mean, median, sample SD, sample variance and coefficient
of variation (CV = SD / mean x 100). Variance is included in summary.json.

The main effect uses our paper's formula:

`change (%) = (mean_new - mean_old) / mean_old * 100`

To quantify uncertainty, resample complete old/new rounds with replacement 5000 times.
Recompute that same mean-change statistic for each resample. The 2.5th and 97.5th
percentiles form an approximate 95% percentile bootstrap confidence interval.
Keeping each pair together preserves the within-round pairing; rounds themselves
are assumed sufficiently independent. The code uses the Python standard library,
not SciPy. This is a chosen method, not a claim that the paper mandated this variant.

The report answers two separate questions:

1. **Statistical direction:** CI entirely above zero -> slower; entirely below zero
   -> faster; otherwise uncertain. This is an interval-based assessment, not a p-value.
2. **Practical decision:** compare the entire interval with the chosen threshold.

| Decision | Rule for a 5% threshold |
|---|---|
| `regression` | CI lower endpoint > +5% |
| `improvement` | CI upper endpoint < -5% |
| `within_threshold` | Entire CI inside [-5%, +5%] |
| `inconclusive` | None of the above |

A statistically detectable +1% change can still be practically small. A +10% point
estimate with a very wide interval can still be inconclusive. Within-threshold does
not prove that two versions are identical. The threshold is an engineering choice.

## Saved experiments

Each run creates a NEW folder under `experiments/`, named with a UTC timestamp:

```text
experiments/<timestamp>/
    raw.csv          All observations, round, execution order, version and commit
    metadata.json    Settings, full SHAs, Python/OS, workload hash, completion status
    summary.json     Descriptive statistics and comparison results
    report.md        Human-readable report for VS Code or your team
    run.py           Source snapshot for provenance
    benchmark.py     Source snapshot for provenance
    analyze.py       Source snapshot for provenance
```

Open report.md in VS Code; Ctrl+Shift+V shows Markdown preview. No browser is required.
Previous runs are not overwritten. A failed run retains CSV, status and error but
does not generate a statistical conclusion. Analysis verifies every expected round.
Source snapshots are reference copies; run the project from its root folder.

Reanalyze the latest completed experiment without measuring again:

```powershell
python analyze.py
```

Or specify a saved folder: `python analyze.py experiments/<actual-folder-name>`.
Replace the placeholder with a real directory name from your experiments folder.
Reanalysis updates the summary and report, not the raw timings.

## Demonstration and limitations

Use AC power, keep the machine quiet, and finish tests before benchmarking:

```powershell
python -m unittest -v test_analysis.py
```

Explain the workload, show raw.csv, then show mean change and its interval in report.md.
The aim is a reproducible comparison; finding a regression is not required for success.
Do not select only runs with interesting outcomes.

Randomized rounds reduce ordering bias but do not eliminate CPU frequency changes,
thermal effects, scheduling noise or correlation between rounds. Bootstrap intervals
are approximate and their coverage is not empirically validated here. No correction
for searching many pairs is implemented; confirm flags in a separate preplanned run.
This workload covers one algorithm and one input; conclusions do not describe all of
NetworkX. We do not install per-revision dependencies, measure memory, or test other libraries.

See PAPER_CONNECTION.md for the exact distinction between paper concepts and our choices.
