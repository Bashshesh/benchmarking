"""Verify immutable checkpoint files and archive exact pre-upgrade edited source."""
import argparse
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import zipfile
ROOT=Path(__file__).resolve().parents[1]
ALLOWED={'process_control.py','tests/test_runner.py','perflens.py'}
def digest(data):return hashlib.sha256(data).hexdigest()
def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path);a=p.parse_args()
    folder=a.output or ROOT/'results'/('upgrade-preservation-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
    folder.mkdir()
    manifest=json.loads((ROOT/'package-manifest.json').read_text())['sha256']
    changed={};verified=0
    for name,expected in manifest.items():
        actual=digest((ROOT/name).read_bytes())
        if actual!=expected:
            if name not in ALLOWED:raise ValueError('Unexpected change to preserved input: '+name)
            changed[name]=dict(original_sha256=expected,upgraded_sha256=actual)
        else:verified+=1
    transfer=Path.home()/'Downloads/PerfLens-complete-transfer-20261103T160906Z.zip'
    with zipfile.ZipFile(transfer) as source,zipfile.ZipFile(folder/'pre-upgrade-edited-sources.zip','x',compression=zipfile.ZIP_DEFLATED) as out:
        for name in sorted(changed):
            data=source.read('PerfLens/'+name)
            if digest(data)!=manifest[name]:raise ValueError('Prior transfer does not match original source inventory')
            out.writestr(name,data)
        out.writestr('original-package-manifest.json',(ROOT/'package-manifest.json').read_bytes())
    import sys
    sys.path.insert(0,str(ROOT))
    from audit_original import verify_originals
    entries=verify_originals(ROOT)
    result=dict(immutable_original_files_verified=verified,intentional_versioned_changes=changed,
                archived_original_entries_verified=entries,original_manifest='preserved; describes the pre-upgrade checkpoint',
                originals_snapshot_sha256=digest((folder/'pre-upgrade-edited-sources.zip').read_bytes()),
                previous_history='preserved starting Git commit 111accf plus original history.bundle and archive/misc.zip')
    (folder/'verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result,indent=2))
if __name__=='__main__':main()
