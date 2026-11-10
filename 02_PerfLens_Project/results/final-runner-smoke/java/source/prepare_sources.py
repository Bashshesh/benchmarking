"""Restore original source and NetworkX offline from the unchanged supplied ZIP."""
from pathlib import Path
import zipfile

ROOT=Path(__file__).resolve().parent


def main():
    with zipfile.ZipFile(ROOT/'archive/misc.zip') as archive:
        for item in archive.infolist():
            if item.is_dir():
                continue
            original=(ROOT/'original'/item.filename).resolve()
            if not original.is_relative_to((ROOT/'original').resolve()):
                raise ValueError('Unsafe archive member')
            if not original.exists():
                original.parent.mkdir(parents=True,exist_ok=True)
                original.write_bytes(archive.read(item))
            if item.filename.startswith('misc/networkx_repo/'):
                destination=(ROOT/item.filename.removeprefix('misc/')).resolve()
                if not destination.is_relative_to(ROOT):
                    raise ValueError('Unsafe source member')
                if not destination.exists():
                    destination.parent.mkdir(parents=True,exist_ok=True)
                    destination.write_bytes(archive.read(item))
    print('Originals and NetworkX restored without overwriting existing files.')


if __name__=='__main__':
    main()
