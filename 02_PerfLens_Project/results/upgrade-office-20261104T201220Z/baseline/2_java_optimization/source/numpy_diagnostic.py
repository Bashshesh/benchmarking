"""Record historical NumPy environment details and run a fixed-int64 comparison."""
import argparse
from datetime import datetime,timezone
import json
from pathlib import Path
import subprocess

from perflens import ROOT,run,write_json


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--old-python',required=True,type=Path)
    parser.add_argument('--new-python',required=True,type=Path)
    args=parser.parse_args()
    output=ROOT/'results'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ_numpy-diagnostic')
    output.mkdir()
    interpreters=[str(args.old_python.resolve()),str(args.new_python.resolve())]
    info=[]
    code=('import numpy as np,sys,json; '
          'print(json.dumps(dict(version=np.__version__,python=sys.version,default_dtype=str(np.arange(10).dtype),'
          'cpu_features=np.core._multiarray_umath.__cpu_features__))); np.show_config()')
    for index,executable in enumerate(interpreters):
        result=subprocess.run([executable,'-c',code],capture_output=True,text=True,check=True)
        (output/f'environment-{index}.txt').write_text(result.stdout+'\nSTDERR:\n'+result.stderr,encoding='utf-8')
        info.append(json.loads(result.stdout.splitlines()[0]))
    if [record['version'] for record in info]!=['1.26.4','2.0.0']:
        raise ValueError('Expected the two pinned NumPy releases')
    write_json(output/'environments.json',info)
    config=dict(name='numpy_fixed_int64',rounds=20,threshold=5,seed=2901,timeout=120,
                arms=[dict(name=name,command=[exe,'{root}/workloads/numpy_argsort.py','--dtype','int64'])
                      for name,exe in zip(['numpy_1_26_4','numpy_2_0_0'],interpreters)])
    write_json(output/'config.json',config)
    run(output/'config.json',output/'comparison')
    print(output)


if __name__=='__main__':
    main()
