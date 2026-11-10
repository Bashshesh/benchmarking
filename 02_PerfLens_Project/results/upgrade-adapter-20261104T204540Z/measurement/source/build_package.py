"""Export review sources, archived inputs and evidence, excluding local runtimes."""
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import zipfile

ROOT=Path(__file__).resolve().parent
EXCLUDE={'.git','.venv','.numpy126','.numpy200','.tmp','__pycache__','networkx_repo','original','build'}


def main():
    files=sorted(p for p in ROOT.rglob('*') if p.is_file() and
                 not any(part in EXCLUDE for part in p.relative_to(ROOT).parts) and
                 p.name!='package-manifest.json' and p.suffix!='.pyc')
    manifest=dict(created_utc=datetime.now(timezone.utc).isoformat(),
        excludes=sorted(EXCLUDE),note='Originals and NetworkX are restorable offline from archive/misc.zip. Environments/JDK must be installed separately. Inventory is an integrity check, not a digital signature.',
        sha256={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files})
    inventory=ROOT/'package-manifest.json'
    inventory.write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    destination=ROOT.parent/'PerfLens-review-package.zip'
    with zipfile.ZipFile(destination,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
        for path in files+[inventory]:
            archive.write(path,Path('PerfLens')/path.relative_to(ROOT),
                          compress_type=zipfile.ZIP_STORED if path.suffix in ['.zip','.bundle'] else zipfile.ZIP_DEFLATED)
    print(destination)
    print('Files:',len(files)+1,'Bytes:',destination.stat().st_size)


if __name__=='__main__':
    main()
