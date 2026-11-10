"""Native Windows benchmark with a Java policy and bounded Windows job ownership."""
import argparse
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time
import winreg

import psutil

from study import (CORE, ROOT, SHAS, analyze, artifacts, benchmark_args,
                   digest, fork_score, paired_schedule, write)
from process_control import WindowsJob


def run_java(java, args, env, receipt, cwd):
    command = [str(java), *args]
    started = time.monotonic()
    data = dict(command=command, returncode=None)
    job = WindowsJob()
    child = None
    try:
        child = subprocess.Popen([sys.executable, str(ROOT / "benchmark_launcher.py"), *command],
            cwd=cwd, env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace")
        job.assign(child.pid)
        stdout, stderr = child.communicate(input="run\n", timeout=120)
        data.update(stdout=stdout, stderr=stderr, returncode=child.returncode)
    except subprocess.TimeoutExpired as error:
        data.update(error="timeout", stdout=str(error.stdout), stderr=str(error.stderr))
        raise
    except Exception as error:
        data.update(error=repr(error))
        raise
    finally:
        try:
            job.close()
            if child is not None:
                child.wait(timeout=5)
        finally:
            data["elapsed_seconds"] = time.monotonic() - started
            write(receipt, data)
    if data["returncode"] != 0:
        raise RuntimeError("Native command failed. See " + str(receipt))
    return data


def check_artifacts(folder, sha):
    out = artifacts(folder, sha)
    expected = json.loads((folder / (sha[:12] + "-artifact-hashes.json")).read_text())
    for name, wanted in expected.items():
        if digest(out / name) != wanted:
            raise ValueError("Changed Docker artifact: " + name)
    for directory in ("harness", "library", "probe", "deps"):
        current = {p.relative_to(out).as_posix() for p in (out / directory).rglob("*") if p.is_file()}
        if current != {name for name in expected if name.startswith(directory + "/")}:
            raise ValueError("Unexpected file in executable artifact directory")


def make_policy(folder, target, guard):
    grants = [f'grant codeBase "{guard.as_uri()}/-" {{ permission java.security.AllPermission; }};']
    for sha in SHAS:
        out = artifacts(folder, sha)
        locations = [(out / "harness").as_uri() + "/-", *[
            p.as_uri() for p in sorted((out / "deps").glob("*.jar"))]]
        grants.extend(f'grant codeBase "{location}" {{ permission java.security.AllPermission; }};'
                      for location in locations)
    path = target / "benchmark.policy"
    path.write_text("\n".join(grants) + "\n", encoding="utf-8")
    return ["-Djava.security.manager=perflens.finalstudy.LoopbackGuard",
            "-Djava.security.policy==" + path.as_uri(), "-Djmh.link.address=127.0.0.1"]


def hardware():
    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DESCRIPTION\System\CentralProcessor\0") as key:
        cpu = winreg.QueryValueEx(key, "ProcessorNameString")[0].strip()
    return dict(os=platform.platform(), windows_version=platform.win32_ver(), processor=cpu,
                physical_cores=psutil.cpu_count(logical=False),
                logical_processors=psutil.cpu_count(), memory_bytes=psutil.virtual_memory().total,
                process_allowed_cpus=psutil.Process().cpu_affinity(),
                host_cpu_utilization_percent=psutil.cpu_percent(interval=0.25))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folder", type=Path)
    parser.add_argument("--java", required=True, type=Path)
    parser.add_argument("--ipc", choices=["default-sandbox", "reviewed-loopback"], required=True)
    args = parser.parse_args()
    folder = args.folder.resolve()
    if os.name != "nt" or not folder.is_relative_to(ROOT / "results"):
        parser.error("Native Windows and a study folder under results are required")
    if not (folder / "docker-lazy/summary.json").exists():
        raise RuntimeError("Complete Docker experiment before native benchmarking")
    java = args.java.resolve(strict=True)
    guard_base = artifacts(folder, SHAS[0])
    guard = guard_base / "native-guard"
    guard_hashes = json.loads((folder / "native-guard-hashes.json").read_text())
    if {p.relative_to(guard_base).as_posix(): digest(p) for p in guard.rglob("*.class")} != {
            name: value for name, value in guard_hashes.items() if name.endswith(".class")}:
        raise ValueError("Native guard differs from Docker-built artifact")
    target = folder / "windows-native"
    target.mkdir()
    scratch = artifacts(folder, SHAS[0]).parent / "native-scratch-guarded"
    scratch.mkdir()
    marker = scratch / "permission-marker.txt"
    marker.write_text("permission probe", encoding="utf-8")
    policy_flags = make_policy(folder, target, guard)
    flags = ["-Xms512m", "-Xmx512m", "-Djava.io.tmpdir=" + scratch.as_posix(), *policy_flags]
    if any(" " in flag for flag in flags):
        raise ValueError("Use a scratch path without spaces for the JMH JVM argument string")
    env = {key: os.environ[key] for key in ("SystemRoot", "WINDIR", "ComSpec") if key in os.environ}
    env.update(PATH=str(java.parent) + os.pathsep + str(Path(env["SystemRoot"]) / "System32"),
               TEMP=str(scratch), TMP=str(scratch))
    power = subprocess.run([str(Path(env["SystemRoot"]) / "System32/powercfg.exe"),
                            "/GETACTIVESCHEME"], capture_output=True, text=True,
                           errors="replace", timeout=10)
    write(target / "environment.json", dict(**hardware(), java=str(java), java_sha256=digest(java),
          power_scheme=power.stdout.strip(), power_scheme_status=power.returncode,
          environment_keys=sorted(env), flags=flags, policy_sha256=digest(target / "benchmark.policy"),
          scope="Native Windows on same physical machine as Docker/WSL, separate dataset",
          ipc_context=args.ipc,
          isolation="Java 21 exclusive code-source policy, IPv4 loopback-only guard, "
                    "Windows job and minimal environment"))
    run_java(java, ["-XshowSettings:vm", "-version"], env, target / "jvm.json", scratch)
    guard_check = run_java(java, [*flags, "-cp", str(guard), "perflens.finalstudy.LoopbackGuard"],
                           env, target / "loopback-guard.json", scratch)
    if "Trusted loopback allowed; non-loopback denied" not in guard_check["stdout"]:
        raise RuntimeError("Native loopback guard check failed")
    classpaths = {}
    for sha in SHAS:
        check_artifacts(folder, sha)
        out = artifacts(folder, sha)
        cp = os.pathsep.join(str(p) for p in [guard, out / "harness", out / "library",
                                                *sorted((out / "deps").glob("*.jar"))])
        classpaths[sha] = cp
        denied = run_java(java, [*flags, "-cp", os.pathsep.join([str(guard), str(out / "probe")]),
            "perflens.finalstudy.DeniedProbe", str(marker), str(java)], env,
            target / (sha[:12] + "-denials.json"), scratch)
        if len([line for line in denied["stdout"].splitlines() if line.startswith("denied ")]) != 8:
            raise RuntimeError("Missing policy denial evidence")
        correctness = run_java(java, [*flags, "-cp", cp, "perflens.external.CorrectnessMain"],
                               env, target / (sha[:12] + "-correctness.json"), scratch)
        if '"valid":true' not in correctness["stdout"] or '"checksum":458211' not in correctness["stdout"]:
            raise RuntimeError("Native correctness failed")
    write(target / "gate.json", dict(status="artifacts, denial probes and both correctness checks passed"))
    schedule = paired_schedule(CORE, 84591)
    write(target / "schedule.json", schedule)
    for pair in schedule:
        for sha in pair["shas"]:
            for case in pair["workloads"]:
                method, limit = CORE[case]
                filename = f"r{pair['round']:02d}-{sha[:12]}-{case}.json"
                path = target / filename
                args = benchmark_args("perflens.external.RankBenchmark." + method,
                                      ["limit=" + str(limit), "containers=16"], False, str(path))
                run_java(java, [*flags, "-cp", classpaths[sha], "org.openjdk.jmh.Main",
                         *args, "-jvmArgs", " ".join(flags)],
                         env, target / (filename + ".command.json"), scratch)
                fork_score(path, case, sha, False)
                print(filename, flush=True)
    for sha in SHAS:
        check_artifacts(folder, sha)
    analyze(target, False)


if __name__ == "__main__":
    main()
