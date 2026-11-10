"""Supplemental diagnostic: separate NumPy release and integer-dtype choices."""
import argparse
import json
from time import perf_counter

import numpy as np


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--dtype',choices=['default','int64'],default='int64')
    parser.add_argument('--size',type=int,default=100000)
    parser.add_argument('--loops',type=int,default=100)
    args=parser.parse_args()
    if args.size<2 or args.loops<1:
        parser.error('Invalid dimensions')
    values=np.arange(args.size,**({'dtype':np.int64} if args.dtype=='int64' else {}))
    expected=np.arange(args.size,dtype=np.int64)
    for _ in range(5):
        result=values.argsort()
    start=perf_counter()
    for _ in range(args.loops):
        result=values.argsort()
    seconds=(perf_counter()-start)/args.loops
    if not np.array_equal(result,expected):
        raise RuntimeError('Wrong sorting indices')
    print(json.dumps(dict(seconds=seconds,valid=True,
        checksum=[int(result[0]),int(result[-1]),int(result.sum())],
        numpy_version=np.__version__,dtype=str(values.dtype),result_dtype=str(result.dtype),
        size=args.size,loops=args.loops)))


if __name__=='__main__':
    main()
