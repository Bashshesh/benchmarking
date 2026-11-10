"""Run the fixed experiment set sequentially, never concurrently on this host."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil

from perflens import ROOT, run, write_json


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--java', required=True)
    p.add_argument('--session', choices=['1','2','all'], default='all')
    p.add_argument('--label', default='evaluation')
    args = p.parse_args()
    java = str(Path(args.java).resolve())
    folder = ROOT / 'results' / (datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ_') + args.label)
    folder.mkdir()
    manifest = dict(status='running', started_utc=datetime.now(timezone.utc).isoformat(), experiments=[])
    try:
        for config in sorted((ROOT / 'configs').glob('*.json')):
            if args.session != 'all' and not config.name.startswith(args.session+'_'):
                continue
            target = folder / config.stem
            run(config, target, dict(java=java))
            manifest['experiments'].append(target.name)
            write_json(folder / 'suite.json', manifest)
        manifest['status'] = 'complete'
    except BaseException as error:
        manifest.update(status='failed', error=repr(error))
        raise
    finally:
        manifest['finished_utc'] = datetime.now(timezone.utc).isoformat()
        write_json(folder / 'suite.json', manifest)
    print('Suite:', folder)


if __name__ == '__main__':
    main()
