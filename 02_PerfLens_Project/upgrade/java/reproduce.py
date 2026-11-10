"""Prepared isolated RoaringBitmap/JMH gates. Never execute upstream code on host."""
import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import random
import shutil
import stat
import subprocess
import sys
import time
import urllib.request
import uuid
import zipfile
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from analyze import compare
from upgrade.metrics import jmh_single_fork

SHAS=['2dfd0fb994468c8d416dea3d217dc40ca7d6d145','684531c13877fbdacccf02262b32e6faf889d76f']
CACHE=ROOT/'.tmp/j845'
STATE=CACHE/'state.json'
def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2),encoding='utf-8')
def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
def command(args,log,timeout=300,container=None):
    start=time.monotonic()
    try:
        r=subprocess.run(args,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=timeout)
        data=dict(command=args,returncode=r.returncode,stdout=r.stdout,stderr=r.stderr,elapsed_seconds=time.monotonic()-start)
    except subprocess.TimeoutExpired as error:
        if container:
            subprocess.run(['docker','rm','-f',container],capture_output=True,timeout=30)
        data=dict(command=args,returncode=None,stdout=str(error.stdout),stderr=str(error.stderr),error='timeout',elapsed_seconds=time.monotonic()-start)
    write(log,data)
    if data['returncode']!=0:
        raise RuntimeError('Command failed; retained '+str(log))
    return data['stdout']
def container_args(image,source,output,name):
    return ['docker','run','--rm','--name',name,'--init','--read-only','--network','none','--cap-drop','ALL',
            '--security-opt','no-new-privileges','--pids-limit','256','--memory','2g','--cpus','2','--user','10001:10001',
            '--tmpfs','/tmp:rw,nosuid,nodev,size=256m',
            '--mount','type=bind,source='+str(source)+',target=/src,readonly',
            '--mount','type=bind,source='+str(output)+',target=/out',image]
def load():
    if not STATE.exists():
        raise RuntimeError('Run --prepare in a working isolated environment first')
    return json.loads(STATE.read_text())
