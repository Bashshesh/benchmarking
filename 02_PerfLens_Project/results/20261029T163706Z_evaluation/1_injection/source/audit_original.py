"""Verify archive bytes, extracted originals and saved original statistics."""
import csv
import hashlib
import json
from pathlib import Path
import zipfile

from analyze import compare, descriptive
from perflens import ROOT, write_json


def main():
    hashes = json.loads((ROOT/'archive/SHA256.json').read_text())
    for name, expected in hashes.items():
        if hashlib.sha256((ROOT/'archive'/name).read_bytes()).hexdigest() != expected:
            raise ValueError('Archive changed: '+name)
    count = 0
    with zipfile.ZipFile(ROOT/'archive/misc.zip') as archive:
        for item in archive.infolist():
            if item.is_dir():
                continue
            path = ROOT/'original'/item.filename
            if path.exists() and path.read_bytes() != archive.read(item):
                raise ValueError('Extracted original changed: '+item.filename)
            count += 1
    records=[]
    roots=[ROOT/'original/misc/experiments', ROOT/'original/misc/numpy-experiment/experiments']
    for root in roots:
        for folder in sorted(root.iterdir()):
            metadata=json.loads((folder/'metadata.json').read_text())
            stored=json.loads((folder/'summary.json').read_text())
            groups={label:{} for label in metadata['commits']}
            with (folder/'raw.csv').open(newline='') as stream:
                for row in csv.DictReader(stream):
                    label, repeat=row['commit'],int(row['repeat'])
                    if label not in groups or repeat in groups[label]:
                        raise ValueError('Bad original rows')
                    groups[label][repeat]=float(row['seconds'])
            n=metadata['config']['repeats']
            if any(set(rows)!=set(range(1,n+1)) for rows in groups.values()):
                raise ValueError('Missing original observations')
            arrays=[[groups[label][i] for i in range(1,n+1)] for label in metadata['commits']]
            result=compare(*arrays,threshold=metadata['config']['threshold'],seed=metadata['config']['seed'])
            if result != stored['comparison']:
                raise ValueError('Original comparison does not reproduce: '+str(folder))
            if {label:descriptive(a) for label,a in zip(metadata['commits'],arrays)} != stored['summaries']:
                raise ValueError('Original descriptive statistics do not reproduce')
            records.append(dict(folder=str(folder.relative_to(ROOT)),pairs=n,comparison=result,
                                status='saved-data analysis exactly reproduced; not a fresh timing reproduction'))
    output=ROOT/'results/original-audit.json'
    write_json(output,dict(archive_hashes_verified=True,zip_file_entries=count,experiments=records))
    print(output)


if __name__=='__main__':
    main()
