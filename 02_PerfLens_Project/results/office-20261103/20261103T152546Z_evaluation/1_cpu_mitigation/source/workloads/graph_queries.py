"""Repeated same-source distance queries on the original NetworkX grid workload."""
import argparse
import json
import sys
from pathlib import Path
from time import perf_counter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'networkx_repo'))
import networkx as nx
if not Path(nx.__file__).resolve().is_relative_to((ROOT / 'networkx_repo').resolve()):
    raise RuntimeError('Wrong NetworkX source imported; restore the supplied checkout')


def query(graph, targets, variant):
    if variant == 'optimized':
        distances = nx.single_source_shortest_path_length(graph, (0, 0))
        return [distances[target] for target in targets]
    values = []
    for target in targets:
        distances = nx.single_source_shortest_path_length(graph, (0, 0))
        if variant == 'regression':
            # Deliberately redundant real computation, not a synthetic delay.
            distances = nx.single_source_shortest_path_length(graph, (0, 0))
        values.append(distances[target])
    return values


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--variant', choices=['baseline', 'optimized', 'regression'], default='baseline')
    p.add_argument('--size', type=int, default=35)
    p.add_argument('--queries', type=int, default=16)
    p.add_argument('--loops', type=int, default=10)
    p.add_argument('--warmups', type=int, default=3)
    a = p.parse_args()
    if a.size < 2 or min(a.queries, a.loops) < 1 or a.warmups < 0:
        p.error('Invalid workload dimensions')
    graph = nx.grid_2d_graph(a.size, a.size)
    targets = [(i % a.size, (i * 7 + 3) % a.size) for i in range(a.queries)]
    expected = [x + y for x, y in targets]  # Independent Manhattan-distance oracle.
    for _ in range(a.warmups):
        query(graph, targets, a.variant)
    start = perf_counter()
    for _ in range(a.loops):
        values = query(graph, targets, a.variant)
    seconds = (perf_counter() - start) / a.loops
    if values != expected:
        raise RuntimeError('Incorrect distances')
    print(json.dumps(dict(seconds=seconds, checksum=values, valid=True,
                         networkx_version=nx.__version__, size=a.size,
                         networkx_source=str(Path(nx.__file__).resolve()),
                         queries=a.queries, loops=a.loops, warmups=a.warmups)))


if __name__ == '__main__':
    main()
