"""Compare within-process warmup using PerfLens SearchBench and CPython."""
import argparse
import csv
from datetime import datetime
import json
from pathlib import Path
import platform
import random
import statistics
import subprocess
import sys
import tempfile
from time import perf_counter_ns

MODES = ("Java HotSpot", "Java -Xint", "CPython")
JAVA_FLAGS = {
    "Java HotSpot": (),
    "Java Tier 1": ("-XX:TieredStopAtLevel=1",),
    "Java -Xint": ("-Xint",),
}


def python_trace(size, query_count, rounds):
    values = [2 * index for index in range(size)]
    queries = [(index * 7919) % (2 * size) for index in range(query_count)]
    expected = sum(query % 2 == 0 for query in queries)

    def search():
        found = 0
        for query in queries:
            low, high = 0, size - 1
            while low <= high:
                middle = (low + high) // 2
                value = values[middle]
                if value < query:
                    low = middle + 1
                elif value > query:
                    high = middle - 1
                else:
                    found += 1
                    break
        return found

    times = []
    for _ in range(rounds):
        start = perf_counter_ns()
        checksum = search()
        times.append((perf_counter_ns() - start) / 1e9)
        if checksum != expected:
            raise RuntimeError("Incorrect Python checksum")
    return {"warmup_seconds": times, "checksum": checksum, "valid": True}


