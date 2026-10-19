"""Select two NetworkX commits, collect repeated timings, then analyze them."""
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
REPO = ROOT / 'networkx_repo'
DEFAULT_COMMITS = ['87b57851e9', '6da4704cbf']


def git(*args):
    return subprocess.check_output(['git', *args], cwd=REPO, text=True,
                                   stderr=subprocess.PIPE).strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--commits', nargs=2, default=DEFAULT_COMMITS, metavar=('OLD', 'NEW'))
    parser.add_argument('--repeats', type=int, default=20, help='Fresh processes per commit (>= 5).')
    parser.add_argument('--loops', type=int, default=100, help='Algorithm calls per observation.')
    parser.add_argument('--warmups', type=int, default=3)
    parser.add_argument('--size', type=int, default=35, help='Side length of the square grid.')
    parser.add_argument('--threshold', type=float, default=5, help='Practical threshold in percent.')
    parser.add_argument('--seed', type=int, default=42)
    args = parser.parse_args()
    if args.repeats < 5 or args.loops < 1 or args.warmups < 0 or args.size < 2:
        parser.error('Require repeats >= 5, loops >= 1, warmups >= 0 and size >= 2.')
    if not 0 < args.threshold < 100:
        parser.error('Threshold must be between 0 and 100 percent.')
    if not REPO.exists():
        subprocess.run(['git', 'clone', 'https://github.com/networkx/networkx.git', str(REPO)], check=True)
    if git('status', '--porcelain'):
        raise RuntimeError('networkx_repo has local changes. Save them before running.')
    commits = [git('rev-parse', '--verify', '--end-of-options', ref + '^{commit}') for ref in args.commits]
    if commits[0] == commits[1]:
        parser.error('Select two distinct commits.')
    git('merge-base', '--is-ancestor', *commits)
    branch = git('rev-parse', '--abbrev-ref', 'HEAD')
    original = git('rev-parse', 'HEAD') if branch == 'HEAD' else branch

    # Unique UTC timestamps prevent overwriting previous experiments.
    folder = ROOT / 'experiments' / datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S_%fZ')
    folder.mkdir(parents=True)
    for name in ['run.py', 'benchmark.py', 'analyze.py']:
        shutil.copy2(ROOT / name, folder / name)
    metadata = dict(status='running', commits=commits, config=vars(args),
                    created_utc=datetime.now(timezone.utc).isoformat(),
                    python=sys.version, platform=platform.platform(), processor=platform.processor(),
                    executable=sys.executable, git=git('--version'),
                    benchmark_sha256=hashlib.sha256((folder / 'benchmark.py').read_bytes()).hexdigest(),
                    measurement='Randomized pairs; one fresh process per observation; GC enabled',
                    bootstrap_samples=5000, confidence=0.95)
    def save_metadata():
        (folder / 'metadata.json').write_text(json.dumps(metadata, indent=2), encoding='utf-8')
    save_metadata()
    env = os.environ.copy()
    env.update(PYTHONHASHSEED='0', PYTHONDONTWRITEBYTECODE='1', PYTHONNOUSERSITE='1')
    env.pop('PYTHONPATH', None)
    rng = random.Random(args.seed)
    print(f'Experiment: {folder}', flush=True)
    try:
        with (folder / 'raw.csv').open('w', newline='', encoding='utf-8') as stream:
            writer = csv.writer(stream)
            writer.writerow(['commit', 'repeat', 'order', 'seconds', 'networkx_version'])
            for repeat in range(1, args.repeats + 1):
                order = commits.copy()
                rng.shuffle(order)  # Avoid always measuring the old version first.
                for position, commit in enumerate(order):
                    git('checkout', '--detach', '--quiet', commit)
                    result = subprocess.run([sys.executable, '-B', str(ROOT / 'benchmark.py'),
                        '--loops', str(args.loops), '--warmups', str(args.warmups), '--size', str(args.size)],
                        capture_output=True, text=True, env=env, timeout=120)
                    if result.returncode:
                        raise RuntimeError(result.stderr)
                    observation = json.loads(result.stdout)
                    seconds = observation['seconds']
                    if not math.isfinite(seconds) or seconds <= 0:
                        raise ValueError('Invalid timing observation.')
                    writer.writerow([commit, repeat, position, seconds, observation['networkx_version']])
                    stream.flush()
                    print(f'  Round {repeat:2}/{args.repeats} | {commit[:10]} | {seconds * 1000:.3f} ms', flush=True)
        metadata['status'] = 'measured'
    except BaseException as error:
        metadata.update(status='failed', error=str(error))
        raise
    finally:
        save_metadata()
        git('checkout', '--quiet', original)  # Restore the original branch or detached HEAD.
    from analyze import analyze_experiment
    analyze_experiment(folder)


if __name__ == '__main__':
    main()
