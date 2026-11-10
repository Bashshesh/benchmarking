"""Sequential, isolated follow-up experiments; never run upstream Java on host."""
import argparse,csv,json,random,shutil,sys,time
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from upgrade.java.reproduce import load,write,digest,command,container_args,CACHE,SHAS
from upgrade.metrics import jmh_single_fork
from analyze import compare

def run(state,sha,output,args,log,timeout=300,network=False):
    import uuid
    name='perflens-extra-'+uuid.uuid4().hex[:12]
    base=container_args(state['image_id'],Path(state['sources'][sha]['directory']),output,name)
    if network:base[base.index('none')]='bridge'
    return command(base+args,log,timeout,name)

def main():
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['diagnostics','runtime-diagnostic','corpus','interventions','clone-tests','ablation'])
    p.add_argument('--case',action='append',choices=['contention','mitigation','runtime'])
    a=p.parse_args();s=load()
    if a.case and a.phase!='interventions':p.error('--case is only supported for interventions')
    folder=ROOT/'results'/('resume-'+a.phase+'-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'));folder.mkdir()
    write(folder/'plan.json',dict(phase=a.phase,shas=SHAS,image=s['image_id'],environment='Docker Desktop WSL2 on office physical host; never pooled with native',
       rounds=8,seed=84551,sampling='one independent JMH fork per arm/round; no flattened iterations',
       threshold=5,warmup='3x200ms',measurement='3x300ms',requested_cases=a.case,trust='third-party execution only in restricted Docker containers'))
    (folder/'source').mkdir()
    for f in [Path(__file__),ROOT/'upgrade/java/CorpusBenchmark.java',ROOT/'upgrade/java/RankDiagnostic.java']:
        shutil.copy2(f,folder/'source'/f.name)
    write(folder/'source-sha256.json',{f.name:digest(f) for f in (folder/'source').iterdir()})
    if a.phase=='runtime-diagnostic':
        sha=SHAS[0];out=CACHE/'built'/sha;cp=(out/'classpath.txt').read_text().strip()
        name='rank-'+sha[:12]+'-65534-tier1'
        run(s,sha,out,['java','-Xms512m','-Xmx512m','-XX:TieredStopAtLevel=1',
            '-XX:StartFlightRecording=filename=/out/'+name+'.jfr,settings=profile,dumponexit=true',
            '-Xlog:gc*,safepoint:file=/out/'+name+'-gc.log','-XX:+PrintCompilation','-cp',cp,'perflens.external.RankDiagnostic','65534'],folder/(name+'.json'))
        for suffix in ['.jfr','-gc.log']:shutil.copy2(out/(name+suffix),folder/(name+suffix))
        run(s,sha,out,['jfr','summary','/out/'+name+'.jfr'],folder/(name+'-summary.json'))
        run(s,sha,out,['jfr','print','--json','--events','jdk.ExecutionSample,jdk.Compilation,jdk.GarbageCollection,jdk.CPULoad','/out/'+name+'.jfr'],folder/(name+'-events.json'))
        print(folder);return
    if a.phase=='clone-tests':
        # No host credentials or home mount. Network only for source/dependency setup.
        out=CACHE/'git-test';out.mkdir(exist_ok=False)
        script='git clone --no-checkout --filter=blob:none https://github.com/RoaringBitmap/RoaringBitmap.git /out/repo && cd /out/repo && '
        script+='git show -s --format="%H %P" '+SHAS[1]+' && git checkout --detach '+SHAS[0]
        run(s,SHAS[0],out,['sh','-c',script],folder/'clone.json',240,True)
        for sha in SHAS:
            # Project build is confined to a copy in the dedicated output mount.
            script='cd /out/repo && git checkout --detach '+sha+' && GRADLE_USER_HOME=/out/gradle sh gradlew --no-daemon :roaringbitmap:test --tests "org.roaringbitmap.TestRank*" -Dorg.gradle.jvmargs=-Xmx768m --max-workers=1'
            try:run(s,sha,out,['sh','-c',script],folder/('gradle-'+sha+'.json'),480,True)
            except RuntimeError:pass # Preserve explicit upstream-build failure; external correctness is separate.
            xml=out/'repo/roaringbitmap/build/test-results/test'
            if xml.exists():shutil.copytree(xml,folder/('test-results-'+sha),dirs_exist_ok=True)
        return
    if a.phase=='corpus':
        src=Path(s['sources'][SHAS[0]]['directory'])
        files=sorted((src/'roaringbitmap/src/main/java').rglob('*.java'))
        corpus=b''.join(f.read_bytes() for f in files)
        (folder/'corpus.bin').write_bytes(corpus)
        shutil.copy2(src/'LICENSE',folder/'LICENSE-input.txt')
        write(folder/'dataset.json',dict(kind='application-derived source-text index proxy, not a production query trace',
          origin=s['sources'][SHAS[0]]['url'],revision=SHAS[0],license='Apache-2.0',
          preprocessing='concatenate sorted main Java source files as exact bytes; index byte offsets with unsigned byte > 32',
          byte_count=len(corpus),sha256=digest(folder/'corpus.bin'),files={f.relative_to(src).as_posix():digest(f) for f in files},
          limitations='byte-offset/text filter proxy; not representative of all real bitmap applications; same frozen input both revisions'))
    for sha in SHAS:
        out=CACHE/'built'/sha
        cp=(out/'classpath.txt').read_text().strip()
        for name in ['RankDiagnostic','CorpusBenchmark']:
            shutil.copy2(ROOT/'upgrade/java'/(name+'.java'),out/(name+'.java'))
        if a.phase=='corpus':shutil.copy2(folder/'corpus.bin',out/'corpus.bin')
        run(s,sha,out,['sh','-c','javac -cp "'+cp+'" -processorpath "'+cp+'" -processor org.openjdk.jmh.generators.BenchmarkProcessor -d /out/harness /out/RankDiagnostic.java /out/CorpusBenchmark.java'],folder/('compile-'+sha+'.json'))
    if a.phase=='diagnostics':
        for sha in SHAS:
            out=CACHE/'built'/sha;cp=(out/'classpath.txt').read_text().strip()
            run(s,sha,out,['sh','-c','uname -a; cat /proc/cpuinfo; cat /proc/self/status; cat /sys/fs/cgroup/cpu.max; command -v taskset'],folder/('environment-'+sha+'.json'))
            for limit in ['65535','65534']:
                name='rank-'+sha[:12]+'-'+limit
                run(s,sha,out,['java','-Xms512m','-Xmx512m','-XX:StartFlightRecording=filename=/out/'+name+'.jfr,settings=profile,dumponexit=true',
                    '-Xlog:gc*,safepoint:file=/out/'+name+'-gc.log','-XX:+PrintCompilation','-cp',cp,'perflens.external.RankDiagnostic',limit],folder/(name+'.json'))
                shutil.copy2(out/(name+'.jfr'),folder/(name+'.jfr'));shutil.copy2(out/(name+'-gc.log'),folder/(name+'-gc.log'))
                run(s,sha,out,['jfr','summary','/out/'+name+'.jfr'],folder/(name+'-summary.json'))
                run(s,sha,out,['jfr','print','--json','--events','jdk.ExecutionSample,jdk.Compilation,jdk.GarbageCollection,jdk.CPULoad','/out/'+name+'.jfr'],folder/(name+'-events.json'))
            run(s,sha,out,['javap','-c','-p','-classpath',cp,'org.roaringbitmap.BitmapContainer'],folder/('bytecode-'+sha+'.json'))
        return
    if a.phase=='ablation':
        ablation_out=CACHE/('abl-'+folder.name[-16:])
        out=ablation_out;shutil.copytree(CACHE/'built'/SHAS[1],out)
        source=Path(s['sources'][SHAS[1]]['directory'])/'roaringbitmap/src/main/java/org/roaringbitmap/BitmapContainer.java'
        text=source.read_text()
        guard='''    if (lowbits == Character.MAX_VALUE) {
      if (cardinality < 0) {
        computeCardinality();
      }
      return cardinality;
    }
'''
        if text.count(guard)!=1:raise ValueError('Expected unique upstream guard not found')
        (out/'BitmapContainer.java').write_text(text.replace(guard,''),encoding='utf-8')
        shutil.copy2(out/'BitmapContainer.java',folder/'source/BitmapContainer-ablated.java')
        write(folder/'ablation.json',dict(parent=SHAS[1],original_sha256=digest(source),ablated_sha256=digest(out/'BitmapContainer.java'),
            intervention='remove only MAX-value early-return guard in BitmapContainer.rank; private experimental copy, upstream untouched'))
        cp=(out/'classpath.txt').read_text().strip()
        run(s,SHAS[1],out,['javac','-proc:none','--release','8','-cp',cp,'-d','/out/library','/out/BitmapContainer.java'],folder/'ablation-compile.json')
        correctness=run(s,SHAS[1],out,['java','-cp',cp,'perflens.external.CorrectnessMain'],folder/'ablation-correctness.json')
        if json.loads(correctness)['valid'] is not True:raise ValueError('Ablation correctness failed')
    cases=[('corpus-boundary','fullBlock'),('corpus-near-boundary','nearBoundary')] if a.phase=='corpus' else ([('guard-ablation','rank')] if a.phase=='ablation' else [('contention','same-v-clean'),('mitigation','same-v-separate'),('runtime','default-v-tier1')])
    if a.case:cases=[case for case in cases if case[0] in a.case]
    for case,method in cases:
        target=folder/case;target.mkdir();rows=[];rng=random.Random(84551)
        arms=SHAS if a.phase=='corpus' else ['reference','candidate']
        write(target/'arms.json',dict(arms=arms,case=case,method=method))
        for number in range(1,9):
            order=arms.copy();rng.shuffle(order)
            for position,arm in enumerate(order):
                sha=arm if a.phase=='corpus' else (SHAS[1] if a.phase=='ablation' else SHAS[0])
                out=ablation_out if a.phase=='ablation' and arm=='reference' else CACHE/'built'/sha
                cp=(out/'classpath.txt').read_text().strip()
                filename=f'{case}-{number}-{position}.json'
                flags=['-XX:TieredStopAtLevel=1'] if case=='runtime' and arm=='candidate' else []
                bench='perflens.external.CorpusBenchmark.'+method if a.phase=='corpus' else 'perflens.external.RankBenchmark.rank'
                args=['java','-Xms512m','-Xmx512m','-cp',cp,'org.openjdk.jmh.Main',bench,'-f','1','-t','1','-wi','3','-i','3','-w','200ms','-r','300ms',
                    '-rf','json','-rff','/out/'+filename]
                if a.phase!='corpus':args+=['-p','limit='+('65535' if a.phase=='ablation' else '65534'),'-p','containers=16']
                if flags:args+=['-jvmArgsAppend',' '.join(flags)]
                if case in ['contention','mitigation']:
                    # Select allowed virtual CPUs at runtime. No physical core-class claim.
                    import shlex
                    busy=(case=='contention' and arm=='candidate') or case=='mitigation'
                    separate=case=='mitigation' and arm=='candidate'
                    prefix='''stats(){
 for p in /sys/fs/cgroup/cpu.stat /sys/fs/cgroup/cpu/cpu.stat /sys/fs/cgroup/cpu,cpuacct/cpu.stat; do
  if [ -r "$p" ]; then
   echo "# cgroup counters $p"; cat "$p";
   if [ -r "${p%/*}/cpuacct.usage" ]; then printf 'usage_nsec '; cat "${p%/*}/cpuacct.usage"; fi
   return;
  fi;
 done;
 echo '# cgroup CPU counters unavailable';
};
cpus=$(taskset -pc $$ | sed "s/.*: //");
first=$(echo "$cpus" | cut -d, -f1 | cut -d- -f1); second=$((first+1));
echo "# allowed CPUs $cpus; benchmark CPU $first"; stats;
'''
                    if busy:
                        cpu='$second' if separate else '$first'
                        prefix+='taskset -c '+cpu+' true || exit 42; echo "# load CPU '+cpu+'"; taskset -c '+cpu+' sh -c "while :; do :; done" & load=$!; '
                        prefix+='cleanup(){ kill "$load" 2>/dev/null || :; wait "$load" 2>/dev/null || :; }; trap cleanup EXIT; '
                    suffix='; status=$?; '+('cleanup; trap - EXIT; ' if busy else '')+'stats; exit "$status"'
                    args=['sh','-c',prefix+'taskset -c "$first" '+shlex.join(args)+suffix]
                run(s,sha,out,args,target/(filename+'.command.json'))
                raw=json.loads((out/filename).read_text());point=jmh_single_fork(raw)
                rows.append(dict(round=number,order=position,arm=arm,sha=sha,seconds=point['seconds']))
                write(target/filename,raw)
                write(target/'progress.json',dict(status='incomplete until summary exists',observations=rows))
                print(case,number,arm,flush=True)
        with (target/'raw.csv').open('w',newline='') as stream:
            w=csv.DictWriter(stream,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
        arrays=[[r['seconds'] for r in rows if r['arm']==arm] for arm in arms]
        write(target/'summary.json',dict(comparison=compare(*arrays,threshold=5,seed=84551),raw_sha256=digest(target/'raw.csv'),
            throughput='reciprocal of average ns/op is derived rate, not independent throughput benchmark',
            limitation='8 fork pairs only, virtual CPU quota and WSL scheduling; exploratory fixed-plan extension'))
    print(folder)
if __name__=='__main__':main()
