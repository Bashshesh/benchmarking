"""Independent raw ingestion, source checks and figures for additive studies."""
import argparse
from collections import Counter,defaultdict
import csv
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from perflens import analyze_rows,sha256,write_json
from analyze import compare
from statistics import mean
from summarize import cv_interval

def verify_pair(folder):
    config=json.loads((folder/'config.json').read_text())
    meta=json.loads((folder/'metadata.json').read_text())
    saved=json.loads((folder/'summary.json').read_text())
    if meta['status']!='complete':raise ValueError('Incomplete comparison')
    if sha256(folder/'raw.csv')!=meta['raw_sha256']:raise ValueError('Raw CSV hash mismatch')
    if sha256(folder/'observations.jsonl')!=meta['observations_sha256']:raise ValueError('JSONL hash mismatch')
    for path,expected in meta['source_sha256'].items():
        source=(folder/'source'/path).resolve()
        if not source.is_relative_to((folder/'source').resolve()) or sha256(source)!=expected:
            raise ValueError('Source snapshot mismatch')
    with (folder/'raw.csv').open(newline='') as stream:rows=list(csv.DictReader(stream))
    details=[json.loads(line) for line in (folder/'observations.jsonl').read_text().splitlines()]
    if len(rows)!=len(details):raise ValueError('Raw representations have different lengths')
    for row,d in zip(rows,details):
        if d['exit_code']!=0 or d['payload']['valid'] is not True:raise ValueError('Incorrect or failed process')
        if row['arm']!=d['arm'] or int(row['round'])!=d['round'] or int(row['order'])!=d['order']:raise ValueError('Pair/order mismatch')
        for key in ['seconds','internal_seconds','process_seconds']:
            if float(row[key])!=d[key]:raise ValueError('Timing mismatch')
        if json.loads(row['checksum'])!=d['payload']['checksum']:raise ValueError('Checksum mismatch')
    recomputed=analyze_rows(config,rows)
    for key in recomputed:
        if recomputed[key]!=saved[key]:raise ValueError('Saved summary does not reproduce: '+key)
    order_effect={}
    for arm in config['arms']:
        values=[[float(r['seconds']) for r in rows if r['arm']==arm['name'] and int(r['order'])==order] for order in [0,1]]
        order_effect[arm['name']]=None if not all(values) else dict(first_n=len(values[0]),second_n=len(values[1]),
            second_position_change_percent=100*(mean(values[1])/mean(values[0])-1),limitation='descriptive, small/unbalanced groups; no order-causality test')
    arrays=[[float(r['seconds']) for r in sorted(rows,key=lambda r:int(r['round'])) if r['arm']==a['name']] for a in config['arms']]
    cpu_arrays=[[d['payload'].get('process_cpu_seconds_per_operation') for d in details if d['arm']==a['name']] for a in config['arms']]
    cpu_comparison=None
    if all(len(values)>=5 and all(v is not None and v>0 for v in values) for values in cpu_arrays):
        cpu_comparison=compare(*cpu_arrays,threshold=5,seed=config['seed'])
    return dict(name=config['name'],phase=config.get('phase'),**saved,order_effect=order_effect,observations=len(rows),
                exploratory_cv_ratio_ci95=cv_interval(*arrays,seed=config['seed']),cpu_time_comparison=cpu_comparison)

