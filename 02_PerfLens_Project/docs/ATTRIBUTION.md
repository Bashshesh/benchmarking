# Original work and development attribution

The supplied paper, **An Empirical Study of Performance Regressions in NetworkX** (19 October 2026), credits **Ansar Bashayev, Thanh Tra Nguyen, and Dasol Jung**, HAW Kiel. The supplied presentation identifies Team 3 and the same contributors. The recovered prototype Git history contains baseline commit `a5a086bf2c62572a9562f4d03de85f0e098fde41`, author display name `Bashshesh`. Git metadata is evidence of the supplied repository, not independent proof of who wrote each file.

The supplied `misc.zip`, paper, presentation and course PDFs are copied byte-for-byte into `archive/`, with SHA-256 hashes in `archive/SHA256.json`. The unchanged extracted project is under `original/misc/`; `audit_original.py` checks it against ZIP members. The original Git history is retained in the working folder and inside the archived ZIP. Historical results remain in their original directories, separate from new evaluation data.

Original contributions retained include `run.py`, `benchmark.py`, `analyze.py`, `test_analysis.py`, `PAPER_CONNECTION.md`, the initial `results.csv`, the two NetworkX experiment folders and the nested NumPy prototype/three experiments. Root `README.md` is expanded for PerfLens; its original is preserved in `original/misc/README.md`. Original analyzer and workload sources remain byte-identical. New runner code imports `compare` and `descriptive` directly from the original analyzer.

The new PerfLens runner, graph-query optimization case, Java demonstration, tests, configurations, measurements, analysis and documentation were developed with OpenAI Codex assistance in this chat on 29 October 2026. Scientific sources are credited in `LITERATURE.md`. This statement is a development-assistance disclosure; the student must check and comply with the course's required citation format and institutional policy. The course guidelines explicitly require citation of ChatGPT and other text generators.

The previous research is not represented as newly authored work. New experiments are extensions, not evidence that all historical claims or cited papers have been independently replicated. No guarantee of a passing grade or completion of peer reviews, tests or colloquium obligations is made.

NetworkX is third-party software under its supplied license (`networkx_repo/LICENSE.txt`). NumPy, OpenJDK and Python dependencies retain their respective licenses. No new license is assigned to the original seminar materials; they are retained for the requested project hand-off, not published publicly.
