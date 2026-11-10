"""Two additional pinned revision pilots, never repeats the completed PR845 pair."""
from datetime import datetime,timezone
from pathlib import Path
import json,sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from upgrade.java.reproduce import CACHE,SHAS,load,write,digest
from upgrade.java.extend import run
from upgrade.metrics import jmh_single_fork

def main():
 s=load();folder=ROOT/'results'/('resume-compatibility-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'));folder.mkdir()
 anchors=['e140aee9358b1e33be6e5b0cd8f043daef05299a','ef131a71e0aa6cd67b4ea649c957b1cd4c52b141']
 write(folder/'plan.json',dict(anchors=anchors,original_pair=SHAS,scope='Four nearby pinned source revisions; not independent release/JDK portability or a second real optimization case',image=s['image_id']))
 clone=CACHE/'git-test'
 for i,sha in enumerate(anchors):
  dirname='anchor-'+sha[:12]
  script='cd /out/repo && git cat-file -e '+sha+'^{commit} && git show -s --format="%H %P" '+sha+' && mkdir /out/'+dirname+' && git archive '+sha+' | tar -x -C /out/'+dirname
  run(s,SHAS[0],clone,['sh','-c',script],folder/('archive-'+sha+'.json'),240,True)
  source=clone/dirname;out=CACHE/('compat-'+sha[:12]);out.mkdir()
  s['sources'][sha]=dict(directory=str(source))
  write(folder/('source-'+sha+'.json'),{p.relative_to(source).as_posix():digest(p) for p in source.rglob('*') if p.is_file()})
  text=run(s,sha,out,['sh','/harness/build-roaring.sh'],folder/('build-'+sha+'.json'))
  assert '"checksum":458211' in text and '"valid":true' in text
  cp=(out/'classpath.txt').read_text().strip()
  run(s,sha,out,['java','-Xms512m','-Xmx512m','-cp',cp,'org.openjdk.jmh.Main','perflens.external.RankBenchmark.rank',
      '-p','limit=65535','-p','containers=16','-f','1','-t','1','-wi','1','-i','1','-w','100ms','-r','100ms','-rf','json','-rff','/out/pilot.json'],folder/('pilot-'+sha+'.json'))
  raw=json.loads((out/'pilot.json').read_text());jmh_single_fork(raw);write(folder/('jmh-'+sha+'.json'),raw)
 write(folder/'status.json',dict(status='two additional source/correctness/JMH pilots passed',total_pinned_revisions=4,anchors=anchors))
 print(folder)
if __name__=='__main__':main()
