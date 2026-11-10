"""Plot saved JMH comparisons using only the Python standard library."""
import argparse
import csv
from html import escape
import json
import math
from pathlib import Path
import re
import subprocess
import sys
from statistics import median

COLORS = ("#1565ac", "#b34c15")
WARMUP = re.compile(r"Warmup Iteration\s+\d+:\s+([\d.]+)\s+ns/op")


def plot_comparison(folder):
    with (folder / "raw.csv").open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    runtime = folder.name == "runtime"
    if runtime:
        key = "arm"
        labels = {"reference": "Default HotSpot", "candidate": "Tier 1"}
        title = "RoaringBitmap rank(65534) | JIT modes"
    else:
        key = "sha"
        revisions = json.loads((folder.parent / "measurement-plan.json").read_text())["shas"]
        labels = dict(zip(revisions, ("Before " + revisions[0][:7], "After " + revisions[1][:7])))
        title = "RoaringBitmap " + folder.name + " | default HotSpot"
    scores = {arm: sorted((int(row["round"]), float(row["seconds"]) * 1e9)
                          for row in rows if row[key] == arm) for arm in labels}
    warmups = {arm: [] for arm in labels}
    for log in sorted(folder.glob("*.command.json")):
        result = json.loads(log.read_text())
        if result["returncode"] != 0:
            continue
        args = result["command"]
        if runtime:
            arm = "candidate" if "-XX:TieredStopAtLevel=1" in args else "reference"
        else:
            # The matching JMH result filename contains the pair and arm order.
            _, pair, order = log.name.removesuffix(".json.command.json").split("-")
            arm = next(row[key] for row in rows if row["round"] == pair and row["order"] == order)
        values = [float(value) for value in WARMUP.findall(result["stdout"])]
        if values:
            warmups[arm].append(list(enumerate(values, 1)))

    svg = ['<svg xmlns="http://www.w3.org/2000/svg" width="960" height="400" viewBox="0 0 960 400">',
           '<rect width="960" height="400" fill="white"/>',
           '<g font-family="system-ui,sans-serif" fill="#203049">',
           f'<text x="60" y="32" font-size="23" font-weight="bold">{escape(title)}</text>',
           '<text x="60" y="56" font-size="13">Time in ns/op · lower is faster · one fresh JVM per arm and pair</text>']

    def panel(left, heading, xlabel, data, traces=None):
        top, width, height = 105, 365, 205
        all_lines = [line for lines in (traces or {}).values() for line in lines] + list(data.values())
        count = max((i for line in all_lines for i, _ in line), default=2)
        maximum = max((v for line in all_lines for _, v in line), default=1)
        magnitude = 10 ** math.floor(math.log10(maximum))
        step = magnitude / 2
        ceiling = math.ceil(maximum / step) * step

        def x(i):
            return left + width * (i - 1) / max(count - 1, 1)

        def y(v):
            return top + height * (1 - v / ceiling)

        svg.append(f'<text x="{left}" y="88" font-size="15" font-weight="bold">{heading}</text>')
        for i in range(5):
            tick = ceiling * i / 4
            svg.append(f'<path d="M{left} {y(tick):.2f}h{width}" stroke="#dce3ec"/>')
            svg.append(f'<text x="{left-7}" y="{y(tick)+4:.2f}" text-anchor="end" font-size="11">{tick:g}</text>')
        for i in range(1, count + 1):
            svg.append(f'<text x="{x(i):.2f}" y="327" text-anchor="middle" font-size="11">{i}</text>')
        svg.append(f'<text x="{left+width/2}" y="350" text-anchor="middle" font-size="13">{xlabel}</text>')
        for arm, color in zip(labels, COLORS):
            for line, opacity, stroke in [
                *((line, 0.18, 1) for line in (traces or {}).get(arm, [])),
                (data[arm], 1, 2.5),
            ]:
                points = " ".join(f"{x(i):.2f},{y(v):.2f}" for i, v in line)
                svg.append(f'<polyline points="{points}" fill="none" stroke="{color}" '
                           f'stroke-width="{stroke}" opacity="{opacity}"/>')
                if opacity == 1:
                    svg.extend(f'<circle cx="{x(i):.2f}" cy="{y(v):.2f}" r="3" fill="{color}"/>'
                               for i, v in line)

    warmup_medians = {
        arm: [(column[0][0], median(v for _, v in column)) for column in zip(*lines)]
        for arm, lines in warmups.items()
    }
    panel(60, "Warmup across JVMs", "JMH warmup iteration", warmup_medians, warmups)
    panel(550, "Measured score after warmup", "Paired run", scores)
    for i, (label, color) in enumerate(zip(labels.values(), COLORS)):
        svg.append(f'<text x="{60 + 220*i}" y="380" fill="{color}" font-size="14">{escape(label)}</text>')
    svg.append('<text x="550" y="380" font-size="12">Faint lines show individual JVM warmup traces</text>')
    svg.append("</g></svg>")
    (folder / "jmh-comparison.svg").write_text("\n".join(svg), encoding="utf-8")


def run_revision_measurement():
    from tempfile import mkdtemp
    from unittest.mock import patch

    import reproduce

    state = reproduce.load()
    folder = Path(mkdtemp(prefix="upgrade-java-measure-", dir=reproduce.ROOT / "results"))
    print(f"New measurement folder: {folder}", flush=True)
    # Redirect only this invocation. The prepared state and its hash checks stay intact.
    with patch.object(reproduce, "load", return_value={**state, "folder": str(folder)}):
        reproduce.measure()
    return sorted(path.parent for path in folder.glob("*/summary.json"))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folders", nargs="*", type=Path)
    runs = parser.add_mutually_exclusive_group()
    runs.add_argument("--run-measure", action="store_true",
                      help="measure both revisions in a new folder and plot the results")
    runs.add_argument("--run-runtime", action="store_true",
                        help="run the runtime comparison and plot its results")
    args = parser.parse_args()
    if args.run_runtime:
        runner = Path(__file__).with_name("extend.py")
        process = subprocess.Popen(
            [sys.executable, "-B", str(runner), "interventions", "--case", "runtime"],
            stdout=subprocess.PIPE, text=True,
        )
        last_line = ""
        with process.stdout:
            for line in process.stdout:
                print(line, end="", flush=True)
                if line.strip():
                    last_line = line.strip()
        if process.wait():
            raise SystemExit(process.returncode)
        if not last_line:
            parser.error("runtime runner did not report a result folder")
        args.folders.append(Path(last_line) / "runtime")
    if args.run_measure:
        args.folders.extend(run_revision_measurement())
    if not args.folders:
        parser.error("provide result folders, --run-measure, or --run-runtime")
    for folder in args.folders:
        plot_comparison(folder)
