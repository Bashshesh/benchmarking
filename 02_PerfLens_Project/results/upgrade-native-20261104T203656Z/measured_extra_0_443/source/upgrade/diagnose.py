"""Separate JFR/JIT/GC and latency diagnostics for trusted project workloads."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
from xml.etree import ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from perflens import write_json,sha256
from upgrade.metrics import permitted_jvm
from upgrade.topology import cpu_sets,diagnostic_probe

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--java',default=os.environ.get('PERFLENS_JAVA',r'C:\Program Files\Java\jdk-21\bin\java.exe'))
    p.add_argument('--output',type=Path)
    a=p.parse_args()
    out=a.output or ROOT/'results'/('upgrade-diagnostics-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
    out.mkdir()
    jdk=Path(a.java).parent.parent
    write_json(out/'environment.json',dict(evidence_class='instrumented diagnostics, not clean performance observations',
        topology=cpu_sets(),system_probe=diagnostic_probe(),java=a.java,
        source_sha256=sha256(ROOT/'upgrade/workloads/MetricsBench.java')))
    for label,variant,loops,setting in [('linear','baseline',1000,'default'),('binary','optimized',20000,'default'),('binary-tier1','optimized',20000,'tier1')]:
        case=out/label;case.mkdir()
        tree=ET.parse(jdk/'lib/jfr/profile.jfc')
        root=tree.getroot()
        for name in ['jdk.InitialEnvironmentVariable','jdk.InitialSystemProperty','jdk.SystemProcess']:
            event=next((e for e in root.findall('event') if e.get('name')==name),None)
            if event is None:event=ET.SubElement(root,'event',name=name)
            enabled=next((s for s in event.findall('setting') if s.get('name')=='enabled'),None)
            if enabled is None:enabled=ET.SubElement(event,'setting',name='enabled')
            enabled.attrib.pop('control',None);enabled.text='false'
        event=next((e for e in root.findall('event') if e.get('name')=='jdk.Compilation'),None)
        if event is not None:
            for s in event.findall('setting'):
                if s.get('name')=='threshold':s.attrib.pop('control',None);s.text='0 ms'
        tree.write(case/'privacy-profile.jfc',encoding='utf-8',xml_declaration=True)
        command=[a.java,*permitted_jvm(setting),'-XX:+PrintCompilation',
                 '-XX:StartFlightRecording=filename=recording.jfr,settings=privacy-profile.jfc,dumponexit=true',
                 '-Xlog:gc*,safepoint:file=gc.log','-cp',str(ROOT/'build/upgrade'),'MetricsBench',variant,str(loops),'200']
        result=subprocess.run(command,cwd=case,capture_output=True,text=True,timeout=120)
        write_json(case/'invocation.json',dict(command=command,returncode=result.returncode,stdout=result.stdout,stderr=result.stderr))
        if result.returncode:raise RuntimeError('Diagnostic JVM failed; retained logs in '+str(case))
        payloads=[json.loads(line) for line in result.stdout.splitlines() if line.startswith('{"seconds":')]
        if len(payloads)!=1 or payloads[0]['valid'] is not True:raise ValueError('Diagnostic correctness failure')
        write_json(case/'payload.json',payloads[0])
        jfr=str(jdk/'bin'/('jfr.exe' if os.name=='nt' else 'jfr'))
        summary=subprocess.run([jfr,'summary','recording.jfr'],cwd=case,capture_output=True,text=True,check=True)
        (case/'jfr-summary.txt').write_text(summary.stdout+summary.stderr,encoding='utf-8')
        command=[jfr,'print','--json','--events','jdk.Compilation,jdk.GarbageCollection,jdk.ExecutionSample,jdk.CPULoad,jdk.ThreadCPULoad,jdk.ObjectAllocationSample','recording.jfr']
        printed=subprocess.run(command,cwd=case,capture_output=True,text=True,check=True)
        (case/'jfr-events.json').write_text(printed.stdout,encoding='utf-8')
        events=json.loads(printed.stdout)['recording']['events']
        counts=Counter(e['type'] for e in events)
        levels=Counter(str(e['values'].get('compileLevel')) for e in events if e['type']=='jdk.Compilation')
        write_json(case/'event-counts.json',dict(event_counts=counts,compilation_levels=levels,
            recording_sha256=sha256(case/'recording.jfr'),limit='counts depend on instrumented duration, settings and operation budget; do not compare raw counts as speedups'))
        print('diagnostic',label,dict(counts),flush=True)
    command=[a.java,'-cp',str(ROOT/'build/upgrade'),'MetricsBench','optimized','2000','100','latency']
    result=subprocess.run(command,capture_output=True,text=True,timeout=60)
    write_json(out/'latency-invocation.json',dict(command=command,returncode=result.returncode,stderr=result.stderr))
    if result.returncode:raise RuntimeError('Latency diagnostic failed')
    payload=json.loads(result.stdout)
    write_json(out/'latency-raw.json',payload)
    values=sorted(payload['latency_nanoseconds']);n=len(values)
    import math
    assert payload['latencies']['p99_seconds']==values[math.ceil(.99*n)-1]/1e9
    assert payload['valid'] is True
    print('DIAGNOSTIC_FOLDER='+str(out),flush=True)

if __name__=='__main__':main()
