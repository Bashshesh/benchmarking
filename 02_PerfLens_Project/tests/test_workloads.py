import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('graph_queries', Path(__file__).resolve().parents[1] / 'workloads/graph_queries.py')
graph_queries = importlib.util.module_from_spec(spec)
spec.loader.exec_module(graph_queries)


class WorkloadTests(unittest.TestCase):
    def test_every_grid_distance_matches_independent_oracle(self):
        for size in [2, 5, 17]:
            graph = graph_queries.nx.grid_2d_graph(size, size)
            targets = list(graph.nodes)
            expected = [x+y for x, y in targets]
            for variant in ['baseline', 'optimized', 'regression']:
                self.assertEqual(graph_queries.query(graph, targets, variant), expected)


if __name__ == '__main__':
    unittest.main()
