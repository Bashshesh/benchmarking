"""Two final PR845 experiments using the existing pinned image and source cache."""
import argparse
import csv
import json
import math
from pathlib import Path
import random
import shlex
import shutil
import statistics
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from analyze import compare
from upgrade.java.reproduce import SHAS, digest, load, write
from upgrade.java.extend import run
from upgrade.metrics import jmh_single_fork

LAZY = {"cached": "cached", "first": "first", "repeat": "repeat"}
CORE = {"rank-max": ("rank", 65535), "rank-near": ("rank", 65534),
        "range": ("fullContainerRange", 65535)}
ROUNDS = 10
LAZY_NAME = "perflens.finalstudy.LazyRank.rankBatch"


def artifacts(folder, sha):
    return ROOT / ".tmp" / "final845" / folder.name / sha[:12]


def prepare(folder):
    folder.mkdir(parents=True)
    state = load()
    prior = json.loads((ROOT / "results/resume-validation-20261105-final/source-provenance.json").read_text())
    write(folder / "plan.json", dict(shas=SHAS, image=state["image_id"], rounds=ROUNDS,
          lazy=dict(mode="ss", shots_per_fork=20, warmup_shots=30, batch_rank_calls=256,
                    fixtures=16, untimed_batch_preheat=16000, fresh_objects_per_shot=True, seed=84590),
          native=dict(mode="avgt", settings="3x200ms warmup, 3x300ms measurement, 512m heap",
                      seed=84591, jmh="1.37"),
          statistics="paired bootstrap 5000 resamples, +/-5% practical threshold, fork means"))
    if prior["artifact_image"] != state["image_id"]:
        raise ValueError("Pinned image differs from the previously verified image")
    for sha in SHAS:
        out = artifacts(folder, sha)
        out.mkdir(parents=True)
        source = state["sources"][sha]
        for name, expected in source["source_sha256"].items():
            if digest(Path(source["directory"]) / name) != expected:
                raise ValueError("Source hash mismatch: " + name)
        for name in ("LazyRank.java", "DeniedProbe.java"):
            shutil.copy2(Path(__file__).with_name(name), out / name)
        repairs = str(sha == SHAS[1]).lower()
        script = (
            "sh /harness/build-roaring.sh && mkdir /out/deps /out/lazy /out/probe && "
            "cp /opt/jmh/*.jar /out/deps/ && cp=$(cat /out/classpath.txt) && "
            "javac -cp \"$cp\" -processorpath \"$cp\" "
            "-processor org.openjdk.jmh.generators.BenchmarkProcessor "
            "-d /out/lazy /out/LazyRank.java && "
            "javac -proc:none -d /out/probe /out/DeniedProbe.java && "
            "java -cp \"/out/lazy:$cp\" perflens.finalstudy.LazyRank " + repairs +
            " && sha256sum /out/library/org/roaringbitmap/BitmapContainer.class /out/deps/*.jar"
        )
        receipt = folder / (sha[:12] + "-docker-build.json")
        stdout = run(state, sha, out, ["sh", "-ec", script], receipt)
        if '"checksum":458211' not in stdout or "valid: 16 independent membership counts" not in stdout:
            raise ValueError("Missing correctness evidence")
        library_class = out / "library/org/roaringbitmap/BitmapContainer.class"
        if digest(library_class) != prior["library_BitmapContainer_class_sha256"][sha]:
            raise ValueError("Rebuilt target class differs from verified original")
        for jar in (out / "deps").glob("*.jar"):
            if digest(jar) + "  /out/deps/" + jar.name not in stdout:
                raise ValueError("Dependency verification failed")
        hashes = {p.relative_to(out).as_posix(): digest(p) for p in out.rglob("*") if p.is_file()}
        write(folder / (sha[:12] + "-artifact-hashes.json"), hashes)
    write(folder / "prepared.json", dict(status="both Docker builds and oracles passed"))


