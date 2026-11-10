"""The actual benchmark: one fresh process produces one timing observation."""
import argparse
import json
from pathlib import Path
import sys
from time import perf_counter

ROOT = Path(__file__).resolve().parent


def measure(loops, warmups, size):
    # Import the checked-out source, never a separately installed NetworkX.
    repo = ROOT / 'networkx_repo'
    sys.path.insert(0, str(repo))
    import networkx as nx
    if not Path(nx.__file__).resolve().is_relative_to(repo):
        raise RuntimeError('The wrong NetworkX installation was imported.')
    graph = nx.grid_2d_graph(size, size)
    for _ in range(warmups):
        nx.single_source_shortest_path_length(graph, (0, 0))

    start = perf_counter()  # The measured region starts here.
    for _ in range(loops):
        distances = nx.single_source_shortest_path_length(graph, (0, 0))
    elapsed = perf_counter() - start  # The measured region ends here.

    # Correctness checks, imports, setup and output are outside the timer.
    if len(distances) != size * size or distances[(size - 1, size - 1)] != 2 * (size - 1):
        raise RuntimeError('The shortest-path result is incorrect.')
    return {'seconds': elapsed / loops, 'networkx_version': nx.__version__}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--loops', type=int, default=100)
    parser.add_argument('--warmups', type=int, default=3)
    parser.add_argument('--size', type=int, default=35)
    args = parser.parse_args()
    if args.loops < 1 or args.warmups < 0 or args.size < 2:
        parser.error('Require loops >= 1, warmups >= 0 and size >= 2.')
    print(json.dumps(measure(args.loops, args.warmups, args.size)))
