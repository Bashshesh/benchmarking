"""Compare two SearchBench profiles and rank methods with extra CPU samples."""
import argparse
from collections import Counter
from datetime import datetime
import json
from pathlib import Path
import random
import re
import subprocess
import tempfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def capture(command):
    return subprocess.check_output(command, text=True, timeout=120)


def sample_methods(jfr, path):
    result = json.loads(capture([str(jfr), "print", "--json", "--events",
                                 "jdk.ExecutionSample", "--stack-depth", "64", str(path)]))
    counts = Counter()
    leaf_lines = Counter()
    total = 0
    for event in result["recording"]["events"]:
        stack = event["values"].get("stackTrace") or {}
        frames = stack.get("frames", [])
        methods = []
        for frame in frames:
            method = frame["method"]
            owner = method["type"]["name"].replace("/", ".")
            methods.append(f"{owner}.{method['name']}")
        if "RegressionProbe.run" not in methods:
            continue
        total += 1
        if methods and not methods[0].startswith("RegressionProbe."):
            leaf_lines[(methods[0], frames[0].get("lineNumber"))] += 1
        # Inclusive samples, once per method per stack, excluding the harness.
        counts.update({method for method in methods if not method.startswith("RegressionProbe.")})
    return total, counts, leaf_lines


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=HERE / "search-regression.json")
    parser.add_argument("--project", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    config = json.loads(args.config.read_text())
    project = args.project.resolve()
    arms = ("reference", "candidate")
    keys = ("size", "queries", "warmup_rounds", "measurement_rounds")
    if (any(config[arm] not in {"baseline", "optimized"} for arm in arms)
            or any(type(config[key]) is not int or config[key] < 1 for key in keys)
            or config["size"] < 2):
        parser.error("Invalid workload or round count")
    out = (args.output or project / "results" /
           f"regression-jfr-{datetime.now():%Y%m%d-%H%M%S-%f}").resolve()
    out.mkdir(parents=True, exist_ok=False)
    java = subprocess.run(["java", "-XshowSettings:properties", "-version"],
                          capture_output=True, text=True, check=True).stderr
    java_home = re.search(r"^\s*java\.home\s*=\s*(.+)$", java, re.MULTILINE)
    if not java_home:
        raise RuntimeError("Cannot locate the active JDK")
    jdk_bin = Path(java_home[1].strip()) / "bin"
    (out / "config.json").write_text(json.dumps(config, indent=2) + "\n")
    (out / "java.txt").write_text(java)
    profiles = {}
    with tempfile.TemporaryDirectory(prefix="perflens-regression-") as build:
        subprocess.run([str(jdk_bin / "javac"), "-d", build,
                        str(project / "workloads/SearchBench.java"),
                        str(HERE / "RegressionProbe.java")], check=True)
        for arm in random.Random(42).sample(arms, len(arms)):
            recording = out / f"{arm}.jfr"
            command = [str(jdk_bin / "java"), "-cp", build, "RegressionProbe",
                       config[arm], *(str(config[key]) for key in keys), str(recording)]
            seconds = float(capture(command).strip())
            total, methods, lines = sample_methods(jdk_bin / "jfr", recording)
            profiles[arm] = (seconds, total, methods, lines)

    before, after = (profiles[arm] for arm in arms)
    candidates = []
    for method in sorted(before[2].keys() | after[2].keys()):
        reference, candidate = before[2][method], after[2][method]
        if candidate <= reference:
            continue
        lines = sorted(
            {line for counts in (before[3], after[3]) for owner, line in counts
             if owner == method and line is not None and line > 0},
            key=lambda line: (-after[3][method, line] + before[3][method, line], line),
        )
        candidates.append({
            "method": method,
            "reference_stack_samples": reference,
            "candidate_stack_samples": candidate,
            "added_stack_samples": candidate - reference,
            "candidate_share_percent": round(100 * candidate / after[1], 1),
            "directly_sampled_lines": [
                {"line": line, "reference_samples": before[3][method, line],
                 "candidate_samples": after[3][method, line]}
                for line in lines[:5]
            ],
        })
    candidates.sort(key=lambda row: -row["added_stack_samples"])
    report = {
        "profiled_seconds_per_round": {arm: profiles[arm][0] for arm in arms},
        "profiled_candidate_to_reference_time_ratio": after[0] / before[0],
        "workload_samples": {arm: profiles[arm][1] for arm in arms},
        "profile_status": (
            "insufficient_samples" if after[1] < 20 else
            "candidates_found" if candidates else "no_added_samples"
        ),
        "candidates": candidates[:10] if after[1] >= 20 else [],
        "interpretation": "Inclusive stack samples overlap across methods. Leaf lines show "
                          "where sampling observed execution. Timings include profiling overhead.",
    }
    (out / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    print(out)


if __name__ == "__main__":
    main()
