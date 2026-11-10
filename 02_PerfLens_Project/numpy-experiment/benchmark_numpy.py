"""One fresh Python process yields one NumPy argsort timing observation."""
import argparse
import json
import sys
from time import perf_counter


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--loops', type=int, default=100)
    p.add_argument('--warmups', type=int, default=5)
    p.add_argument('--size', type=int, default=100000)
    a = p.parse_args()
    if a.loops < 1 or a.warmups < 0 or a.size < 2:
        p.error('Require loops >= 1, warmups >= 0 and size >= 2')
    import numpy as np
    data = np.arange(a.size)
    # Check behavior before timing, and avoid timing input creation.
    if not np.array_equal(np.argsort(data), np.arange(a.size)):
        raise RuntimeError('Incorrect argsort output')
    for _ in range(a.warmups):
        data.argsort()
    start = perf_counter()
    for _ in range(a.loops):
        result = data.argsort()
    seconds = (perf_counter() - start) / a.loops
    if not np.array_equal(result, np.arange(a.size)):
        raise RuntimeError('Incorrect argsort output after timing')
    print(json.dumps({'seconds': seconds, 'numpy_version': np.__version__,
                      'python': sys.version.split()[0]}))

if __name__ == '__main__':
    main()
