"""Configurable external-command runner; extends the original paired analysis."""
import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import random
import shutil
import subprocess
import sys
from time import perf_counter, sleep

from analyze import compare, descriptive

ROOT = Path(__file__).resolve().parent


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n', encoding='utf-8')


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_revision(folder):
    try:
        return subprocess.check_output(['git', '-C', str(folder), 'rev-parse', 'HEAD'],
                                       text=True, stderr=subprocess.DEVNULL).strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def validate_config(config):
    if not isinstance(config.get('rounds'), int) or config['rounds'] < 5:
        raise ValueError('At least five fresh-process pairs required')
    if not math.isfinite(config.get('threshold', 5)) or not 0 < config.get('threshold', 5) < 100:
        raise ValueError('Threshold must be finite and between zero and 100')
    if len(config.get('arms', [])) != 2 or len({a['name'] for a in config['arms']}) != 2:
        raise ValueError('Exactly two distinct named arms required')
    if len({a.get('metric', 'internal') for a in config['arms']}) != 1:
        raise ValueError('Both arms must use the same timing boundary')
    for arm in config['arms']:
        if not arm.get('command') or not all(isinstance(x, str) for x in arm['command']):
            raise ValueError('Commands must be nonempty argument arrays')
        if arm.get('load', False) and arm.get('cpu') is None:
            raise ValueError('Controlled contention requires an explicit CPU')
        if arm.get('metric', 'internal') not in ['internal', 'process']:
            raise ValueError('Metric must be internal or process')
    target = config.get('target_seconds')
    if target is not None and (not math.isfinite(target) or target <= 0):
        raise ValueError('Target must be positive and finite')


def expand_command(command, runtime):
    mapping = dict(python=sys.executable, root=str(ROOT), **runtime)
    expanded = []
    for part in command:
        for key, value in mapping.items():
            part = part.replace('{' + key + '}', str(value))
        if '{java}' in part:
            raise ValueError('Java executable is required for this command')
        expanded.append(part)
    return expanded


