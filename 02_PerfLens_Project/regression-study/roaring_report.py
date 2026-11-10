"""Compare the RoaringBitmap JFR recordings produced by extend.py diagnostics."""
import argparse
from collections import Counter
import json
from pathlib import Path
import re

WORKLOAD = "perflens.external.RankDiagnostic.main"


def profile(folder, revision, limit):
    stem = f"rank-{revision[:12]}-{limit}"
    log = json.loads((folder / f"{stem}.json").read_text())
    result_match = re.search(r'\{"valid":true,"operations":\d+,"checksum":-?\d+\}', log["stdout"])
    if not result_match:
        raise ValueError(f"Missing operation count in {stem}")
    result = json.loads(result_match[0])
    operations = result["operations"]
    events_log = json.loads((folder / f"{stem}-events.json").read_text())
    events = json.loads(events_log["stdout"])["recording"]["events"]
    methods, leaves = Counter(), Counter()
    total = 0
    for event in events:
        if event["type"] != "jdk.ExecutionSample":
            continue
        stack = event["values"].get("stackTrace") or {}
        frames = stack.get("frames") or []
        names = [
            f"{frame['method']['type']['name'].replace('/', '.')}.{frame['method']['name']}"
            for frame in frames
        ]
        if WORKLOAD not in names:
            continue
        total += 1
        methods.update(set(names) - {WORKLOAD})
        if names[0] != WORKLOAD:
            leaves[names[0], frames[0].get("lineNumber")] += 1
    return operations, total, methods, leaves


def compare_limit(folder, newer, older, limit):
    reference = profile(folder, newer, limit)
    candidate = profile(folder, older, limit)

    def stats(profile, samples):
        operations, total, _, _ = profile
        return {
            "samples": samples,
            "share_percent": round(100 * samples / total, 2) if total else None,
            "samples_per_million_calls": round(samples * 1e6 / operations, 3),
        }

    methods = []
    for name in reference[2].keys() | candidate[2].keys():
        before, after = stats(reference, reference[2][name]), stats(candidate, candidate[2][name])
        delta = after["samples_per_million_calls"] - before["samples_per_million_calls"]
        if delta > 0:
            lines = sorted(((line, count) for (method, line), count in candidate[3].items()
                            if method == name and line is not None and line > 0),
                           key=lambda entry: (-entry[1], entry[0]))
            methods.append({
                "method": name, "reference": before, "candidate": after,
                "added_samples_per_million_calls": round(delta, 3),
                "candidate_leaf_lines": [
                    {"line": line, "samples": count} for line, count in lines[:5]
                ],
            })
    methods.sort(key=lambda method: (-method["added_samples_per_million_calls"], method["method"]))
    return {
        "reference": {"revision": newer, "calls": reference[0], "workload_samples": reference[1]},
        "candidate": {"revision": older, "calls": candidate[0], "workload_samples": candidate[1]},
        "status": "profiled" if min(reference[1], candidate[1]) >= 20 else "sparse_profile",
        "candidates": methods[:10],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folder", type=Path, help="results/resume-diagnostics-*")
    args = parser.parse_args()
    folder = args.folder.resolve()
    older, newer = json.loads((folder / "plan.json").read_text())["shas"]
    report = {limit: compare_limit(folder, newer, older, limit) for limit in ("65535", "65534")}
    report["interpretation"] = (
        "Diagnostic recordings include warmup. Stack samples are inclusive and can overlap. "
        "Samples per million calls account for different call counts in the fixed-duration recordings. "
        "Use unprofiled JMH results for benchmark timings."
    )
    output = folder / "jfr-localization.json"
    output.write_text(json.dumps(report, indent=2) + "\n")
    print(output)


if __name__ == "__main__":
    main()
