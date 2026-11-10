"""Compare two installed NumPy versions with randomized paired benchmark rounds.

Use any Python interpreter to invoke this script; both measured interpreters are
specified explicitly via --old-python and --new-python.
"""
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

ROOT = Path(__file__).resolve().parent


def probe(executable):
    code = 'import json, sys, numpy; print(json.dumps({"version": numpy.__version__, "executable": sys.executable, "python": sys.version.split()[0]}))'
    result = subprocess.run([str(executable), '-c', code], capture_output=True, text=True, check=True)
    return json.loads(result.stdout)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--old-python', required=True, type=Path)
    p.add_argument('--new-python', required=True, type=Path)
    p.add_argument('--repeats', type=int, default=20)
    p.add_argument('--loops', type=int, default=100)
    p.add_argument('--warmups', type=int, default=5)
    p.add_argument('--size', type=int, default=100000)
    p.add_argument('--threshold', type=float, default=5)
    p.add_argument('--seed', type=int, default=42)
    p.add_argument('--control', action='store_true', help='Compare identical NumPy versions as labeled A/B controls')
    a = p.parse_args()
    if a.repeats < 5 or a.loops < 1 or a.warmups < 0 or a.size < 2:
        p.error('Require repeats >= 5, loops >= 1, warmups >= 0 and size >= 2')
    if not 0 < a.threshold < 100:
        p.error('Threshold must be between 0 and 100')

    executables = [a.old_python.resolve(), a.new_python.resolve()]
    for executable in executables:
        if not executable.is_file():
            p.error(f'Python executable not found: {executable}')
    info = [probe(executable) for executable in executables]
    if a.control:
        if info[0]['version'] != info[1]['version']:
            p.error('--control requires the same NumPy version on both sides')
        commits = [f"numpy-{info[0]['version']}-control-A", f"numpy-{info[1]['version']}-control-B"]
    else:
        commits = [f"numpy-{record['version']}" for record in info]  # labels for analyze.py; not Git SHAs
        if commits[0] == commits[1]:
            p.error('Old/new interpreters have the same NumPy version; use --control for a negative control')
    if info[0]['python'] != info[1]['python']:
        p.error('For this experiment use the same Python version in both environments')

    folder = ROOT / 'experiments' / datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S_%fZ')
    folder.mkdir(parents=True)
    for name in ['run_numpy.py', 'benchmark_numpy.py', 'analyze_numpy.py']:
        shutil.copy2(ROOT / name, folder / name)
    metadata = {'status': 'running', 'commits': commits,
                'note': 'commits field contains NumPy release/control labels, NOT Git commits',
                'experiment_kind': 'negative_control' if a.control else 'release_comparison',
                'config': vars(a), 'environments': info,
                'created_utc': datetime.now(timezone.utc).isoformat(),
                'python': sys.version, 'platform': platform.platform(), 'processor': platform.processor(),
                'benchmark_sha256': hashlib.sha256((folder / 'benchmark_numpy.py').read_bytes()).hexdigest(),
                'measurement': 'Randomized paired rounds; one fresh process per observation; per-process batch average; imports and input setup excluded',
                'bootstrap_samples': 5000, 'confidence': 0.95}
    metadata['config'] = {k: str(v) if isinstance(v, Path) else v for k,v in vars(a).items()}

    def save_metadata():
        (folder / 'metadata.json').write_text(json.dumps(metadata, indent=2), encoding='utf-8')
    save_metadata()
    env = os.environ.copy()
    env.update(PYTHONHASHSEED='0', PYTHONDONTWRITEBYTECODE='1', PYTHONNOUSERSITE='1')
    env.pop('PYTHONPATH', None)
    rng = random.Random(a.seed)
    print(f'Experiment: {folder}', flush=True)
    try:
        with (folder / 'raw.csv').open('w', newline='', encoding='utf-8') as stream:
            writer = csv.writer(stream)
            writer.writerow(['commit', 'repeat', 'order', 'seconds', 'numpy_version'])
            for repeat in range(1, a.repeats + 1):
                order = [0, 1]
                rng.shuffle(order)
                for position, index in enumerate(order):
                    result = subprocess.run([str(executables[index]), '-B', str(ROOT / 'benchmark_numpy.py'),
                        '--loops', str(a.loops), '--warmups', str(a.warmups), '--size', str(a.size)],
                        capture_output=True, text=True, env=env, timeout=120, check=True)
                    observation = json.loads(result.stdout)
                    if observation['numpy_version'] != info[index]['version']:
                        raise RuntimeError('Wrong NumPy version loaded')
                    seconds = observation['seconds']
                    if not math.isfinite(seconds) or seconds <= 0:
                        raise ValueError('Invalid timing')
                    writer.writerow([commits[index], repeat, position, seconds, observation['numpy_version']])
                    stream.flush()
                    print(f'  Round {repeat:2}/{a.repeats} | {commits[index]} | {seconds*1000:.3f} ms', flush=True)
        metadata['status'] = 'measured'
    except BaseException as error:
        metadata.update(status='failed', error=str(error))
        raise
    finally:
        save_metadata()
    from analyze_numpy import analyze_experiment
    analyze_experiment(folder)

if __name__ == '__main__':
    main()
