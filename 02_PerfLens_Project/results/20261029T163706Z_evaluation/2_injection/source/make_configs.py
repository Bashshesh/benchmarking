"""Write explicit reusable configurations; inspect before running experiments."""
import argparse
import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--cpu', type=int, default=2)
    p.add_argument('--other-cpu', type=int, default=4)
    args = p.parse_args()
    def graph(variant='baseline', size=35):
        return ['{python}', '{root}/workloads/graph_queries.py', '--variant', variant,
                '--size', str(size), '--loops', '5', '--warmups', '3']
    def java(variant='baseline', warmups=5, interpreted=False):
        return ['{java}'] + (['-Xint'] if interpreted else []) + ['-cp', '{root}/build',
            'SearchBench', variant, '20000', '2000', '5', str(warmups)]
    experiments = {
        'control': [dict(name='reference', command=graph()), dict(name='unchanged', command=graph())],
        'injection': [dict(name='reference', command=graph()), dict(name='redundant_BFS', command=graph('regression'))],
        'python_optimization': [dict(name='repeated_BFS', command=graph()), dict(name='reuse_BFS', command=graph('optimized'))],
        'python_scaling': [dict(name='repeated_BFS', command=graph(size=60)), dict(name='reuse_BFS', command=graph('optimized',60))],
        'cpu_contention': [dict(name='quiet', command=graph(), cpu=args.cpu),
            dict(name='same_cpu_load', command=graph(), cpu=args.cpu, load=True)],
        'cpu_mitigation': [dict(name='same_cpu_load', command=graph(), cpu=args.cpu, load=True),
            dict(name='separate_cpu_load', command=graph(), cpu=args.other_cpu, load=True, load_cpu=args.cpu)],
        'java_optimization': [dict(name='linear_search', command=java()), dict(name='binary_search', command=java('optimized'))],
        'java_warmup': [dict(name='no_warmup', command=java('optimized',0)), dict(name='20_warmups', command=java('optimized',20))],
        'java_runtime': [dict(name='interpreter', command=java('optimized',20,True)), dict(name='default_JVM', command=java('optimized',20))],
    }
    for session in [1,2]:
        for name, arms in experiments.items():
            if name == 'python_scaling' and session == 2:
                continue
            config = dict(name=name, session=session, seed=1729+session, rounds=20,
                          threshold=5, timeout=120, arms=copy.deepcopy(arms))
            if name in ['control','python_optimization','python_scaling']:
                config['target_seconds'] = .003
            path = ROOT / 'configs' / f'{session}_{name}.json'
            path.write_text(json.dumps(config, indent=2) + '\n', encoding='utf-8')
    print('Wrote 17 fixed-budget configurations (20 paired fresh processes each).')


if __name__ == '__main__':
    main()