def benchmark_args(name, params, lazy, output):
    schedule = ["-bm", "ss", "-wi", "30", "-i", "20", "-wbs", "1", "-bs", "1"] if lazy else [
        "-bm", "avgt", "-wi", "3", "-i", "3", "-w", "200ms", "-r", "300ms"]
    return [name, "-f", "1", "-t", "1", "-foe", "true", *schedule,
            *[item for param in params for item in ("-p", param)],
            "-rf", "json", "-rff", output]


def prepare_native_guard(folder):
    out = artifacts(folder, SHAS[0])
    target = out / "native-guard"
    target.mkdir()
    source = Path(__file__).with_name("LoopbackGuard.java")
    shutil.copy2(source, out / source.name)
    run(load(), SHAS[0], out, ["javac", "-proc:none", "-d", "/out/native-guard",
                              "/out/LoopbackGuard.java"], folder / "native-guard-build.json")
    write(folder / "native-guard-hashes.json", {
        p.relative_to(out).as_posix(): digest(p) for p in [out / source.name, *target.rglob("*.class")]})


def paired_schedule(workloads, seed):
    rng = random.Random(seed)
    order = []
    for round_number in range(1, ROUNDS + 1):
        shas = SHAS.copy()
        rng.shuffle(shas)
        cases = list(workloads)
        rng.shuffle(cases)
        order.append(dict(round=round_number, shas=shas, workloads=cases))
    return order


def lazy_measure(folder):
    state = load()
    target = folder / "docker-lazy"
    target.mkdir()
    order = paired_schedule(LAZY, 84590)
    write(target / "schedule.json", order)
    for pair in order:
        for sha in pair["shas"]:
            out = artifacts(folder, sha)
            repairs = str(sha == SHAS[1]).lower()
            jobs = []
            cp = "/out/lazy:" + (out / "classpath.txt").read_text().strip()
            for scenario in pair["workloads"]:
                filename = f"r{pair['round']:02d}-{sha[:12]}-{scenario}.json"
                args = benchmark_args(LAZY_NAME, ["scenario=" + scenario, "repairs=" + repairs],
                                      True, "/out/" + filename)
                jobs.append((filename, shlex.join(["java", "-Xms512m", "-Xmx512m", "-cp", cp,
                                                  "org.openjdk.jmh.Main", *args])))
            group = f"r{pair['round']:02d}-{sha[:12]}-commands.json"
            try:
                run(state, sha, out, ["sh", "-ec", "\n".join(line for _, line in jobs)], target / group)
            finally:
                for filename, line in jobs:
                    if (out / filename).exists():
                        shutil.copy2(out / filename, target / filename)
                        write(target / (filename + ".command.json"), dict(receipt=group, invocation=line))
                        print(filename, flush=True)
    analyze(target, True)


def fork_score(path, workload, sha, lazy):
    record = json.loads(path.read_text())
    if len(record) != 1:
        raise ValueError("Expected exactly one benchmark per JVM fork")
    value = record[0]
    if value["jmhVersion"] != "1.37" or value["forks"] != 1 or value["threads"] != 1:
        raise ValueError("Unexpected JMH setup")
    metric = value["primaryMetric"]
    raw = metric["rawData"]
    expected_iterations = 20 if lazy else 3
    if len(raw) != 1 or len(raw[0]) != expected_iterations or not all(
            math.isfinite(x) and x > 0 for x in raw[0]):
        raise ValueError("Invalid retained JMH iteration values")
    if not math.isclose(metric["score"], statistics.mean(raw[0]), rel_tol=1e-12):
        raise ValueError("Fork mean differs from its iterations")
    if lazy:
        expected = {"scenario": workload, "repairs": str(sha == SHAS[1]).lower()}
        if (value["mode"], value["benchmark"], value["params"], value["warmupIterations"],
                value["measurementBatchSize"], metric["scoreUnit"]) != (
                "ss", LAZY_NAME, expected, 30, 1, "ns/op"):
            raise ValueError("Unexpected lazy benchmark metadata")
        return metric["score"] * 1e-9
    method, limit = CORE[workload]
    if (value["benchmark"], value["params"], value["warmupIterations"],
            value["warmupTime"], value["measurementTime"]) != (
            "perflens.external.RankBenchmark." + method, {"containers":"16","limit":str(limit)},
            3, "200 ms", "300 ms"):
        raise ValueError("Unexpected native benchmark metadata")
    native_environment = json.loads((path.parent / "environment.json").read_text())
    if (value["jvmArgs"] != native_environment["flags"] or
            "-Djava.security.manager=perflens.finalstudy.LoopbackGuard" not in value["jvmArgs"]):
        raise ValueError("Native fork flags differ from the recorded restricted environment")
    return jmh_single_fork(record)["seconds"]