def native(folder):
    manifest=json.loads((folder/'suite.json').read_text())
    if manifest['status']!='complete':raise ValueError('Incomplete suite')
    records=[verify_pair(folder/name) for name in manifest['experiments']]
    out=folder/'analysis';out.mkdir(exist_ok=True)
    write_json(out/'reanalyzed.json',records)
    lines=['# Native upgrade measurements','',
        'Fresh-process paired observations on the office Windows host. Original 5000-draw classifier, fixed5% threshold. Exploratory selection, confirmation, measured work interventions and separate diagnostics are labeled. No real upstream Java library was executed.', '',
        '| Comparison | Stage | Change % | 95% interval % | Decision |', '|---|---|---:|---|---|']
    for r in records:
        c=r['comparison'];lo,hi=c['ci95_percent']
        lines.append(f"| {r['name']} | {r['phase']} | {c['change_percent']:+.2f} | [{lo:+.2f}, {hi:+.2f}] | {c['decision']} |")
    lines+=['','## Secondary resources and limits','',
        'secondary_metrics in reanalyzed.json retains per-arm CPU-time, allocated-byte and throughput means/min/max. CPU-time granularity can create zero/small samples. Per-thread allocation is not peak working set or total JVM allocation; management calls have observer cost. Throughput is the reciprocal time for this batch operation, not an independent application-level benefit. No customer SLA is available: the runtime decision uses a prespecified relative >5% improvement goal and observed CPU mean <=+10%.',
        '', 'Order-group changes, half-run drift and lag-one correlations are descriptive diagnostics, not proof of independent sampling or causal order effects. No multiple-comparison correction or general detector accuracy claim is made. Nominal extra-work fractions do not establish true timing effects. Inconclusive measured outcomes remain inconclusive.']
    (out/'RESULTS.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,ax=plt.subplots(figsize=(11,max(6,len(records)*.3)))
    for i,r in enumerate(records):
        c=r['comparison'];ax.plot(c['ci95_percent'],[i,i],color='tab:blue');ax.plot(c['change_percent'],i,'o',color='tab:blue')
    ax.set_yticks(range(len(records)),[r['name'] for r in records]);ax.invert_yaxis();ax.axvspan(-5,5,color='gray',alpha=.15)
    ax.set_xlabel('Candidate relative mean internal-time change (%)');fig.tight_layout();fig.savefig(out/'effects.png',dpi=160);plt.close(fig)
    return dict(comparisons=len(records),observations=sum(r['observations'] for r in records),status='all raw, source and summary checks passed')

def synthetic(folder):
    plan=json.loads((folder/'plan.json').read_text());saved=json.loads((folder/'summary.json').read_text())
    if sha256(folder/'synthetic-pairs.csv')!=saved['raw_sha256'] or sha256(folder/'classifications.jsonl')!=saved['classifications_sha256']:
        raise ValueError('Synthetic raw hash mismatch')
    groups=defaultdict(list)
    with (folder/'synthetic-pairs.csv').open(newline='') as stream:
        for row in csv.DictReader(stream):groups[(float(row['effect']),float(row['cv']),int(row['run']))].append(row)
    classifications=[json.loads(line) for line in (folder/'classifications.jsonl').read_text().splitlines()]
    if len(groups)!=len(classifications):raise ValueError('Synthetic dataset count mismatch')
    for record in classifications:
        rows=sorted(groups[(record['effect'],record['cv'],record['run'])],key=lambda r:int(r['pair']))
        if [int(r['pair']) for r in rows]!=list(range(1,21)):raise ValueError('Incomplete synthetic pairs')
        result=compare([float(r['reference']) for r in rows],[float(r['candidate']) for r in rows],threshold=5,seed=record['bootstrap_seed'],samples=5000)
        if result!=record['comparison']:raise ValueError('Synthetic classification does not reproduce')
    for group in saved['groups']:
        actual=Counter(r['comparison']['decision'] for r in classifications if r['effect']==group['effect'] and r['cv']==group['cv'])
        if any(actual[name]!=count for name,count in group['outcomes'].items()):raise ValueError('Synthetic count mismatch')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(1,2,figsize=(10,4))
    for ax,key,title in zip(axes,['regression_flag_rate','inconclusive_frequency'],['Regression flag frequency','Inconclusive frequency']):
        matrix=[[next(r[key] for r in saved['groups'] if r['effect']==effect and r['cv']==cv) for effect in plan['effects']] for cv in plan['cvs']]
        image=ax.imshow(matrix,vmin=0,vmax=1,aspect='auto');ax.set_xticks(range(6),[f'{v:+.0%}' for v in plan['effects']]);ax.set_yticks(range(3),plan['cvs']);ax.set_xlabel('Synthetic population mean effect');ax.set_ylabel('Residual lognormal CV parameter');ax.set_title(title);fig.colorbar(image,ax=ax)
    fig.tight_layout();fig.savefig(folder/'synthetic-operating-characteristics.png',dpi=160);plt.close(fig)
    return dict(datasets=len(classifications),independent_runs_per_cell=plan['runs'],status='all synthetic raw classifications and counts exactly reproduced',
                limitation='synthetic model only; no real-world detector-accuracy claim')

def main():
    p=argparse.ArgumentParser();p.add_argument('folder',type=Path);p.add_argument('--kind',choices=['native','synthetic'],required=True);a=p.parse_args()
    result=native(a.folder) if a.kind=='native' else synthetic(a.folder)
    write_json(a.folder/'verification.json',result);print(json.dumps(result))

if __name__=='__main__':main()
