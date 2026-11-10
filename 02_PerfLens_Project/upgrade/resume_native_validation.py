"""Execute the current original and extension suites on the native host."""
import argparse,json,os,shutil,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def main():
 p=argparse.ArgumentParser();p.add_argument('output',type=Path);p.add_argument('--java',required=True);a=p.parse_args()
 temp=ROOT/'.tmp';temp.mkdir(exist_ok=True)
 env=os.environ.copy();env.update(TEMP=str(temp),TMP=str(temp),PERFLENS_JAVA=a.java)
 receipts=[]
 for args in [['-m','unittest','-v','test_analysis.py'],['-m','unittest','discover','-s','tests','-v']]:
  cmd=[sys.executable,'-B',*args];r=subprocess.run(cmd,cwd=ROOT,capture_output=True,encoding='utf-8',errors='replace',env=env)
  receipts.append(dict(command=cmd,java=a.java,returncode=r.returncode,stdout=r.stdout,stderr=r.stderr))
 a.output.write_text(json.dumps(receipts,indent=2),encoding='utf-8')
 for r in receipts:print(r['stderr'][-125:])
 if any(r['returncode']!=0 for r in receipts):raise SystemExit(1)
if __name__=='__main__':main()