def terminate_tree(child):
    """Kill benchmark descendants as well as the affinity wrapper on failure."""
    import psutil
    if os.name != 'nt':
        import signal
        try:
            os.killpg(child.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        return
    try:
        process = psutil.Process(child.pid)
        descendants = process.children(recursive=True)
    except psutil.NoSuchProcess:
        descendants = []
    for descendant in reversed(descendants):
        try:
            descendant.kill()
        except psutil.NoSuchProcess:
            pass
    if child.poll() is None:
        child.kill()


def networkx_identity():
    repo = ROOT / 'networkx_repo'
    if not (repo / 'networkx').is_dir() or not git_revision(repo):
        raise ValueError('Restore the supplied NetworkX source before graph experiments')
    dirty = subprocess.check_output(['git', '-C', str(repo), 'status', '--porcelain'], text=True).strip()
    if dirty:
        raise ValueError('NetworkX checkout must be clean before measurement: ' + dirty)
    return dict(revision=git_revision(repo), clean=True,
                python_source_sha256={str(p.relative_to(repo)): sha256(p)
                                      for p in sorted((repo / 'networkx').rglob('*.py'))})


def observe(arm, runtime, timeout):
    command = expand_command(arm['command'], runtime)
    env = os.environ.copy()
    env.update(PYTHONHASHSEED='0', PYTHONDONTWRITEBYTECODE='1',
               PYTHONNOUSERSITE='1', OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1')
    env.pop('PYTHONPATH', None)
    env.update(arm.get('env', {}))
    worker = child = job = None
    evidence = dict(command=command, started_utc=datetime.now(timezone.utc).isoformat(),
                    status='running', stdout='', stderr='')
    try:
        if arm.get('load'):
            ready = ROOT / '.tmp' / ('load-' + str(os.getpid()) + '.ready')
            ready.parent.mkdir(exist_ok=True)
            ready.unlink(missing_ok=True)
            worker = subprocess.Popen([sys.executable, str(ROOT / 'perflens.py'),
                                       '_load', str(arm.get('load_cpu', arm['cpu'])), str(ready)],
                                      stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, env=env)
            for _ in range(200):
                if ready.exists():
                    break
                if worker.poll() is not None:
                    raise RuntimeError('Contention worker failed: ' + worker.stderr.read().decode())
                sleep(0.01)
            else:
                raise TimeoutError('Contention worker did not become ready')
            ready.unlink()
        # Wrapper sets affinity before launching target; child inherits affinity.
        if arm.get('cpu') is not None:
            command = [sys.executable, str(ROOT / 'perflens.py'), '_affinity',
                       str(arm['cpu']), *command]
        evidence['command'] = command
        if os.name == 'nt':
            from process_control import WindowsJob
            job = WindowsJob()
            command = [sys.executable, str(ROOT / 'benchmark_launcher.py'), *command]
            evidence['launcher_command'] = command
        start = perf_counter()
        child = subprocess.Popen(command, cwd=ROOT, env=env, text=True,
                                 stdin=subprocess.PIPE if job else subprocess.DEVNULL,
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                 start_new_session=os.name != 'nt')
        if job:
            job.assign(child.pid)
        stdout, stderr = child.communicate(input='run\n' if job else None, timeout=timeout)
        wall = perf_counter() - start
        evidence.update(stdout=stdout, stderr=stderr, returncode=child.returncode,
                        process_seconds=wall)
        if child.returncode:
            raise RuntimeError(f'Benchmark failed ({child.returncode}): {stderr}')
        value = json.loads(stdout)
        if value.get('valid') is not True or 'checksum' not in value:
            raise ValueError('Benchmark must report valid=true and a checksum')
        seconds = value.get('seconds')
        if isinstance(seconds, bool) or not isinstance(seconds, (int, float)) or not math.isfinite(seconds) or seconds <= 0:
            raise ValueError('Benchmark seconds must be finite and positive')
        return dict(seconds=wall if arm.get('metric') == 'process' else seconds,
                    internal_seconds=seconds, process_seconds=wall, payload=value,
                    command=command, stderr=stderr)
    except BaseException as error:
        if child is not None:
            if job:
                job.terminate()
            else:
                terminate_tree(child)
            try:
                stdout, stderr = child.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                # Cleanup itself must never wait indefinitely for inherited pipes.
                stdout, stderr = '', 'Cleanup could not drain inherited pipes within five seconds'
                for pipe in [child.stdout,child.stderr]:
                    if pipe:
                        pipe.close()
            evidence.update(stdout=stdout, stderr=stderr, returncode=child.returncode)
        evidence.update(status='failed', error=repr(error))
        error.evidence = evidence
        raise
    finally:
        if job:
            job.close()
        if worker is not None:
            worker.terminate()
            worker.wait(timeout=10)
            worker.stderr.close()


def analyze_rows(config, rows):
    names = [a['name'] for a in config['arms']]
    groups = {name: {} for name in names}
    checksums = []
    for row in rows:
        name, number = row['arm'], int(row['round'])
        if name not in groups or number in groups[name]:
            raise ValueError('Unexpected arm or duplicate observation')
        value = float(row['seconds'])
        if not math.isfinite(value) or value <= 0:
            raise ValueError('Invalid timing')
        groups[name][number] = value
        checksums.append(row['checksum'])
    if len(set(checksums)) != 1:
        raise ValueError('Checksums differ between observations')
    if any(set(group) != set(range(1, config['rounds'] + 1)) for group in groups.values()):
        raise ValueError('Incomplete run: missing pairs')
    arrays = [[groups[name][i] for i in range(1, config['rounds'] + 1)] for name in names]
    result = dict(comparison=compare(*arrays, threshold=config.get('threshold', 5),
                                    seed=config.get('seed', 42)),
                  summaries={name: descriptive(values) for name, values in zip(names, arrays)})
    target = config.get('target_seconds')
    # Descriptive observed-mean target assessment is distinct from relative CI inference.
    result['target'] = None if target is None else dict(seconds=target,
        basis='observed sample mean; not a latency SLA confidence guarantee',
        met={name: summary['mean_seconds'] <= target for name, summary in result['summaries'].items()})
    return result


def run(config_path, output=None, runtime=None):
    config_path = Path(config_path)
    config = json.loads(config_path.read_text(encoding='utf-8-sig'))
    validate_config(config)
    runtime = runtime or {}
    folder = Path(output) if output else ROOT / 'results' / (datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ_') + config['name'])
    folder.mkdir(parents=True, exist_ok=False)
    sources = [p for p in ROOT.glob('*.py')] + list((ROOT / 'workloads').glob('*.*'))
    snapshot = folder / 'source'
    snapshot.mkdir()
    for source in sources:
        relative = source.relative_to(ROOT)
        target = snapshot / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    write_json(folder / 'config.json', config)
    metadata = dict(status='running', started_utc=datetime.now(timezone.utc).isoformat(),
        python=sys.version, executable=sys.executable, platform=platform.platform(),
        processor=platform.processor(), logical_cpus=os.cpu_count(),
        root_revision=git_revision(ROOT), networkx_revision=git_revision(ROOT / 'networkx_repo'),
        source_sha256={str(p.relative_to(snapshot)): sha256(p) for p in snapshot.rglob('*') if p.is_file()},
        runtime=runtime, timer=str(__import__('time').get_clock_info('perf_counter')),
        environment=dict(PYTHONHASHSEED='0',PYTHONDONTWRITEBYTECODE='1',PYTHONNOUSERSITE='1',
                         OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',PYTHONPATH='removed'),
        design='Randomized paired fresh processes; batch averages are observations; 5000 paired bootstrap resamples')
    write_json(folder / 'metadata.json', metadata)
    rows = []
    rng = random.Random(config.get('seed', 42))
    try:
        uses_graph = any('graph_queries.py' in part for arm in config['arms'] for part in arm['command'])
        if uses_graph:
            metadata['networkx_source'] = networkx_identity()
        if runtime.get('java'):
            metadata['java_version'] = subprocess.run([runtime['java'], '-version'], capture_output=True,text=True,check=True).stderr
            javac = str(Path(runtime['java']).with_name('javac.exe' if os.name == 'nt' else 'javac'))
            (ROOT / 'build').mkdir(exist_ok=True)
            subprocess.run([javac, '-d', str(ROOT / 'build'), str(ROOT / 'workloads/SearchBench.java')], check=True)
            metadata['java_class_sha256'] = sha256(ROOT / 'build/SearchBench.class')
        write_json(folder / 'metadata.json', metadata)
        with (folder / 'raw.csv').open('w', newline='', encoding='utf-8') as csvfile, (folder / 'observations.jsonl').open('w', encoding='utf-8') as details:
            writer = csv.DictWriter(csvfile, fieldnames=['round','order','arm','seconds','internal_seconds','process_seconds','checksum'])
            writer.writeheader()
            for number in range(1, config['rounds'] + 1):
                arms = config['arms'].copy()
                rng.shuffle(arms)
                for order, arm in enumerate(arms):
                    try:
                        observation = observe(arm, runtime, config.get('timeout', 120))
                    except BaseException as error:
                        with (folder / 'failures.jsonl').open('a', encoding='utf-8') as failures:
                            failures.write(json.dumps(dict(round=number, order=order, arm=arm['name'],
                                **getattr(error, 'evidence', dict(error=repr(error),command=arm['command'])))) + '\n')
                        raise
                    row = dict(round=number, order=order, arm=arm['name'],
                        seconds=observation['seconds'], internal_seconds=observation['internal_seconds'],
                        process_seconds=observation['process_seconds'],
                        checksum=json.dumps(observation['payload']['checksum'], sort_keys=True))
                    rows.append(row)
                    writer.writerow(row)
                    csvfile.flush()
                    details.write(json.dumps(dict(round=number, order=order, arm=arm['name'], **observation)) + '\n')
                    details.flush()
                print(f"{config['name']}: pair {number}/{config['rounds']}", flush=True)
        if uses_graph and networkx_identity() != metadata['networkx_source']:
            raise ValueError('NetworkX source drifted during measurement')
        result = analyze_rows(config, rows)
        write_json(folder / 'summary.json', result)
        metadata.update(status='complete', finished_utc=datetime.now(timezone.utc).isoformat(),
                        raw_sha256=sha256(folder / 'raw.csv'))
    except BaseException as error:
        metadata.update(status='failed', error=repr(error))
        raise
    finally:
        write_json(folder / 'metadata.json', metadata)
    print(folder, result['comparison'], flush=True)
    return folder


def main():
    if len(sys.argv) > 1 and sys.argv[1] in ['_load', '_affinity']:
        import psutil
        psutil.Process().cpu_affinity([int(sys.argv[2])])
        if sys.argv[1] == '_affinity':
            raise SystemExit(subprocess.call(sys.argv[3:]))
        Path(sys.argv[3]).write_text('ready')
        while True:
            sum(range(10000))
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('config', type=Path)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--java', help='Path to Java executable; otherwise JAVA_HOME or PATH')
    args = parser.parse_args()
    java = args.java or (str(Path(os.environ['JAVA_HOME']) / 'bin' / ('java.exe' if os.name == 'nt' else 'java')) if os.environ.get('JAVA_HOME') else shutil.which('java'))
    runtime = dict(java=java) if java else {}
    run(args.config, args.output, runtime)


if __name__ == '__main__':
    main()
