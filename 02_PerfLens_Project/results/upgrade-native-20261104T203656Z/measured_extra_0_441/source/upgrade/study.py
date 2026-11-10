"""Additive paired experiments and resource metrics using the original classifier."""
import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
import os
import platform
from pathlib import Path
import random
import shutil
from statistics import mean
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from perflens import observe, analyze_rows, validate_config, write_json, sha256
from upgrade.metrics import permitted_jvm, recommend, dependence
from upgrade.topology import cpu_sets, diagnostic_probe
import psutil

def source_snapshot(folder):
    paths=[ROOT/'perflens.py',ROOT/'process_control.py',ROOT/'analyze.py',ROOT/'workloads/SearchBench.java']
    paths+=sorted(p for p in (ROOT/'upgrade').rglob('*') if p.is_file() and p.suffix in {'.py','.java','.json','.xml','.sh','.md'})
    for path in paths:
        target=folder/'source'/path.relative_to(ROOT)
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(path,target)
    return {p.relative_to(ROOT).as_posix():sha256(p) for p in paths}

def paired(folder,config):
    validate_config(config)
    folder.mkdir()
    write_json(folder/'config.json',config)
    sources=source_snapshot(folder)
    metadata=dict(status='running',started_utc=datetime.now(timezone.utc).isoformat(),source_sha256=sources,
                  platform=sys.platform,python=sys.version,sampling_unit='one fresh process',
                  probe_limit='system-wide frequency/context switches are supporting diagnostics, not process attribution')
    write_json(folder/'metadata.json',metadata)
    rows=[]
    details=[]
    rng=random.Random(config['seed'])
    try:
        with (folder/'raw.csv').open('w',newline='',encoding='utf-8') as stream,(folder/'observations.jsonl').open('w',encoding='utf-8') as out:
            writer=csv.DictWriter(stream,fieldnames=['round','order','arm','seconds','internal_seconds','process_seconds','checksum'])
            writer.writeheader()
            for number in range(1,config['rounds']+1):
                arms=config['arms'].copy()
                rng.shuffle(arms)
                for order,arm in enumerate(arms):
                    before=diagnostic_probe()
                    observation=observe(arm,{},config.get('timeout',120))
                    after=diagnostic_probe()
                    row=dict(round=number,order=order,arm=arm['name'],seconds=observation['seconds'],
                        internal_seconds=observation['internal_seconds'],process_seconds=observation['process_seconds'],
                        checksum=json.dumps(observation['payload']['checksum'],sort_keys=True))
                    writer.writerow(row);stream.flush();rows.append(row)
                    detail=dict(round=number,order=order,arm=arm['name'],exit_code=0,**observation,
                                supporting_before=before,supporting_after=after)
                    out.write(json.dumps(detail)+'\n');out.flush();details.append(detail)
                print(config['name'],number,'/',config['rounds'],flush=True)
        result=analyze_rows(config,rows)
        result['secondary_metrics']={}
        result['dependence']={}
        for arm in config['arms']:
            selected=[d for d in details if d['arm']==arm['name']]
            result['secondary_metrics'][arm['name']]={}
            for key in ['process_cpu_seconds_per_operation','thread_allocated_bytes_per_operation','throughput_ops_per_second']:
                values=[d['payload'][key] for d in selected if d['payload'].get(key) is not None]
                result['secondary_metrics'][arm['name']][key]=None if not values else dict(n=len(values),mean=mean(values),min=min(values),max=max(values))
            result['dependence'][arm['name']]=dependence([d['seconds'] for d in selected])
        if any(sha256(ROOT/name)!=expected for name,expected in sources.items()):
            raise ValueError('Source changed during the experiment')
        write_json(folder/'summary.json',result)
        metadata.update(status='complete',raw_sha256=sha256(folder/'raw.csv'),observations_sha256=sha256(folder/'observations.jsonl'))
        return result
    except BaseException as error:
        metadata.update(status='failed',error=repr(error))
        write_json(folder/'failure.json',getattr(error,'evidence',dict(error=repr(error))))
        raise
    finally:
        metadata['finished_utc']=datetime.now(timezone.utc).isoformat()
        write_json(folder/'metadata.json',metadata)

def java_command(java,setting='default',variant='optimized',loops=2000,warmups=100):
    return [java,*permitted_jvm(setting),'-cp',str(ROOT/'build/upgrade'),'MetricsBench',variant,str(loops),str(warmups)]

