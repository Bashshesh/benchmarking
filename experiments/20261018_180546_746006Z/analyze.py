"""Descriptive statistics and a paired bootstrap confidence interval."""
import argparse
import csv
import json
import math
from pathlib import Path
import random
from statistics import mean, median, stdev, variance

ROOT = Path(__file__).resolve().parent


def descriptive(values):
    average = mean(values)
    sd = stdev(values)
    return dict(n=len(values), mean_seconds=average, median_seconds=median(values),
                sd_seconds=sd, variance_seconds2=variance(values), cv_percent=sd / average * 100)


def compare(old, new, threshold=5, seed=42, samples=5000):
    """Resample whole rounds, keeping old/new measurements paired."""
    if len(old) != len(new) or len(old) < 5:
        raise ValueError('At least five complete pairs are required.')
    if any(not math.isfinite(x) or x <= 0 for x in old + new):
        raise ValueError('Timings must be finite and positive.')
    if samples < 100 or not 0 < threshold < 100:
        raise ValueError('Invalid bootstrap count or threshold.')
    change = (mean(new) / mean(old) - 1) * 100
    rng = random.Random(seed)
    changes = []
    for _ in range(samples):
        indices = rng.choices(range(len(old)), k=len(old))
        old_mean = mean(old[i] for i in indices)
        new_mean = mean(new[i] for i in indices)
        changes.append((new_mean / old_mean - 1) * 100)
    changes.sort()
    low = changes[int(0.025 * (samples - 1))]
    high = changes[int(0.975 * (samples - 1))]
    statistical = 'slower' if low > 0 else 'faster' if high < 0 else 'uncertain'
    if low > threshold:
        decision = 'regression'
    elif high < -threshold:
        decision = 'improvement'
    elif low >= -threshold and high <= threshold:
        decision = 'within_threshold'
    else:
        decision = 'inconclusive'
    return dict(change_percent=change, ci95_percent=[low, high], statistical_direction=statistical,
                threshold_percent=threshold, decision=decision)


def analyze_experiment(folder):
    folder = Path(folder).resolve()
    metadata = json.loads((folder / 'metadata.json').read_text(encoding='utf-8'))
    if metadata['status'] not in ['measured', 'complete']:
        raise ValueError('This experiment is incomplete or failed; no inference is allowed.')
    commits = metadata['commits']
    expected = metadata['config']['repeats']
    timings = {commit: {} for commit in commits}
    with (folder / 'raw.csv').open(newline='', encoding='utf-8') as stream:
        for row in csv.DictReader(stream):
            commit, repeat = row['commit'], int(row['repeat'])
            if commit not in timings or repeat in timings[commit]:
                raise ValueError('Unexpected commit or duplicate measurement.')
            timings[commit][repeat] = float(row['seconds'])
    if any(set(rows) != set(range(1, expected + 1)) for rows in timings.values()):
        raise ValueError('Missing observations; refusing to analyze an incomplete experiment.')
    old, new = [[timings[sha][i] for i in range(1, expected + 1)] for sha in commits]
    comparison = compare(old, new, metadata['config']['threshold'], metadata['config']['seed'])
    summaries = {sha: descriptive(values) for sha, values in zip(commits, [old, new])}
    result = dict(commits=commits, summaries=summaries, comparison=comparison,
                  method='Paired percentile bootstrap of relative mean change; 5000 resamples; 95% CI')
    lines = ['# NetworkX benchmark report', '',
             '| Commit | N | Mean (ms) | Median (ms) | SD (ms) | CV (%) |',
             '|---|---:|---:|---:|---:|---:|']
    for sha, summary in summaries.items():
        lines.append(f"| {sha[:10]} | {summary['n']} | {summary['mean_seconds']*1000:.4f} | "
                     f"{summary['median_seconds']*1000:.4f} | {summary['sd_seconds']*1000:.4f} | {summary['cv_percent']:.2f} |")
    low, high = comparison['ci95_percent']
    lines += ['', f"Relative mean change: {comparison['change_percent']:+.2f}%",
              f'95% confidence interval of change: [{low:+.2f}%, {high:+.2f}%]',
              f"Statistical direction (CI vs zero): {comparison['statistical_direction']}",
              f"Practical threshold: {comparison['threshold_percent']:g}%",
              f"Decision: **{comparison['decision']}**", '',
              'Positive changes mean slower execution. Regression requires the entire CI above the threshold.',
              'Within-threshold describes this interval, not proof of equal performance.',
              'The percentile bootstrap is approximate. Rounds may remain correlated; no correction for multiple experiments.',
              'Confirm flagged changes in a separate preplanned run on a quiet machine.',
              'One observation is a batch average from one fresh process, not independent loop timings.',
              'CV is SD / mean; it describes variation, not statistical significance.',
              f"Configuration: repeats={expected}, loops={metadata['config']['loops']}, "
              f"warmups={metadata['config']['warmups']}, grid={metadata['config']['size']} x {metadata['config']['size']}",
              f"Python: {metadata['python'].splitlines()[0]}", f"Platform: {metadata['platform']}"]
    if expected < 20:
        lines += ['', 'Small sample: fewer than 20 pairs. Treat the interval as a smoke-test estimate.']
    (folder / 'summary.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    (folder / 'report.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    metadata['status'] = 'complete'
    (folder / 'metadata.json').write_text(json.dumps(metadata, indent=2), encoding='utf-8')
    print('\n'.join(lines))
    print(f'\nSaved: {folder / "report.md"}')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('experiment', nargs='?', help='Experiment directory; defaults to latest complete run.')
    args = parser.parse_args()
    if args.experiment:
        selected = Path(args.experiment)
    else:
        candidates = [p.parent for p in sorted((ROOT / 'experiments').glob('*/metadata.json'))
                      if json.loads(p.read_text(encoding='utf-8')).get('status') in ['measured', 'complete']]
        if not candidates:
            parser.error('No completed experiment found. Run python run.py first.')
        selected = candidates[-1]
    analyze_experiment(selected)
