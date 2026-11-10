"""Synthetic operating characteristics of the unchanged 5000-draw classifier."""
import argparse
import csv
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import random
import sys
import time
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from analyze import compare
from perflens import sha256,write_json
from summarize import exact_binomial_interval

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--output',type=Path)
    p.add_argument('--runs',type=int,default=30)
    a=p.parse_args()
    if a.runs<1:
        p.error('At least one independent generated dataset required')
    folder=a.output or ROOT/'results'/('upgrade-synthetic-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
    folder.mkdir()
    plan=dict(evidence_class='synthetic distributional study; NOT benchmark observations',effects=[0,.02,.05,.10,.30,-.15],
              cvs=[.01,.05,.20],runs=a.runs,pairs=20,seed_base=831000,bootstrap_samples=5000,threshold=5,
              data_generating_process='Independent lognormal arm residuals around common lognormal pair factor; arithmetic population means ratio 1+effect; separate generation/bootstrap PRNG seeds',
              boundary='effect .05 is a threshold-boundary case, excluded from binary truth counts',analyzer_sha256=sha256(ROOT/'analyze.py'))
    write_json(folder/'plan.json',plan)
    records=[]
    start=time.perf_counter()
    with (folder/'synthetic-pairs.csv').open('w',newline='',encoding='utf-8') as stream,(folder/'classifications.jsonl').open('w',encoding='utf-8') as details:
        writer=csv.writer(stream);writer.writerow(['effect','cv','run','pair','reference','candidate','seed'])
        for e,effect in enumerate(plan['effects']):
            for c,cv in enumerate(plan['cvs']):
                sigma=math.sqrt(math.log1p(cv*cv))
                for run in range(a.runs):
                    seed=plan['seed_base']+10000*e+100*c+run
                    rng=random.Random(seed)
                    old=[];new=[]
                    for pair in range(20):
                        factor=rng.lognormvariate(-sigma*sigma/8,sigma/2)
                        x=factor*rng.lognormvariate(-sigma*sigma/2,sigma)
                        y=factor*(1+effect)*rng.lognormvariate(-sigma*sigma/2,sigma)
                        old.append(x);new.append(y);writer.writerow([effect,cv,run,pair+1,x,y,seed])
                    bootstrap_seed=seed+7000000
                    result=compare(old,new,threshold=5,seed=bootstrap_seed,samples=5000)
                    record=dict(effect=effect,cv=cv,run=run,seed=seed,bootstrap_seed=bootstrap_seed,comparison=result)
                    details.write(json.dumps(record)+'\n');details.flush();records.append(record)
                print('synthetic',effect,cv,'done',flush=True)
    summaries=[]
    for effect in plan['effects']:
        for cv in plan['cvs']:
            group=[r for r in records if r['effect']==effect and r['cv']==cv]
            counts={name:sum(r['comparison']['decision']==name for r in group) for name in ['regression','improvement','within_threshold','inconclusive']}
            n=len(group);k=counts['regression']
            summaries.append(dict(effect=effect,cv=cv,n=n,outcomes=counts,
                truth='boundary' if effect==.05 else 'regression' if effect>.05 else 'nonregression',
                regression_flag_rate=k/n,regression_flag_ci95=exact_binomial_interval(k,n),
                false_negatives_decisive=(counts['within_threshold']+counts['improvement']) if effect>.05 else None,
                missed_detections_including_inconclusive=(n-k) if effect>.05 else None,
                false_positives=k if effect<.05 else None,
                true_negatives_decisive=(counts['within_threshold']+counts['improvement']) if effect<.05 else None,
                inconclusive_frequency=counts['inconclusive']/n,
                empirical_interval_coverage=sum(r['comparison']['ci95_percent'][0]<=100*effect<=r['comparison']['ci95_percent'][1] for r in group)/n))
    write_json(folder/'summary.json',dict(groups=summaries,elapsed_seconds=time.perf_counter()-start,
        raw_sha256=sha256(folder/'synthetic-pairs.csv'),classifications_sha256=sha256(folder/'classifications.jsonl'),
        limitation='Only specified synthetic lognormal model; no calibrated detector accuracy on arbitrary hardware/software'))
    lines=['# Synthetic classifier operating characteristics','',
        'Generated distributions, not benchmark observations. The original 5000-resample classifier and5% rule are unchanged. Every cell contains independent generated20-pair datasets with separate generation and bootstrap random streams. Boundary+5% cases are not binary ground truth. Inconclusive decisions are reported separately from decisive false negatives.', '',
        '| True mean effect | Residual CV | Runs | Regression | Improvement | Within | Inconclusive | Empirical interval coverage |',
        '|---|---|---:|---:|---:|---:|---:|---:|']
    for g in summaries:
        c=g['outcomes'];lines.append(f"| {g['effect']:+.0%} | {g['cv']:.0%} | {g['n']} | {c['regression']} | {c['improvement']} | {c['within_threshold']} | {c['inconclusive']} | {g['empirical_interval_coverage']:.1%} |")
    lines+=['','Each flag-rate exact binomial interval and confusion counts are retained in summary.json. Empirical coverage here is conditional on this simulation model and modest repetitions, not proof of nominal coverage or independence for real timing runs. No measured nominal work fraction is used as a guaranteed timing-effect label.']
    (folder/'RESULTS.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print('SYNTHETIC_FOLDER='+str(folder),flush=True)

if __name__=='__main__':
    main()