def analyze(target, lazy, verify=False):
    schedule = json.loads((target / "schedule.json").read_text())
    cases = LAZY if lazy else CORE
    if schedule != paired_schedule(cases, 84590 if lazy else 84591):
        raise ValueError("Schedule differs from the planned randomized paired rounds")
    series = {(sha, case): [] for sha in SHAS for case in cases}
    rows = []
    for pair in schedule:
        for sha in pair["shas"]:
            for case in pair["workloads"]:
                name = f"r{pair['round']:02d}-{sha[:12]}-{case}.json"
                path = target / name
                receipt = json.loads((target / (name + ".command.json")).read_text())
                if lazy:
                    receipt = json.loads((target / receipt["receipt"]).read_text())
                if receipt["returncode"] != 0:
                    raise ValueError("Unsuccessful fork command")
                score = fork_score(path, case, sha, lazy)
                series[sha, case].append(score)
                rows.append(dict(round=pair["round"], sha=sha, case=case,
                                 seconds_per_operation=score, raw=name, sha256=digest(path)))
    effects = {}
    for case in cases:
        effects[case] = effect(series[SHAS[0], case], series[SHAS[1], case])
    if lazy:
        for sha in SHAS:
            for reference, candidate in [("cached", "first"), ("first", "repeat"), ("cached", "repeat")]:
                effects[f"{sha[:12]}:{candidate}/{reference}"] = effect(
                    series[sha, reference], series[sha, candidate])
    summary = dict(pairs=ROUNDS, forks=len(rows), effects=effects)
    if verify:
        saved = json.loads((target / "summary.json").read_text())
        if summary != saved:
            raise ValueError("Saved statistics differ from the raw JMH results")
        with (target / "forks.csv").open(newline="", encoding="utf-8") as stream:
            if list(csv.DictReader(stream)) != [{k: str(v) for k, v in row.items()} for row in rows]:
                raise ValueError("Fork CSV differs from the raw JMH results")
    else:
        with (target / "forks.csv").open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
        write(target / "summary.json", summary)
    print(target / "summary.json", flush=True)


def effect(reference, candidate):
    return dict(reference_ns=statistics.mean(reference) * 1e9,
                candidate_ns=statistics.mean(candidate) * 1e9,
                **compare(reference, candidate, threshold=5, seed=84592))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=["prepare", "lazy", "native-guard", "verify"])
    parser.add_argument("folder", type=Path)
    args = parser.parse_args()
    folder = args.folder.resolve()
    if not folder.is_relative_to(ROOT / "results"):
        parser.error("Use a timestamped folder under results")
    if args.phase == "prepare":
        prepare(folder)
    elif args.phase == "lazy":
        if not (folder / "prepared.json").exists():
            raise RuntimeError("Run Docker preparation and correctness checks first")
        lazy_measure(folder)
    elif args.phase == "native-guard":
        prepare_native_guard(folder)
    else:
        analyze(folder / "docker-lazy", True, verify=True)
        if (folder / "windows-native/summary.json").exists():
            analyze(folder / "windows-native", False, verify=True)


if __name__ == "__main__":
    main()
