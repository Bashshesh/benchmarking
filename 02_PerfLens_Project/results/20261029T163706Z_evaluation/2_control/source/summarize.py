"""Recompute analysis and charts from an explicit completed suite, without timing."""
import argparse
import csv
import json
from pathlib import Path
import random
from statistics import mean, stdev

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from perflens import ROOT, analyze_rows, sha256, write_json


def cv_interval(old, new, seed=42):
    """Paired percentile interval for CV ratio; exploratory, not a coverage proof."""
    rng = random.Random(seed)
    ratios = []
    for _ in range(2000):
        indices = rng.choices(range(len(old)), k=len(old))
        a, b = [[values[i] for i in indices] for values in [old,new]]
        acv, bcv = stdev(a)/mean(a), stdev(b)/mean(b)
        if acv > 0:
            ratios.append(bcv/acv)
    ratios.sort()
    if not ratios:
        return None
    return [ratios[int(.025*(len(ratios)-1))],ratios[int(.975*(len(ratios)-1))]]


def exact_binomial_interval(k, n):
    """Clopper-Pearson 95% interval by inversion of the binomial tails."""
    from math import comb
    def cdf(k, p):
        return sum(comb(n,i)*p**i*(1-p)**(n-i) for i in range(k+1))
    def solve(k, target):
        low, high = 0., 1.
        for _ in range(80):
            mid = (low+high)/2
            if cdf(k,mid) > target:
                low = mid
            else:
                high = mid
        return (low+high)/2
    return [0. if k == 0 else solve(k-1,.975), 1. if k == n else solve(k,.025)]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('suite', type=Path)
    args = parser.parse_args()
    suite = args.suite.resolve()
    manifest = json.loads((suite / 'suite.json').read_text())
    if manifest['status'] != 'complete':
        raise ValueError('Refusing publication analysis of an incomplete suite')
    output = suite / 'analysis'
    output.mkdir(exist_ok=True)
    records = []
    for name in manifest['experiments']:
        folder = suite / name
        config = json.loads((folder / 'config.json').read_text())
        metadata = json.loads((folder / 'metadata.json').read_text())
        if metadata['status'] != 'complete' or metadata['raw_sha256'] != sha256(folder / 'raw.csv'):
            raise ValueError('Incomplete or altered raw data: ' + name)
        with (folder / 'raw.csv').open(newline='') as stream:
            rows = list(csv.DictReader(stream))
        result = analyze_rows(config, rows)
        saved = json.loads((folder / 'summary.json').read_text())
        if result != saved:
            raise ValueError('Saved summary differs from reproducible reanalysis: ' + name)
        arms = [arm['name'] for arm in config['arms']]
        arrays = [[float(row['seconds']) for row in sorted(rows,key=lambda r:int(r['round'])) if row['arm']==arm] for arm in arms]
        record = dict(name=name, experiment=config['name'], session=config['session'], arms=arms,
            **result, cv_ratio_ci95=cv_interval(*arrays),
            point_only_decision=('regression' if result['comparison']['change_percent'] > 5 else
                                 'improvement' if result['comparison']['change_percent'] < -5 else 'within_threshold'),
            minimum_change_percent=(min(arrays[1])/min(arrays[0])-1)*100,
            process_mean_seconds={arm:mean(float(r['process_seconds']) for r in rows if r['arm']==arm) for arm in arms})
        records.append(record)
        fig, axes = plt.subplots(1,2,figsize=(11,3.5))
        axes[0].boxplot([[x*1000 for x in values] for values in arrays], tick_labels=arms, showmeans=True)
        axes[0].set_ylabel('Internal time per operation (ms)')
        for arm, values in zip(arms,arrays):
            axes[1].plot(range(1,len(values)+1), [x*1000 for x in values], '.-', label=arm)
        axes[1].set_xlabel('Fresh-process pair'); axes[1].set_ylabel('Internal time (ms)'); axes[1].legend(fontsize=8)
        fig.suptitle(name); fig.tight_layout(); fig.savefig(output / (name+'.png'), dpi=160); plt.close(fig)
        if config['name'] == 'java_warmup':
            details = [json.loads(line) for line in (folder/'observations.jsonl').read_text().splitlines()]
            traces = [d['payload']['warmup_seconds'] for d in details if d['arm']=='20_warmups']
            fig, ax = plt.subplots(figsize=(7,3.5))
            for trace in traces:
                ax.plot(range(1,len(trace)+1),[v*1000 for v in trace],alpha=.3)
            ax.set(xlabel='Untimed warmup call',ylabel='Time (ms)',title=name+': each line is one JVM')
            fig.tight_layout();fig.savefig(output/(name+'_traces.png'),dpi=160);plt.close(fig)
    write_json(output / 'comparisons.json', records)
    columns=['name','reference_ms','candidate_ms','change_percent','ci_low','ci_high','decision','reference_cv','candidate_cv','point_only_decision','minimum_change_percent']
    with (output / 'comparisons.csv').open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=columns);writer.writeheader()
        for r in records:
            a,b=[r['summaries'][name] for name in r['arms']]; c=r['comparison']
            writer.writerow(dict(name=r['name'],reference_ms=a['mean_seconds']*1000,candidate_ms=b['mean_seconds']*1000,
                change_percent=c['change_percent'],ci_low=c['ci95_percent'][0],ci_high=c['ci95_percent'][1],decision=c['decision'],
                reference_cv=a['cv_percent'],candidate_cv=b['cv_percent'],point_only_decision=r['point_only_decision'],minimum_change_percent=r['minimum_change_percent']))
    fig, ax=plt.subplots(figsize=(10,8))
    for i,r in enumerate(records):
        c=r['comparison']; low,high=c['ci95_percent']
        ax.plot([low,high],[i,i],color='tab:blue');ax.plot(c['change_percent'],i,'o',color='tab:blue')
    ax.axvspan(-5,5,color='gray',alpha=.15,label='Practical tolerance ±5%'); ax.axvline(0,color='black',lw=.7)
    ax.set_yticks(range(len(records)),[r['name'] for r in records]);ax.invert_yaxis()
    ax.set_xlabel('Candidate time relative to reference (%) — negative is faster');ax.set_title('Mean changes with paired bootstrap 95% intervals')
    ax.legend();fig.tight_layout();fig.savefig(output/'effects.png',dpi=180);plt.close(fig)
    lines=['# Measured evaluation results','',
        'All values below come from completed raw measurements in this suite. No simulated timings are mixed into these results. Internal operation times exclude setup/startup and are not full-application latency.', '',
        '| Comparison | Reference ms | Candidate ms | Change % | 95% CI % | Classification |',
        '|---|---:|---:|---:|---|---|']
    for r in records:
        a,b=[r['summaries'][name] for name in r['arms']]; c=r['comparison'];lo,hi=c['ci95_percent']
        lines.append(f"| {r['name']} | {a['mean_seconds']*1000:.4f} | {b['mean_seconds']*1000:.4f} | {c['change_percent']:+.2f} | [{lo:+.2f}, {hi:+.2f}] | {c['decision']} |")
    lines += ['','## Classifier validation','',
        'Trials here are whole 20-pair comparisons, not inner timing loops. Exact binomial intervals below are descriptive and assume independent comparable trials; the two sessions share a host, so independence/generalization is limited. Two trials cannot establish a reliable general false-positive or detection rate.']
    for experiment,label,decision in [('control','False regression flags','regression'),('injection','Detected injected slowdowns','regression')]:
        subset=[r for r in records if r['experiment']==experiment]; n=len(subset); k=sum(r['comparison']['decision']==decision for r in subset)
        lo,hi=exact_binomial_interval(k,n)
        outcomes=', '.join(r['comparison']['decision'] for r in subset)
        lines += ['',f'- {label}: {k}/{n}; exact 95% binomial interval [{100*lo:.1f}%, {100*hi:.1f}%]. Outcomes: {outcomes}.']
    lines += ['','## Noise and mitigation','',
        'CV is sample SD / mean. Lower CV is not automatically less bias or a better estimator. CV-ratio intervals use 2000 paired bootstrap draws and are exploratory. A mitigation may change average duration without reducing variation.']
    for r in records:
        if r['experiment'] not in ['cpu_contention','cpu_mitigation','java_warmup']:continue
        a,b=[r['summaries'][name] for name in r['arms']];ci=r['cv_ratio_ci95']
        lines += ['',f"- {r['name']}: CV {a['cv_percent']:.2f}% → {b['cv_percent']:.2f}%; candidate/reference CV ratio 95% interval [{ci[0]:.2f}, {ci[1]:.2f}]. See per-pair plot and Java warmup traces where applicable."]
    lines += ['','## No regression and absolute targets','',
        'The graph target is a preselected illustrative mean-operation budget of 3 ms, not a real application SLA. Assessment uses the observed mean; it makes no tail-latency or confidence guarantee.']
    for r in records:
        if r['target']:
            lines.append(f"- {r['name']}: {r['target']['met']}.")
    disagreements=[r['name'] for r in records if r['point_only_decision']!=r['comparison']['decision']]
    lines += ['','## Comparative methodology evaluation','',
        'Paired interval classification quantifies uncertainty and can remain inconclusive. A point-estimate-only ±5% rule cannot express uncertainty. The minimum-time ratio is recorded in comparisons.csv; it describes best observed timings and is not the mean-change estimand. No significance test is performed on minima.',
        '',f'Point-only versus interval classification differs for {len(disagreements)} of {len(records)} comparisons: '+(', '.join(disagreements) or 'none')+'.',
        '', 'Warmup traces allow inspection but no changepoint analysis or steady-state proof is implemented. Process-wall means in comparisons.json include startup/setup; never substitute them for internal times when interpreting the optimization magnitude.',
        '', '## Repeatability and limitations','',
        'Session 2 is a preplanned held-out confirmation with fresh processes and a different order seed. It is same-host repeatability, not reproduction on another machine. The suite provides limited workloads, one host and JVM, no power calculation, approximate bootstrap coverage, no multiple-testing adjustment, and no measurements of energy, memory or end-to-end user impact. Source/runtime effects are conditional on these exact workloads. Large improvements from deliberately redundant BFS or linear search do not establish improvements across all of NetworkX or Java.',
        '', 'All original project claims, especially NumPy presentation results without raw data, remain distinct from these new measurements.',
        '', '![Effect intervals](effects.png)']
    (output/'RESULTS.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(output/'RESULTS.md')


if __name__=='__main__':
    main()
