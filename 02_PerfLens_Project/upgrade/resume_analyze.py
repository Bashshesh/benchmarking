"""Independent re-ingestion of retained JMH forks, XML tests and JFR evidence."""
import argparse,csv,hashlib,json,math,random,re,statistics,sys,zipfile
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
import xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from analyze import compare,descriptive
from upgrade.metrics import jmh_single_fork,dependence
from upgrade.java.reproduce import SHAS,write,digest
from summarize import cv_interval

def circular_block_interval(old,new):
    # Exploratory dependence sensitivity, not a replacement decision rule.
    rng=random.Random(84552);n=len(old);effects=[]
    for _ in range(5000):
        indices=[]
        while len(indices)<n:
            start=rng.randrange(n);indices.extend([start,(start+1)%n])
        indices=indices[:n]
        effects.append(100*(statistics.mean(new[i] for i in indices)/statistics.mean(old[i] for i in indices)-1))
    effects.sort();return [effects[124],effects[4874]]

def validate_case(case,arms,seed,original=False):
    rows=list(csv.DictReader((case/'raw.csv').open(newline='')))
    n=len(rows)//2
    assert n>=5 and len(rows)==n*2
    rng=random.Random(seed);arrays={a:[] for a in arms};iteration_cv={a:[] for a in arms}
    command_capture_warnings=0
    quota_diagnostics=[]
    for number in range(1,n+1):
        order=arms.copy();rng.shuffle(order)
        r=[row for row in rows if int(row['round'])==number]
        assert len(r)==2 and {int(v['order']) for v in r}=={0,1}
        for row in r:
            arm=row['sha'] if original else row['arm'];position=int(row['order'])
            assert arm==order[position]
            if original:
                case_number={'rank-65535':0,'rank-65534':1,'fullContainerRange-65535':2}[case.name]
                filename=f'{case_number}-{number}-{position}.json'
            else:filename=f'{case.name}-{number}-{position}.json'
            record=json.loads((case/filename).read_text())
            point=jmh_single_fork(record)
            assert math.isclose(float(row['seconds']),point['seconds'],rel_tol=1e-14)
            value=record[0]
            assert value['jmhVersion']=='1.37' and value['threads']==1 and value['forks']==1
            assert value['warmupIterations']==3 and value['measurementIterations']==3
            assert value['warmupTime']=='200 ms' and value['measurementTime']=='300 ms'
            expected_flags=['-Xms512m','-Xmx512m']+(['-XX:TieredStopAtLevel=1'] if case.name=='runtime' and arm=='candidate' else [])
            assert value['jvmArgs']==expected_flags
            assert len(point['within_fork_iterations'])==3
            assert math.isclose(value['primaryMetric']['score'],statistics.mean(point['within_fork_iterations']),rel_tol=1e-12)
            if original:
                assert value['params']=={'containers':'16','limit':case.name.rsplit('-',1)[1]}
                assert value['benchmark'].rsplit('.',1)[1]==('fullContainerRange' if case_number==2 else 'rank')
            else:
                expected_method={'corpus-boundary':'fullBlock','corpus-near-boundary':'nearBoundary'}.get(case.name,'rank')
                assert value['benchmark'].rsplit('.',1)[1]==expected_method
                if not case.name.startswith('corpus-'):
                    assert value['params']=={'containers':'16','limit':'65535' if case.name=='guard-ablation' else '65534'}
            receipt=json.loads((case/(filename+'.command.json')).read_text())
            assert receipt['returncode']==0
            command_capture_warnings+=receipt['stdout'] is None or receipt['stderr'] is None
            text=receipt['stdout'] or ''
            counters={key:[int(v) for v in re.findall(r'^'+key+r' (\d+)$',text,re.MULTILINE)] for key in ['usage_usec','usage_nsec','nr_periods','nr_throttled','throttled_usec','throttled_time']}
            deltas={k:v[1]-v[0] for k,v in counters.items() if len(v)==2}
            if deltas:quota_diagnostics.append(dict(round=number,arm=arm,delta=deltas))
            assert any('/'+row['sha'] in arg or '\\'+row['sha'] in arg for arg in receipt['command']) or not original
            arrays[arm].append(float(row['seconds']))
            iteration_cv[arm].append(100*statistics.stdev(point['within_fork_iterations'])/statistics.mean(point['within_fork_iterations']))
    old,new=[arrays[a] for a in arms]
    summary=json.loads((case/'summary.json').read_text())
    assert digest(case/'raw.csv')==summary['raw_sha256']
    calculated=compare(old,new,threshold=5,seed=seed)
    assert calculated==summary['comparison']
    orders={a:{str(p):[float(r['seconds']) for r in rows if (r['sha'] if original else r['arm'])==a and int(r['order'])==p] for p in [0,1]} for a in arms}
    return dict(case=str(case.relative_to(ROOT)),arms=arms,pairs=n,observations=len(rows),comparison=calculated,
       summaries={a:descriptive(arrays[a]) for a in arms},dependence={a:dependence(arrays[a]) for a in arms},
       order_group_means={a:{p:statistics.mean(v) if v else None for p,v in groups.items()} for a,groups in orders.items()},
       within_fork_iteration_cv_percent=iteration_cv,
       exploratory_cv_ratio_ci95=cv_interval(old,new,seed=84551),
       circular_length2_block_bootstrap_sensitivity_ci95_percent=circular_block_interval(old,new),
       command_text_capture_warnings=command_capture_warnings,
       cgroup_quota_diagnostics=quota_diagnostics,
       derived_rate_ratio=statistics.mean(old)/statistics.mean(new),
       limitations='Small fork-pair count; shared-host/WSL drift and autocorrelation possible. Iterations are not independent observations. Derived rate is not a separate throughput experiment.')

