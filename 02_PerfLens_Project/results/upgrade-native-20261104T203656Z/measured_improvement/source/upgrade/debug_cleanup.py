"""Retained diagnostic reproducer for asynchronous Windows descendant cleanup."""
from pathlib import Path
import subprocess
import sys
import tempfile
import time
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from perflens import observe
import psutil
for trial in range(5):
    with tempfile.TemporaryDirectory(dir=ROOT/'.tmp') as temp:
        pidfile=Path(temp)/'pid'
        leaf=f'import os,time; open({str(pidfile)!r},"w").write(str(os.getpid())); time.sleep(60)'
        parent='import subprocess,sys; subprocess.Popen([sys.executable,"-c",'+repr(leaf)+']); print("parent exits",flush=True)'
        try:
            observe(dict(command=['{python}','-c',parent]),{},1)
        except subprocess.TimeoutExpired:
            pid=int(pidfile.read_text())
            timeline=[]
            start=time.monotonic()
            for delay in [0,.01,.05,.1]:
                time.sleep(delay)
                timeline.append(dict(milliseconds=round(1000*(time.monotonic()-start),2),exists=psutil.pid_exists(pid)))
            print(dict(trial=trial,pid=pid,timeline=timeline),flush=True)
