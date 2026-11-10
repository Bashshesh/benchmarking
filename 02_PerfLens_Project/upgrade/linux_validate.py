"""Project-owned Linux validation executed only in a restricted Docker container."""
import json,os,sys
from pathlib import Path
import shutil,subprocess,unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from perflens import observe,run,write_json
from upgrade.adapter import build

def main():
    os.chdir(ROOT)
    out=Path('/out')
    # No writable project mount: use a disposable copy of only reviewed project files.
    work=out/'project';shutil.copytree(ROOT,work,ignore=shutil.ignore_patterns('.git','.agents','.tmp','.venv','results','original','archive','transfer'))
    os.chdir(work);sys.path.insert(0,str(work))
    env=os.environ.copy();env['PERFLENS_JAVA']=shutil.which('java')
    test_codes=[]
    for name,args in [('original-tests',['-m','unittest','-v','test_analysis.py']),('extension-tests',['-m','unittest','discover','-s','tests','-v'])]:
        r=subprocess.run([sys.executable,'-B',*args],env=env,capture_output=True,text=True)
        write_json(out/(name+'.json'),dict(command=args,returncode=r.returncode,stdout=r.stdout,stderr=r.stderr))
        test_codes.append(r.returncode)
    for variant in ['python','java']:
        if variant=='java':
            classes=out/'classes';classes.mkdir()
            build([[shutil.which('javac'),'-d',str(classes),str(work/'workloads/SearchBench.java')]],out/'build',{},60)
            command=[shutil.which('java'),'-cp',str(classes),'SearchBench','optimized','3','7','1','0']
        else:command=['{python}','-c','import json; print(json.dumps(dict(seconds=.01,checksum=4,valid=True)))']
        config=dict(name='linux-'+variant,rounds=5,seed=845,arms=[dict(name='A',command=command),dict(name='B',command=command)])
        path=out/(variant+'-config.json');write_json(path,config)
        run(path,out/(variant+'-integration'))
    subprocess.run(['uname','-a'],check=True)
    write_json(out/'validation-status.json',dict(test_returncodes=test_codes,status='passed' if not any(test_codes) else 'failed',
        integration='functional smoke only; Python constant payload is a protocol fixture, tiny Java timing is not an accuracy or performance claim'))
    if any(test_codes):raise SystemExit(1)
if __name__=='__main__':main()