def plot(path, traces, rounds, processes, smoke, reference_window, focus_round):
    colors = ("#1664ad", "#b34f16", "#087653")
    curves = {}
    for mode, samples in traces.items():
        baselines = [
            statistics.median(row[-reference_window:]) if reference_window else row[0]
            for row in samples
        ]
        normalized = [[value / baseline for value in row]
                      for row, baseline in zip(samples, baselines)]
        curves[mode] = [
            statistics.median(row[index] for row in normalized)
            for index in range(rounds)
        ]

    x0, y0, width, height = 80, 90, 680, 310
    maximum = max(1.1, max(max(curve) for curve in curves.values())) * 1.05

    def y(value):
        return y0 + height * (1 - value / maximum)

    reference = (f"median of last {reference_window} rounds = 1.0"
                 if reference_window else "first round = 1.0")
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="800" height="510" viewBox="0 0 800 510">',
        '<rect width="800" height="510" fill="white"/>',
        '<g font-family="system-ui, sans-serif" fill="#17283b">',
        '<text x="80" y="33" font-size="24" font-weight="bold">Binary search warmup</text>',
        f'<text x="80" y="60" font-size="14">{"SMOKE TEST | " if smoke else ""}'
        f'Median of {processes} fresh processes per mode | {reference}</text>',
    ]
    step = max(1, round(maximum / 5)) if reference_window else 0.5
    ticks = {0, 1, *(step * i for i in range(1, int(maximum / step) + 1))}
    for value in sorted(ticks):
        parts.append(f'<path d="M{x0} {y(value):.2f}h{width}" stroke="#dbe1e8"/>')
        parts.append(f'<text x="66" y="{y(value)+4:.2f}" text-anchor="end" font-size="12">{value:.1f}</text>')
    for index in sorted({1, rounds, *range(10, rounds, 10)}):
        x = x0 + width * (index - 1) / (rounds - 1)
        parts.append(f'<text x="{x:.1f}" y="420" text-anchor="middle" font-size="12">{index}</text>')
    if focus_round and focus_round <= rounds:
        x = x0 + width * (focus_round - 1) / (rounds - 1)
        parts.append(f'<path d="M{x:.1f} {y0}v{height}" stroke="#52647a" stroke-dasharray="5 4"/>')
        parts.append(f'<text x="{x:.1f}" y="82" text-anchor="middle" font-size="12">Round {focus_round}</text>')
    for index, (mode, color) in enumerate(zip(traces, colors)):
        points = " ".join(
            f"{x0 + width * i / (rounds - 1):.2f},{y(value):.2f}"
            for i, value in enumerate(curves[mode])
        )
        parts.append(f'<polyline points="{points}" stroke="{color}" stroke-width="3" fill="none"/>')
        parts.append(f'<text x="{80 + 220 * index}" y="480" font-size="16" fill="{color}">{mode}</text>')
    parts.extend([
        '<text x="420" y="445" text-anchor="middle" font-size="14">Round within the same process</text>',
        '<text x="21" y="245" transform="rotate(-90 21 245)" text-anchor="middle" font-size="14">Relative time</text>',
        '</g></svg>',
    ])
    path.write_text("\n".join(parts), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()
    config = json.loads(args.config.read_text())
    if args.smoke:
        config.update(rounds=12, processes_per_mode=2)
    size = config["array_size"]
    queries = config["queries_per_round"]
    rounds = config["rounds"]
    processes = config["processes_per_mode"]
    modes = config.get("modes", MODES)
    reference_window = config.get("reference_window", 0)
    focus_round = config.get("focus_round")
    if args.smoke and reference_window:
        reference_window = min(reference_window, rounds // 2)
        config["reference_window"] = reference_window
        if focus_round and focus_round > rounds:
            focus_round = None
            config.pop("focus_round")
    if (not 1 <= len(modes) <= 3 or len(set(modes)) != len(modes)
            or any(mode not in JAVA_FLAGS and mode != "CPython" for mode in modes)
            or not 0 <= reference_window <= rounds
            or (focus_round is not None and not 1 <= focus_round <= rounds)):
        parser.error("Invalid modes, reference window, or focus round")
    source = args.project / "workloads" / "SearchBench.java"
    output = args.output or Path(f"warmup-{datetime.now():%Y%m%d-%H%M%S}")
    output.mkdir(parents=True, exist_ok=False)
    traces = {mode: [] for mode in modes}
    rng = random.Random(config["seed"])
    metadata = {
        "config": config,
        "smoke": args.smoke,
        "platform": platform.platform(),
        "python": sys.version,
        "python_implementation": platform.python_implementation(),
        "java": subprocess.check_output(["java", "-version"], stderr=subprocess.STDOUT, text=True).strip(),
    }
    (output / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")

    expected = sum((index * 7919) % (2 * size) % 2 == 0 for index in range(queries))
    with tempfile.TemporaryDirectory(prefix="perflens-warmup-") as build:
        subprocess.run(["javac", "-d", build, str(source)], check=True)
        with (output / "rounds.csv").open("w", newline="") as stream:
            writer = csv.writer(stream)
            writer.writerow(["mode", "process", "round", "seconds", "checksum"])
            for trial in range(1, processes + 1):
                order = list(modes)
                rng.shuffle(order)
                for mode in order:
                    if mode == "CPython":
                        command = [sys.executable, "-B", str(Path(__file__).resolve()),
                                   "_worker", str(size), str(queries), str(rounds)]
                    else:
                        flags = JAVA_FLAGS[mode]
                        command = ["java", *flags, "-cp", build, "SearchBench",
                                   "optimized", str(size), str(queries), "1", str(rounds)]
                    data = json.loads(subprocess.check_output(command, text=True, timeout=120))
                    times = data["warmup_seconds"]
                    if (not data["valid"] or data["checksum"] != expected
                            or len(times) != rounds or any(value <= 0 for value in times)):
                        raise RuntimeError(f"Invalid result for {mode}, process {trial}")
                    traces[mode].append(times)
                    writer.writerows((mode, trial, index, value, expected)
                                     for index, value in enumerate(times, 1))
                    stream.flush()
                    print(f"{mode}: {trial}/{processes}", flush=True)
    plot(output / "warmup.svg", traces, rounds, processes, args.smoke,
         reference_window, focus_round)
    if focus_round:
        for mode, samples in traces.items():
            ratios = [row[focus_round - 1] /
                      (statistics.median(row[-reference_window:]) if reference_window else row[0])
                      for row in samples]
            print(f"{mode}: round {focus_round} = {statistics.median(ratios):.2f}x; "
                  f"over 2x in {sum(ratio > 2 for ratio in ratios)}/{processes} JVMs")
    print(output.resolve())


if __name__ == "__main__":
    if sys.argv[1:2] == ["_worker"]:
        print(json.dumps(python_trace(*map(int, sys.argv[2:]))))
    else:
        main()
