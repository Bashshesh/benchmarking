"""Check files in the portable package against its SHA-256 inventory."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent


def main():
    manifest=json.loads((ROOT/'package-manifest.json').read_text())
    for name,expected in manifest['sha256'].items():
        path=(ROOT/name).resolve()
        if not path.is_relative_to(ROOT):
            raise ValueError('Unsafe inventory path')
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=expected:
            raise ValueError('Missing or changed package file: '+name)
    print(f"Verified {len(manifest['sha256'])} packaged files against SHA-256 inventory.")


if __name__=='__main__':
    main()
