"""Observable descendant lifetime contract, including a successful parent exit."""
import os
from pathlib import Path
import tempfile
import unittest
import psutil
from perflens import observe

class JobLifetimeTests(unittest.TestCase):
    def test_successful_parent_cannot_leave_detached_descendant_running(self):
        with tempfile.TemporaryDirectory() as temp:
            pidfile=Path(temp)/'pid'
            leaf=f'import os,time; open({str(pidfile)!r},"w").write(str(os.getpid())); time.sleep(60)'
            code=('import subprocess,sys,pathlib,time; '
                  f'subprocess.Popen([sys.executable,"-c",{leaf!r}],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); '
                  f'p=pathlib.Path({str(pidfile)!r}); '
                  'exec("while not p.exists(): time.sleep(.005)"); '
                  'print(\'{"seconds":.01,"checksum":42,"valid":true}\')')
            # Correct valid JSON is emitted by the real process, not a mock timer assertion.
            code=code.replace('"seconds":.01','"seconds":0.01')
            observe(dict(command=['{python}','-c',code]),{},10)
            pid=int(pidfile.read_text())
            try:
                try:
                    psutil.Process(pid).wait(timeout=5)
                except psutil.NoSuchProcess:
                    pass
            finally:
                try:
                    psutil.Process(pid).kill()
                except psutil.NoSuchProcess:
                    pass
