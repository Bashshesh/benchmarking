"""Measured redundant computation; step additions are NOT guaranteed timing effects."""
import argparse
import json
from time import perf_counter, process_time

def sum_squares_mod97(n):
    result=0
    for i in range(n):
        result+=(i*i)%97
    return result

def oracle(n):
    # One complete residue period and an independently expressed finite remainder.
    cycles,remainder=divmod(n,97)
    return cycles*4656+sum(pow(i,2,97) for i in range(remainder))

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--extra',type=float,default=0)
    p.add_argument('--steps',type=int,default=50000)
    a=p.parse_args()
    if a.steps<100 or not 0<=a.extra<=2:
        p.error('Invalid computation budget')
    expected=oracle(a.steps)
    if sum_squares_mod97(a.steps)!=expected:
        raise AssertionError('Incorrect residue sum')
    start_cpu=process_time()
    start=perf_counter()
    result=sum_squares_mod97(a.steps)
    redundant=sum_squares_mod97(round(a.steps*a.extra))
    seconds=perf_counter()-start
    cpu=process_time()-start_cpu
    print(json.dumps(dict(seconds=seconds,checksum=result,valid=result==expected,
        process_cpu_seconds_per_operation=cpu,extra_fraction=a.extra,redundant_sink=redundant,
        label='real work intervention; effect magnitude uncalibrated')))

if __name__=='__main__':
    main()
