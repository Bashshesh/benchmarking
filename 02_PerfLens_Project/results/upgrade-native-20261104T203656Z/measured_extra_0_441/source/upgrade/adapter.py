"""Declarative build receipts plus the existing language-independent paired runner.

This adapter is NOT a security sandbox. Only reviewed project-owned commands may
run natively; downloaded repositories use the restricted Docker setup instead.
"""
import argparse
from datetime import datetime,timezone
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from perflens import expand_command,run,write_json,sha256

def build(commands,folder,runtime,timeout=60):
    folder.mkdir()
    receipts=[]
    for index,template in enumerate(commands):
        if not isinstance(template,list) or not template or not all(isinstance(x,str) for x in template):
            raise ValueError('Build commands must be argument arrays')
        command=expand_command(template,runtime)
        actual=command.copy();job=None;child=None;started=time.perf_counter()
        receipt=dict(command=command,status='running')
        try:
            if os.name=='nt':
                from process_control import WindowsJob
                job=WindowsJob();actual=[sys.executable,str(ROOT/'benchmark_launcher.py'),*actual]
            child=subprocess.Popen(actual,cwd=ROOT,text=True,stdin=subprocess.PIPE if job else subprocess.DEVNULL,
                stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=os.name!='nt')
            if job:job.assign(child.pid)
            out,err=child.communicate(input='run\n' if job else None,timeout=timeout)
            receipt.update(returncode=child.returncode,stdout=out,stderr=err,status='complete' if child.returncode==0 else 'failed')
        except BaseException as error:
            receipt.update(status='failed',error=repr(error))
            if child:
                if job:job.terminate()
                else:
                    try:os.killpg(child.pid,signal.SIGKILL)
                    except ProcessLookupError:pass
                try:
                    out,err=child.communicate(timeout=5);receipt.update(stdout=out,stderr=err,returncode=child.returncode)
                except subprocess.TimeoutExpired:receipt['cleanup_error']='could not drain pipes within five seconds'
        finally:
            if job:job.close()
            elif child:
                try:os.killpg(child.pid,signal.SIGKILL)
                except ProcessLookupError:pass
            receipt['elapsed_seconds']=time.perf_counter()-started
            write_json(folder/(str(index)+'.json'),receipt);receipts.append(receipt)
        if receipt['status']!='complete':raise RuntimeError('Build failed; receipt retained')
    return receipts

def main():
    p=argparse.ArgumentParser();p.add_argument('spec',type=Path);p.add_argument('--output',required=True,type=Path);p.add_argument('--java',required=True)
    a=p.parse_args();spec=json.loads(a.spec.read_text(encoding='utf-8-sig'))
    if spec.get('trust')!='reviewed-project-owned':raise ValueError('Native adapter only accepts explicitly reviewed project-owned recipes; this is not a sandbox')
    a.output.mkdir()
    runtime=dict(java=a.java,javac=str(Path(a.java).with_name('javac.exe' if os.name=='nt' else 'javac')))
    write_json(a.output/'spec.json',spec)
    inputs={}
    for name in spec.get('inputs',[]):
        source=(ROOT/name).resolve()
        if not source.is_relative_to(ROOT) or not source.is_file():raise ValueError('Unsafe/missing source input')
        inputs[name]=sha256(source)
        dest=a.output/'source'/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(source.read_bytes())
    write_json(a.output/'input-sha256.json',inputs)
    build(spec.get('build_commands',[]),a.output/'build',runtime,spec.get('build_timeout',60))
    config=a.output/'measurement.json';write_json(config,spec['measurement'])
    run(config,a.output/'measurement',runtime)

if __name__=='__main__':main()