def config(name,arms,seed,rounds=10,phase='confirmatory'):
    return dict(name=name,arms=arms,seed=seed,rounds=rounds,threshold=5,timeout=120,phase=phase,
                target='>5% internal-time improvement against reference, with observed CPU ratio <=1.10 for runtime recommendation')

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--java',default=os.environ.get('PERFLENS_JAVA',r'C:\Program Files\Java\jdk-21\bin\java.exe'))
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    os.chdir(ROOT)
    os.environ.update(TEMP=str(ROOT/'.tmp'),TMP=str(ROOT/'.tmp'),PYTHONDONTWRITEBYTECODE='1')
    folder=args.output or ROOT/'results'/('upgrade-native-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
    folder.mkdir()
    (ROOT/'build/upgrade').mkdir(parents=True,exist_ok=True)
    build=[str(Path(args.java).with_name('javac.exe' if os.name=='nt' else 'javac')),'-d',str(ROOT/'build/upgrade'),str(ROOT/'workloads/SearchBench.java'),str(ROOT/'upgrade/workloads/MetricsBench.java')]
    started=datetime.now(timezone.utc).isoformat()
    result=subprocess.run(build,capture_output=True,text=True,timeout=60)
    write_json(folder/'build.json',dict(command=build,started_utc=started,returncode=result.returncode,stdout=result.stdout,stderr=result.stderr))
    if result.returncode:
        raise RuntimeError('Trusted project Java workload failed to compile')
    topology=cpu_sets()
    write_json(folder/'topology.json',topology)
    write_json(folder/'environment.json',dict(role='office Windows native',physical_host='same office context',
        platform=platform.platform(),processor=platform.processor(),node_sha256=hashlib.sha256(platform.node().encode()).hexdigest(),
        git_revision=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        power_plan=subprocess.run(['powercfg','/getactivescheme'],capture_output=True,text=True).stdout if os.name=='nt' else 'not collected',
        python=sys.version,affinity=psutil.Process().cpu_affinity(),java=subprocess.run([args.java,'-version'],capture_output=True,text=True).stderr,
        java_classes={p.name:sha256(p) for p in (ROOT/'build/upgrade').glob('*.class')},probe=diagnostic_probe()))
    training=[]
    manifest=dict(status='running',experiments=[],plan=dict(training_settings=['tier1','interpreter'],training_pairs=8,confirmation_pairs=10,
                  measured_control_extra=[0,.01,.05,.15,.5],measured_seeds=[441,442,443],measured_pairs=5),started_utc=started)
    write_json(folder/'suite.json',manifest)
    def execute(c):
        r=paired(folder/c['name'],c)
        manifest['experiments'].append(c['name']);write_json(folder/'suite.json',manifest)
        return r
    try:
        for i,setting in enumerate(['tier1','interpreter']):
            r=execute(config('runtime_training_'+setting,[dict(name='default',command=java_command(args.java)),dict(name=setting,command=java_command(args.java,setting))],410+i,8,'exploratory'))
            training.append((setting,r))
        candidate=min(training,key=lambda item:item[1]['comparison']['change_percent'])[0]
        r=execute(config('runtime_confirmation',[dict(name='default',command=java_command(args.java)),dict(name=candidate,command=java_command(args.java,candidate))],420))
        cpu=r['secondary_metrics']
        a=cpu['default']['process_cpu_seconds_per_operation'];b=cpu[candidate]['process_cpu_seconds_per_operation']
        ratio=b['mean']/a['mean'] if a and b and a['mean']>0 else None
        write_json(folder/'recommendation.json',dict(exploratory_candidate=candidate,
            decision=recommend('default',candidate,r['comparison'],True,ratio),cpu_mean_ratio=ratio,
            confirmation_seed=420,threshold=5))
        execute(config('algorithm_resource_tradeoff',[dict(name='linear',command=java_command(args.java,variant='baseline',loops=1000,warmups=20)),
            dict(name='binary',command=java_command(args.java,variant='optimized',loops=1000,warmups=20))],430,8))
        allowed=psutil.Process().cpu_affinity()
        sets=[row for row in topology.get('cpu_sets',[]) if row['group']==0 and row['logical'] in allowed]
        if sets:
            fast=max(sets,key=lambda row:row['efficiency_class'])
            same=next((row for row in sets if row['efficiency_class']==fast['efficiency_class'] and row['core']!=fast['core']),None)
            slow=min(sets,key=lambda row:row['efficiency_class'])
            if same:
                execute(config('same_class_contention_mitigation',[
                    dict(name='same_cpu_load',command=java_command(args.java),cpu=fast['logical'],load=True),
                    dict(name='separate_same_class',command=java_command(args.java),cpu=same['logical'],load=True,load_cpu=fast['logical'])],435))
            if slow['efficiency_class']!=fast['efficiency_class']:
                execute(config('heterogeneous_core_policy',[
                    dict(name='higher_class',command=java_command(args.java),cpu=fast['logical']),
                    dict(name='lower_class',command=java_command(args.java),cpu=slow['logical'])],436))
        for seed in [441,442,443]:
            for extra in [0,.01,.05,.15,.5]:
                name=f'measured_extra_{extra}_{seed}'.replace('.','p')
                execute(config(name,[dict(name='unchanged_reference',command=['{python}','{root}/upgrade/workloads/redundant.py','--extra','0']),
                    dict(name='work_intervention',command=['{python}','{root}/upgrade/workloads/redundant.py','--extra',str(extra)])],seed,5,'measured calibration intervention; effect truth unknown'))
        execute(config('measured_improvement',[dict(name='extra_reference',command=['{python}','{root}/upgrade/workloads/redundant.py','--extra','.5']),
            dict(name='removed_work',command=['{python}','{root}/upgrade/workloads/redundant.py','--extra','0'])],450,10))
        manifest['status']='complete'
    except BaseException as error:
        manifest.update(status='failed',error=repr(error));raise
    finally:
        manifest['finished_utc']=datetime.now(timezone.utc).isoformat();write_json(folder/'suite.json',manifest)
    print('NATIVE_FOLDER='+str(folder),flush=True)

if __name__=='__main__':
    main()
