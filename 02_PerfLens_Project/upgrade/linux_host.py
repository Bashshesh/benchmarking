"""Prepare a minimal reviewed-code mount and record restricted Linux tests."""
import argparse,json,shutil,sys,uuid
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from upgrade.java.reproduce import command,write,digest

def main():
 p=argparse.ArgumentParser();p.add_argument('--image',default='perflens-linux:resume');p.add_argument('--label',default='validation');a=p.parse_args()
 name='linux-'+uuid.uuid4().hex[:10]
 stage=ROOT/'.tmp'/name;stage.mkdir()
 # Never expose a whole project/home/credentials to the container.
 for pattern in ['*.py','requirements-lock.txt']:
  for f in ROOT.glob(pattern):shutil.copy2(f,stage/f.name)
 for directory in ['tests','upgrade','workloads','networkx_repo']:
  shutil.copytree(ROOT/directory,stage/directory,ignore=shutil.ignore_patterns('.git','__pycache__','*.pyc'))
 folder=ROOT/'results'/('resume-linux-'+a.label+'-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'));folder.mkdir()
 write(folder/'mount-sha256.json',{f.relative_to(stage).as_posix():digest(f) for f in stage.rglob('*') if f.is_file()})
 args=['docker','run','--rm','--init','--name',name,'--read-only','--network','none','--cap-drop','ALL','--security-opt','no-new-privileges',
  '--pids-limit','256','--memory','2g','--cpus','2','--user','10001:10001','--tmpfs','/tmp:rw,nosuid,nodev,size=256m',
  '--mount',f'type=bind,source={stage},target=/src,readonly','--mount',f'type=bind,source={folder},target=/out',a.image,
  'python','-B','/src/upgrade/linux_validate.py']
 command(args,folder/'container.json',240,name)
 print(folder)
if __name__=='__main__':main()
