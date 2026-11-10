"""Repeat the unchanged fixed suite in an explicitly separate upgrade dataset."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from perflens import run, write_json, sha256
import psutil

def main():
    os.chdir(ROOT)
    os.environ.update(TEMP=str(ROOT/'.tmp'), TMP=str(ROOT/'.tmp'), PYTHONDONTWRITEBYTECODE='1')
    folder = ROOT/'results'/('upgrade-office-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
    folder.mkdir()
    java = os.environ.get('PERFLENS_JAVA', r'C:\Program Files\Java\jdk-21\bin\java.exe')
    host = dict(role='office Windows native', physical_host_continuity='same office context/hardware; do not treat new date as a new physical machine',
                host_key=hashlib.sha256((platform.node()+platform.processor()).encode()).hexdigest(),
                platform=platform.platform(), processor=platform.processor(), python=sys.version,
                affinity=psutil.Process().cpu_affinity(), cpu_counts=[psutil.cpu_count(),psutil.cpu_count(logical=False)],
                java=subprocess.run([java,'-version'],capture_output=True,text=True).stderr,
                revision=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip())
    write_json(folder/'host.json',host)
    for name,command in [('original-tests',[sys.executable,'-B','-m','unittest','-v','test_analysis.py']),
                         ('extension-tests',[sys.executable,'-B','-m','unittest','discover','-s','tests','-v'])]:
        result=subprocess.run(command,capture_output=True,text=True,env={**os.environ,'PERFLENS_JAVA':java})
        (folder/(name+'.txt')).write_text(result.stdout+result.stderr,encoding='utf-8')
        if result.returncode:
            raise RuntimeError('Baseline tests failed: '+name)
    suite=folder/'baseline'
    suite.mkdir()
    configs=sorted((ROOT/'configs').glob('*.json'))
    assert len(configs)==17
    manifest=dict(status='running',experiments=[],phase='unchanged baseline',machine_role=host['role'],
                  started_utc=datetime.now(timezone.utc).isoformat(),config_sha256={p.name:sha256(p) for p in configs},
                  design='Original 20 pairs, seeds 1730/1731, threshold 5%; no pooled cross-host data')
    write_json(suite/'suite.json',manifest)
    print('UPGRADE_FOLDER='+str(folder),flush=True)
    try:
        for config in configs:
            run(config,suite/config.stem,dict(java=java))
            manifest['experiments'].append(config.stem)
            write_json(suite/'suite.json',manifest)
        manifest['status']='complete'
    except BaseException as error:
        manifest.update(status='failed',error=repr(error))
        raise
    finally:
        manifest['finished_utc']=datetime.now(timezone.utc).isoformat()
        write_json(suite/'suite.json',manifest)
    print('Completed upgrade baseline:',folder,flush=True)

if __name__=='__main__':
    main()