def jfr_review(folder):
    results={}
    for path in folder.glob('*-events.json'):
        receipt=json.loads(path.read_text());assert receipt['returncode']==0
        events=json.loads(receipt['stdout'])['recording']['events']
        counts=Counter();methods=Counter();rank_stacks=Counter();tiers=Counter()
        for e in events:
            typ=e['type'];v=e['values'];counts[typ]+=1
            if typ=='jdk.Compilation':
                method=v.get('method') or {};name=method.get('name','')
                cls=(method.get('type') or {}).get('name','')
                if 'BitmapContainer' in cls and name=='rank':tiers[str(v.get('compileLevel'))]+=1
            if typ=='jdk.ExecutionSample':
                for f in (v.get('stackTrace') or {}).get('frames',[]):
                    m=f.get('method') or {};cls=(m.get('type') or {}).get('name','');name=m.get('name','')
                    methods[cls+'.'+name]+=1
                    if 'BitmapContainer' in cls and name=='rank':rank_stacks[str(f.get('lineNumber'))]+=1
        invocation=folder/(path.name.replace('-events.json','.json'))
        log=json.loads(invocation.read_text())['stdout']
        compiled=[line for line in log.splitlines() if 'org.roaringbitmap.BitmapContainer::rank' in line]
        results[path.stem]=dict(event_counts=dict(counts),rank_stack_source_lines=dict(rank_stacks),rank_compilation_levels=dict(tiers),
           rank_print_compilation=compiled,
           top_stack_frames=methods.most_common(12),limit='Same diagnostic wall budget, different operation counts/JIT inlining; raw sample counts are not speedups or causal proof')
    return results

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path)
    p.add_argument('--primary',type=Path,default=ROOT/'results/upgrade-java-20261104T233351Z')
    p.add_argument('--diagnostics',type=Path,default=ROOT/'results/resume-diagnostics-20261104T234629Z')
    p.add_argument('--clone-tests',type=Path,default=ROOT/'results/resume-clone-tests-20261104T233916Z')
    p.add_argument('--runtime-diagnostics',type=Path,default=ROOT/'results/resume-runtime-diagnostic-20261105T192348Z')
    p.add_argument('--extension',type=Path,action='append',help='Select exact extension folders; do not mix hosts or reruns')
    a=p.parse_args()
    out=a.output.resolve() if a.output else ROOT/'results'/('resume-validation-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'));out.mkdir()
    base=a.primary.resolve()
    preparation=json.loads((base/'preparation.json').read_text())
    for sha in SHAS:
        archive=base/'inputs'/(sha+'.zip')
        assert digest(archive)==preparation['sources'][sha]['sha256']
        with zipfile.ZipFile(archive) as z:
            source_hashes={item.filename.split('/',1)[1]:hashlib.sha256(z.read(item)).hexdigest()
                           for item in z.infolist() if not item.is_dir()}
        assert source_hashes==preparation['sources'][sha]['source_sha256']
        build=json.loads((base/('build-'+sha+'.json')).read_text());assert build['returncode']==0
        assert '"checksum":458211' in build['stdout'] and '"valid":true' in build['stdout']
    cases=[]
    for i,name in enumerate(['rank-65535','rank-65534','fullContainerRange-65535']):cases.append(validate_case(base/name,SHAS,8450+i,True))
    extensions=[p.resolve() for p in a.extension] if a.extension else [
        folder for prefix in ['resume-ablation-','resume-corpus-','resume-interventions-']
        for folder in sorted((ROOT/'results').glob(prefix+'*')) if (folder/'plan.json').exists()]
    for folder in extensions:
        for case in sorted(folder.glob('*/summary.json')):
            arms=json.loads((case.parent/'arms.json').read_text())['arms']
            cases.append(validate_case(case.parent,arms,84551))
    if len({Path(c['case']).name for c in cases})!=len(cases):
        raise ValueError('Duplicate case names: select a single execution per case with --extension')
    upstream={}
    for xmlfolder in a.clone_tests.glob('test-results-*'):
        stats=Counter()
        for file in xmlfolder.glob('*.xml'):
            v=ET.parse(file).getroot().attrib
            stats.update({k:int(v[k]) for k in ['tests','failures','errors','skipped']})
        assert stats['tests']>0 and not stats['failures'] and not stats['errors']
        upstream[xmlfolder.name]=dict(stats)
    assert len(upstream)==2
    diagnostics=jfr_review(a.diagnostics)
    assert len(diagnostics)==4
    runtime_diagnostics=jfr_review(a.runtime_diagnostics)
    assert len(runtime_diagnostics)==1
    incomplete=[]
    for folder in extensions:
        incomplete.extend(str(d.relative_to(ROOT)) for d in folder.iterdir() if d.is_dir() and d.name!='source' and not (d/'summary.json').exists())
    write(out/'verification.json',dict(status='all included completed JMH raw/label/pair/summary checks passed',
       case_count=len(cases),observations=sum(c['observations'] for c in cases),cases=cases,upstream_tests=upstream,diagnostics=diagnostics,
       runtime_diagnostics=runtime_diagnostics,
       incomplete_attempts_not_used_for_inference=incomplete))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    labels=[Path(c['case']).name for c in cases];effects=[c['comparison']['change_percent'] for c in cases]
    lo=[x-c['comparison']['ci95_percent'][0] for x,c in zip(effects,cases)]
    hi=[c['comparison']['ci95_percent'][1]-x for x,c in zip(effects,cases)]
    fig,ax=plt.subplots(figsize=(11,max(4,.55*len(cases))))
    ax.errorbar(effects,range(len(cases)),xerr=[lo,hi],fmt='o',capsize=3)
    ax.set_yticks(range(len(cases)),labels);ax.invert_yaxis();ax.axvspan(-5,5,color='grey',alpha=.15);ax.axvline(0,color='grey')
    ax.set_xlabel('Candidate / reference mean time change (%), paired 95% bootstrap CI')
    ax.set_title('Office Docker/WSL2 observations; separate from native Windows data')
    fig.tight_layout();fig.savefig(out/'effects.png',dpi=160);plt.close(fig)
    subset=[i for i,name in enumerate(labels) if name!='runtime']
    fig,ax=plt.subplots(figsize=(11,5.4))
    ax.errorbar([effects[i] for i in subset],range(len(subset)),xerr=[[lo[i] for i in subset],[hi[i] for i in subset]],fmt='o',capsize=3)
    ax.set_yticks(range(len(subset)),[labels[i] for i in subset]);ax.invert_yaxis();ax.axvspan(-5,5,color='grey',alpha=.15);ax.axvline(0,color='grey')
    ax.set_xlabel('Candidate / reference mean time change (%), paired 95% bootstrap CI')
    ax.set_title('Revision, input and noise effects (runtime comparison in full figure)')
    fig.tight_layout();fig.savefig(out/'effects-revision-input-noise.png',dpi=160);plt.close(fig)
    write(out/'evidence-sha256.json',{str(p.relative_to(ROOT)):digest(p) for folder in [base,*sorted((ROOT/'results').glob('resume-*'))] if folder.is_dir() and folder!=out for p in folder.rglob('*') if p.is_file() and 'project' not in p.relative_to(folder).parts})
    print(out)
if __name__=='__main__':main()
