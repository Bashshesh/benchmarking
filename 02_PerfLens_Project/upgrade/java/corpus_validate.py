"""Supplemental independent input correctness, both actual library revisions."""
from datetime import datetime,timezone
from pathlib import Path
import json,shutil,sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from upgrade.java.reproduce import load,CACHE,SHAS,write,digest
from upgrade.java.extend import run

def main():
 s=load();corpus=sorted(p for p in (ROOT/'results').glob('resume-corpus-*') if (p/'dataset.json').exists())[-1]
 folder=ROOT/'results'/('resume-corpus-correctness-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'));folder.mkdir()
 helper=ROOT/'upgrade/java/CorpusCorrectnessMain.java';shutil.copy2(helper,folder/helper.name)
 write(folder/'input.json',dict(corpus_folder=str(corpus.relative_to(ROOT)),sha256=digest(corpus/'corpus.bin'),oracle_sha256=digest(helper),
   timing='Supplemental independent both-boundary validation after retained timings, before final interpretation. Existing JMH setup already validated full blocks.'))
 answers=[]
 for sha in SHAS:
  out=CACHE/'built'/sha;cp=(out/'classpath.txt').read_text().strip()
  assert digest(out/'corpus.bin')==digest(corpus/'corpus.bin')
  shutil.copy2(helper,out/helper.name)
  run(s,sha,out,['javac','-proc:none','-cp',cp,'-d','/out/harness','/out/'+helper.name],folder/('compile-'+sha+'.json'))
  result=run(s,sha,out,['java','-cp',cp,'perflens.external.CorpusCorrectnessMain'],folder/('oracle-'+sha+'.json'))
  answer=json.loads(result);assert answer['valid'] is True;answers.append(answer)
 assert answers[0]==answers[1]
 write(folder/'status.json',dict(status='independent full/near corpus oracle passes on both revisions',answers=answers))
 print(folder)
if __name__=='__main__':main()