def prepare():
    CACHE.mkdir(parents=True,exist_ok=True)
    folder=ROOT/'results'/('upgrade-java-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
    folder.mkdir()
    # Fail before even downloading source if isolation is absent.
    command(['docker','info'],folder/'docker-preflight.json',30)
    state=dict(folder=str(folder),sources={},shas=SHAS,status='preparing',executed=False)
    for sha in SHAS:
        url='https://codeload.github.com/RoaringBitmap/RoaringBitmap/zip/'+sha
        archive=folder/'inputs'/(sha+'.zip');archive.parent.mkdir(exist_ok=True)
        with urllib.request.urlopen(url,timeout=60) as response:
            data=response.read(100_000_001)
        if len(data)>100_000_000:
            raise ValueError('Unexpected source archive size')
        archive.write_bytes(data)
        # Short local paths avoid Windows MAX_PATH; full SHA remains in provenance.
        source=CACHE/'src'/sha[:12]
        if source.exists():
            raise RuntimeError('Source cache exists; inspect before reuse instead of overwriting')
        source.mkdir(parents=True)
        with zipfile.ZipFile(archive) as z:
            if sum(i.file_size for i in z.infolist())>300_000_000:
                raise ValueError('Expanded source archive exceeds fixed budget')
            for item in z.infolist():
                parts=Path(item.filename).parts[1:]
                if not parts or item.is_dir():continue
                if stat.S_ISLNK(item.external_attr>>16):raise ValueError('Symlink source rejected')
                target=source.joinpath(*parts).resolve()
                if not target.is_relative_to(source.resolve()):raise ValueError('Unsafe ZIP source path')
                target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(z.read(item))
        state['sources'][sha]=dict(url=url,archive=str(archive),sha256=digest(archive),directory=str(source),
            source_sha256={p.relative_to(source).as_posix():digest(p) for p in source.rglob('*') if p.is_file()})
    tag='perflens-jmh845:prepared'
    command(['docker','build','--tag',tag,str(ROOT/'upgrade/java')],folder/'image-build.json',900)
    state['image_id']=command(['docker','image','inspect','--format','{{.Id}}',tag],folder/'image-id.json',30).strip()
    state['status']='prepared'
    state['harness_sha256']={p.relative_to(ROOT/'upgrade/java').as_posix():digest(p) for p in (ROOT/'upgrade/java').rglob('*') if p.is_file()}
    write(STATE,state);write(folder/'preparation.json',state)
    print(folder)
def pilot():
    state=load();folder=Path(state['folder'])
    checks=[]
    for name,expected in state['harness_sha256'].items():
        if digest(ROOT/'upgrade/java'/name)!=expected:raise RuntimeError('Harness changed after preparation')
    for sha in SHAS:
        output=CACHE/'built'/sha;output.mkdir(parents=True,exist_ok=True)
        name='perflens-pilot-'+uuid.uuid4().hex[:12]
        base=container_args(state['image_id'],Path(state['sources'][sha]['directory']),output,name)
        text=command(base+['/bin/sh','/harness/build-roaring.sh'],folder/('build-'+sha+'.json'),300,name)
        correctness=[json.loads(line) for line in text.splitlines() if line.startswith('{"valid":')]
        if len(correctness)!=1 or correctness[0].get('valid') is not True:raise RuntimeError('Missing correctness evidence')
        checks.append(correctness[0])
        cp=(output/'classpath.txt').read_text().strip()
        name='perflens-smoke-'+uuid.uuid4().hex[:12]
        base=container_args(state['image_id'],Path(state['sources'][sha]['directory']),output,name)
        command(base+['java','-Xms512m','-Xmx512m','-cp',cp,'org.openjdk.jmh.Main','perflens.external.RankBenchmark.rank',
            '-p','limit=65535','-p','containers=16','-f','1','-t','1','-wi','1','-i','1','-w','100ms','-r','100ms',
            '-rf','json','-rff','/out/pilot.json'],folder/('pilot-'+sha+'.json'),90,name)
        jmh_single_fork(json.loads((output/'pilot.json').read_text()))
        shutil.copy2(output/'pilot.json',folder/('pilot-jmh-'+sha+'.json'))
    if checks[0]!=checks[1]:raise RuntimeError('Before/after correctness results differ')
    state['correctness']=checks
    state['status']='both compatibility and correctness pilots passed'
    write(STATE,state);write(folder/'pilot-status.json',state)
def measure():
    state=load();folder=Path(state['folder'])
    if state['status']!='both compatibility and correctness pilots passed':
        raise RuntimeError('Both real library pilots must pass before measurement')
    for name,expected in state['harness_sha256'].items():
        if digest(ROOT/'upgrade/java'/name)!=expected:raise RuntimeError('Harness changed after preparation')
    plan=dict(rounds=10,threshold=5,warmup_iterations=3,warmup_time='200ms',measurement_iterations=3,measurement_time='300ms',
              sampling_unit='one JMH fork; iterations retained within fork',workloads=[('rank','65535'),('rank','65534'),('fullContainerRange','65535')],
              shas=SHAS,phase='confirmatory after compatibility pilot; no tuning to outcomes')
    write(folder/'measurement-plan.json',plan)
    for case,(method,limit) in enumerate(plan['workloads']):
        target=folder/(method+'-'+limit);target.mkdir()
        rows=[];rng=random.Random(8450+case)
        with (target/'raw.csv').open('w',newline='') as stream:
            writer=csv.DictWriter(stream,fieldnames=['round','order','sha','seconds']);writer.writeheader()
            for number in range(1,11):
                order=SHAS.copy();rng.shuffle(order)
                for position,sha in enumerate(order):
                    output=CACHE/'built'/sha
                    cp=(output/'classpath.txt').read_text().strip()
                    filename=f'{case}-{number}-{position}.json'
                    name='perflens-jmh-'+uuid.uuid4().hex[:12]
                    args=container_args(state['image_id'],Path(state['sources'][sha]['directory']),output,name)
                    args+=['java','-Xms512m','-Xmx512m','-cp',cp,'org.openjdk.jmh.Main','perflens.external.RankBenchmark.'+method,
                           '-p','limit='+limit,'-p','containers=16','-f','1','-t','1','-wi','3','-i','3','-w','200ms','-r','300ms',
                           '-rf','json','-rff','/out/'+filename]
                    command(args,target/(filename+'.command.json'),120,name)
                    raw=json.loads((output/filename).read_text())
                    point=jmh_single_fork(raw)
                    row=dict(round=number,order=position,sha=sha,seconds=point['seconds'])
                    rows.append(row);writer.writerow(row);stream.flush();write(target/filename,raw)
        arrays=[[r['seconds'] for r in sorted(rows,key=lambda r:r['round']) if r['sha']==sha] for sha in SHAS]
        write(target/'summary.json',dict(comparison=compare(*arrays,threshold=5,seed=8450+case),raw_sha256=digest(target/'raw.csv'),
            limitation='virtualized environment on same physical host; no independent-host claim'))
    print('Measured results:',folder)
def main():
    p=argparse.ArgumentParser(description=__doc__)
    group=p.add_mutually_exclusive_group(required=True)
    group.add_argument('--prepare',action='store_true');group.add_argument('--pilot',action='store_true');group.add_argument('--measure',action='store_true')
    a=p.parse_args()
    if a.prepare:prepare()
    elif a.pilot:pilot()
    else:measure()
if __name__=='__main__':main()
